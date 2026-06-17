"""Saathi — grounded patient chatbot.

Answers questions only from the patient's own CurrentTruth data.
Never diagnoses, never prescribes, never suggests changing a dose.
Red-flag keywords short-circuit to an emergency referral with no model call.
"""
from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.safety import BANNED_PHRASES, append_disclaimer

logger = logging.getLogger("setu.saathi")

# ---------------------------------------------------------------------------
# Hard boundaries — injected into every system prompt
# ---------------------------------------------------------------------------
_HARD_BOUNDARIES = (
    "You are Saathi, a health assistant for rural India. "
    "You ONLY answer based on the patient data provided below. "
    "NEVER diagnose any condition. "
    "NEVER prescribe or suggest any medication. "
    "NEVER tell the patient to change, stop, or start any dose. "
    "For any urgent symptom, always refer to emergency services immediately. "
    "For non-urgent advice, always say 'speak with your doctor'. "
    "Do NOT add any disclaimer — it is appended automatically by the system."
)

_EMERGENCY_REPLY: dict[str, str] = {
    "mr": (
        "हे गंभीर लक्षण आहे. लगेच जवळच्या रुग्णालयात जा किंवा 112 वर कॉल करा. "
        "वाट पाहू नका.\n\n"
        "हे तुमच्या कागदाचे स्पष्टीकरण आहे, वैद्यकीय सल्ला नाही. डॉक्टरांशी बोला."
    ),
    "hi": (
        "यह एक गंभीर लक्षण है। तुरंत नज़दीकी अस्पताल जाएं या 112 पर कॉल करें। "
        "देरी न करें।\n\n"
        "यह आपके दस्तावेज़ का स्पष्टीकरण है, चिकित्सीय सलाह नहीं। डॉक्टर से बात करें।"
    ),
    "en": (
        "This is an urgent symptom. Go to the nearest hospital immediately or call 112. "
        "Do not wait.\n\n"
        "This is an explanation of your document, not medical advice. Please speak with your doctor."
    ),
}

_RED_FLAG_KEYWORDS: tuple[str, ...] = (
    # English
    "chest pain", "can't breathe", "cannot breathe", "shortness of breath",
    "unconscious", "fainting", "fainted", "stroke", "heart attack",
    "seizure", "convulsion", "severe bleeding", "not breathing",
    # Hindi
    "छाती में दर्द", "सांस नहीं", "बेहोश", "दौरा", "हृदयघात", "हृदयविकाराचा झटका",
    # Marathi
    "छाती दुखणे", "श्वास घेता येत नाही", "बेशुद्ध",
)

SaathiAction = Literal["none", "urgent_care", "see_doctor", "monitor"]


class SaathiResponse(BaseModel):
    reply: str
    action: SaathiAction = "none"
    safe: bool = True


def _format_context(current_truth: CurrentTruthDTO) -> str:
    def _entries(t: str) -> list[CurrentTruthEntry]:
        return [e for e in current_truth.entries if e.entry_type == t]

    lines: list[str] = []
    meds = _entries("medication")
    if meds:
        lines.append("Medications:")
        for m in meds:
            v = m.value if not m.value.get("conflict") else m.value["values"][0]
            dose = f"{v.get('dose')}{v.get('dose_unit', '')}" if v.get("dose") is not None else ""
            lines.append(f"  - {v.get('name', m.normalized_key)} {dose} {v.get('frequency', '')}".rstrip())
    labs = _entries("lab_result")
    if labs:
        lines.append("Lab results:")
        for lab in labs:
            v = lab.value
            lines.append(
                f"  - {v.get('test_name', lab.normalized_key)}: "
                f"{v.get('value')}{v.get('unit', '')} [{v.get('flag', '')}]"
            )
    conds = _entries("diagnosis")
    if conds:
        lines.append("Conditions:")
        for c in conds:
            v = c.value if not c.value.get("conflict") else c.value["values"][0]
            lines.append(f"  - {v.get('condition', c.normalized_key)} ({v.get('status', 'active')})")
    return "\n".join(lines) if lines else "(no health data on file)"


def _strip_banned(text: str) -> str:
    for phrase in BANNED_PHRASES:
        if phrase.lower() in text.lower():
            text = text.replace(phrase, "[removed]")
    return text


async def chat(
    patient_id: str,
    message: str,
    history: list[dict],
    current_truth: CurrentTruthDTO,
    lang: str,
) -> SaathiResponse:
    msg_lower = message.lower()

    # Red-flag check — no model call needed.
    if any(kw in msg_lower for kw in _RED_FLAG_KEYWORDS):
        return SaathiResponse(
            reply=_EMERGENCY_REPLY.get(lang, _EMERGENCY_REPLY["en"]),
            action="urgent_care",
            safe=True,
        )

    context = _format_context(current_truth)
    lang_names = {"mr": "Marathi", "hi": "Hindi", "en": "English"}
    lang_name = lang_names.get(lang, "Marathi")

    system_prompt = f"{_HARD_BOUNDARIES}\n\nPatient data:\n{context}"

    contents = []
    for turn in history[-6:]:  # keep last 6 turns to stay within token budget
        role = turn.get("role", "user")
        contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": f"Answer in {lang_name}. {message}"}]})

    try:
        from google import genai
        from google.genai import types

        from app.config import settings
        from app.services.gemini_client import generate_content_with_fallback

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        response, _ = await generate_content_with_fallback(
            client,
            contents={"system_instruction": system_prompt, "contents": contents},
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_level="none"),
                max_output_tokens=300,
            ),
        )
        reply = _strip_banned((response.text or "").strip())
    except Exception as exc:  # noqa: BLE001
        logger.warning("saathi gemini failed: %s", exc)
        fallbacks = {
            "mr": "माफ करा, सध्या उत्तर देता येत नाही. डॉक्टरांशी बोला.",
            "hi": "माफ़ करें, अभी उत्तर नहीं दे सकते। डॉक्टर से बात करें।",
            "en": "Sorry, I can't answer right now. Please speak with your doctor.",
        }
        reply = fallbacks.get(lang, fallbacks["en"])

    # Determine action hint from reply keywords.
    action: SaathiAction = "none"
    if any(kw in reply.lower() for kw in ("emergency", "hospital", "112", "immediately", "तातडीने", "अस्पताल")):
        action = "urgent_care"
    elif any(kw in reply.lower() for kw in ("doctor", "डॉक्टर", "physician", "consult")):
        action = "see_doctor"

    return SaathiResponse(
        reply=append_disclaimer(reply, lang),
        action=action,
        safe=True,
    )
