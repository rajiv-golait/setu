"""Saathi — grounded patient chatbot.

Answers questions from the patient's CurrentTruth when possible.
Never diagnoses, never prescribes, never suggests changing a dose.
Red-flag keywords short-circuit to an emergency referral with no model call.
"""
from __future__ import annotations

import logging
import re
from typing import Literal

from pydantic import BaseModel

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.safety import BANNED_PHRASES, append_disclaimer

logger = logging.getLogger("setu.saathi")

# ---------------------------------------------------------------------------
# Hard boundaries — injected into every system prompt
# ---------------------------------------------------------------------------
_HARD_BOUNDARIES = (
    "You are Saathi — a warm, caring health companion for families in rural India, "
    "like a trusted friend who sits beside the patient and helps them understand their own records. "
    "Talk like a kind human, not a machine: short, gentle, everyday words a worried family member "
    "would use. Be reassuring and personal — greet warmly when it fits, acknowledge their feelings, "
    "and never sound like a clinical report or a generic AI assistant. "
    "Ground every answer ONLY in the patient data provided below; if something isn't in their records, "
    "gently say you don't see it there rather than guessing. "
    "If the patient asks who you are, introduce yourself warmly in one line as their health companion. "
    "NEVER diagnose any condition. "
    "NEVER prescribe or suggest any medication. "
    "NEVER tell the patient to change, stop, or start any dose. "
    "For any urgent symptom, always refer to emergency services immediately. "
    "For non-urgent advice, always warmly encourage them to speak with their doctor. "
    "Keep replies to two or three short sentences. "
    "Do NOT add any disclaimer — it is appended automatically by the system."
)

_EMERGENCY_REPLY: dict[str, str] = {
    "mr": (
        "हे गंभीर लक्षण आहे. लगेच जवळच्या रुग्णालयात जा किंवा 112 वर कॉल करा. "
        "वाट पाहू नका."
    ),
    "hi": (
        "यह एक गंभीर लक्षण है। तुरंत नज़दीकी अस्पताल जाएं या 112 पर कॉल करें। "
        "देरी न करें।"
    ),
    "en": (
        "This is an urgent symptom. Go to the nearest hospital immediately or call 112. "
        "Do not wait."
    ),
}

_IDENTITY_REPLY: dict[str, str] = {
    "mr": (
        "मी साथी — तुमचा आरोग्य सोबती. "
        "तुमच्या नोंदींमधील औषधे आणि रिपोर्ट सोप्या भाषेत समजावून सांगते. "
        "निदान किंवा दवा बदलण्याचा सल्ला देत नाही — ते डॉक्टरांकडे."
    ),
    "hi": (
        "मैं साथी हूँ — आपका सेहत साथी। "
        "आपके रिकॉर्ड की दवाइयाँ और रिपोर्ट आसान भाषा में समझाती हूँ। "
        "निदान या दवा बदलने की सलाह नहीं देती — वह डॉक्टर के पास।"
    ),
    "en": (
        "I'm Saathi — your health companion. "
        "I explain your medicines and reports from your records in simple words. "
        "I don't diagnose or tell you to change doses — that's for your doctor."
    ),
}

_EMPTY_DATA_REPLY: dict[str, str] = {
    "mr": (
        "अजून तुमच्या नोंदी रिकाम्या आहेत. एक प्रिस्क्रिप्शन किंवा रिपोर्ट अपलोड केल्यावर "
        "मी तुमच्या औषधांबद्दल विचारू शकता."
    ),
    "hi": (
        "अभी आपके रिकॉर्ड खाली हैं। कोई प्रिस्क्रिप्शन या रिपोर्ट अपलोड करने के बाद "
        "आप अपनी दवाइयों के बारे में पूछ सकते हैं।"
    ),
    "en": (
        "Your records are still empty. After you upload a prescription or report, "
        "you can ask me about your medicines here."
    ),
}

_GEMINI_ERROR_REPLY: dict[str, str] = {
    "mr": "माफ करा, सध्या माझ्या नोंदी वाचता येत नाहीत. थोड्या वेळाने पुन्हा प्रयत्न करा.",
    "hi": "माफ़ करें, अभी मेरे नोट्स नहीं पढ़ पा रही। थोड़ी देर बाद फिर कोशिश करें।",
    "en": "Sorry — I can't read my notes right now. Please try again in a moment.",
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

_IDENTITY_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.IGNORECASE)
    for p in (
        r"\bwho\s+are\s+(you|u)\b",
        r"\bwhat\s+are\s+(you|u)\b",
        r"\bwhat\s+is\s+saathi\b",
        r"तुम्ही\s+कोण",
        r"आप\s+कौन",
        r"साथी\s+कोण",
    )
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


def _is_identity_question(message: str) -> bool:
    return any(p.search(message) for p in _IDENTITY_PATTERNS)


def _gemini_role(role: str) -> str:
    return "model" if role == "assistant" else "user"


def _build_gemini_contents(history: list[dict], message: str, lang_name: str) -> list:
    from google.genai import types

    turns = history[-6:]
    if (
        turns
        and turns[-1].get("role") == "user"
        and turns[-1].get("content", "").strip() == message.strip()
    ):
        turns = turns[:-1]

    contents: list[types.Content] = []
    for turn in turns:
        text = str(turn.get("content", "")).strip()
        if not text:
            continue
        contents.append(
            types.Content(
                role=_gemini_role(str(turn.get("role", "user"))),
                parts=[types.Part.from_text(text=text)],
            )
        )
    contents.append(
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=f"Answer in {lang_name}. {message}")],
        )
    )
    return contents


def _infer_action(reply: str) -> SaathiAction:
    lower = reply.lower()
    if any(kw in lower for kw in ("emergency", "hospital", "112", "immediately", "तातडीने", "अस्पताल")):
        return "urgent_care"
    if any(kw in lower for kw in ("doctor", "डॉक्टर", "physician", "consult")):
        return "see_doctor"
    return "none"


async def chat(
    patient_id: str,
    message: str,
    history: list[dict],
    current_truth: CurrentTruthDTO,
    lang: str,
) -> SaathiResponse:
    from app.services.lang_detect import resolve_reply_lang

    reply_lang = resolve_reply_lang(message, lang, history)
    msg_lower = message.lower()

    if any(kw in msg_lower for kw in _RED_FLAG_KEYWORDS):
        return SaathiResponse(
            reply=append_disclaimer(_EMERGENCY_REPLY.get(reply_lang, _EMERGENCY_REPLY["en"]), reply_lang),
            action="urgent_care",
            safe=True,
        )

    if _is_identity_question(message):
        return SaathiResponse(
            reply=_IDENTITY_REPLY.get(reply_lang, _IDENTITY_REPLY["en"]),
            action="none",
            safe=True,
        )

    context = _format_context(current_truth)
    if context == "(no health data on file)":
        return SaathiResponse(
            reply=_EMPTY_DATA_REPLY.get(reply_lang, _EMPTY_DATA_REPLY["en"]),
            action="none",
            safe=True,
        )

    lang_names = {"mr": "Marathi", "hi": "Hindi", "en": "English"}
    lang_name = lang_names.get(reply_lang, "Marathi")
    system_prompt = f"{_HARD_BOUNDARIES}\n\nPatient data:\n{context}"

    try:
        from google import genai
        from google.genai import types

        from app.config import settings
        from app.services.gemini_client import generate_content_with_fallback

        if not settings.GOOGLE_API_KEY:
            raise RuntimeError("GOOGLE_API_KEY not set")

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        contents = _build_gemini_contents(history, message, lang_name)
        response, _ = await generate_content_with_fallback(
            client,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
                max_output_tokens=300,
            ),
        )
        reply = _strip_banned((response.text or "").strip())
        if not reply:
            raise RuntimeError("empty Gemini response")
    except Exception as exc:  # noqa: BLE001
        logger.warning("saathi gemini failed: %s", exc)
        return SaathiResponse(
            reply=_GEMINI_ERROR_REPLY.get(reply_lang, _GEMINI_ERROR_REPLY["en"]),
            action="none",
            safe=True,
        )

    return SaathiResponse(
        reply=append_disclaimer(reply, reply_lang),
        action=_infer_action(reply),
        safe=True,
    )
