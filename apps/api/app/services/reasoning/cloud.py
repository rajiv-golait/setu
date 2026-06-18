"""Cloud reasoner — Gemini Flash quality-first chain (google-genai >= 2.0.0).

Generates (1) the Marathi/Hindi/English caregiver explanation and (2) the
doctor-facing brief JSON. Free-text explanation does NOT use JSON output mode;
the brief does. Safety enforcement (disclaimer, banned phrases, abstain) is
applied by services/explanation.py around generate_explanation — but we also
append the disclaimer here so raw provider output is already safe.

generate_summary is required by the ABC but the patient summary is no longer in
the pipeline; it delegates to the deterministic mock.

Async via client.aio.models.generate_content (never block the event loop).
"""
from __future__ import annotations

import json
import logging

from app.config import settings
from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.gemini_client import generate_content_with_fallback
from app.services.gemini_models import GEMINI_DEFAULT_MODEL
from app.services.reasoning.base import ReasonerProvider

logger = logging.getLogger("setu.gemini")

GEMINI_MODEL = GEMINI_DEFAULT_MODEL

_LANG_NAME = {"mr": "Marathi", "hi": "Hindi", "en": "English"}


def _format_truth_for_prompt(current_truth: CurrentTruthDTO) -> str:
    """Compact, human-readable rendering of Current Truth for the model prompt.

    Only what is in the data — the model must not introduce anything else.
    """
    lines: list[str] = []

    def _entries(t: str) -> list[CurrentTruthEntry]:
        return [e for e in current_truth.entries if e.entry_type == t]

    meds = _entries("medication")
    if meds:
        lines.append("Medications:")
        for m in meds:
            v = m.value if not m.value.get("conflict") else m.value["values"][0]
            dose = f"{v.get('dose')}{v.get('dose_unit', '')}" if v.get("dose") is not None else ""
            note = " (possibly discontinued)" if m.state == "possibly_discontinued" else ""
            lines.append(f"  - {v.get('name', m.normalized_key)} {dose} {v.get('frequency', '')}".rstrip() + note)

    labs = _entries("lab_result")
    if labs:
        lines.append("Lab results:")
        for lab in labs:
            v = lab.value
            trend = v.get("trend")
            prev = v.get("previous")
            trend_str = ""
            if trend in ("up", "down") and prev is not None:
                trend_str = f" ({trend} from {prev})"
            lines.append(
                f"  - {v.get('test_name', lab.normalized_key)}: {v.get('value')}{v.get('unit', '')}"
                f" [{v.get('flag', '')}]{trend_str}"
            )

    conds = _entries("diagnosis")
    if conds:
        lines.append("Conditions:")
        for c in conds:
            v = c.value if not c.value.get("conflict") else c.value["values"][0]
            lines.append(f"  - {v.get('condition', c.normalized_key)} ({v.get('status', 'active')})")

    allergies = _entries("allergy")
    if allergies:
        lines.append("Allergies:")
        for a in allergies:
            lines.append(f"  - {a.value.get('substance', a.normalized_key)} ({a.value.get('severity', '')})")

    return "\n".join(lines) if lines else "(no structured data)"


class GeminiReasonerProvider(ReasonerProvider):
    name = "gemini-flash"

    def _client(self):  # noqa: ANN202 — lazy SDK import
        from google import genai

        return genai.Client(api_key=settings.GOOGLE_API_KEY)

    async def generate_explanation(
        self, current_truth: CurrentTruthDTO, lang: str, doc_type: str
    ) -> str:
        truth_summary = _format_truth_for_prompt(current_truth)
        lang_name = _LANG_NAME.get(lang, "Marathi")

        prompt = f"""You are a medical assistant explaining a health document to a \
family caregiver in {lang_name}. Be clear, warm, and simple — no jargon.

STRICT RULES (violation = your output is rejected and retried):
1. Never suggest starting, stopping, or changing any dose.
2. Do NOT include any disclaimer or safety note — it is appended automatically by the system.
3. Only describe what is in the extracted data below — nothing else.
4. If a value looks uncertain, say it may need to be checked against the original.
5. Write 3-5 sentences total. Plain language only.

Patient data:
{truth_summary}
"""
        try:
            from google.genai import types

            response, _model = await generate_content_with_fallback(
                self._client(),
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                ),
            )
            explanation = (response.text or "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.warning("gemini explanation failed (%s)", exc)
            raise

        # Disclaimer is appended by explanation.py — do NOT call append_disclaimer here.
        return explanation

    async def generate_brief(self, current_truth: CurrentTruthDTO) -> dict:
        truth_summary = _format_truth_for_prompt(current_truth)
        prompt = f"""Generate a doctor-facing medical brief from this patient data.
Return ONLY valid JSON with this exact structure:
{{
  "one_line": "string",
  "chief_concern": "string",
  "active_medications": [{{"name": "string", "dose": "string or null", "frequency": "string or null"}}],
  "recent_labs": [{{"test": "string", "value": "number or string", "unit": "string or null", "flag": "string or null"}}],
  "active_conditions": [{{"condition": "string"}}],
  "allergies": [{{"substance": "string", "severity": "string or null"}}],
  "timeline": [{{"date": "YYYY-MM-DD", "event": "string"}}],
  "suggested_questions": ["string"],
  "referred_by": "string or null",
  "referral_reason": "string or null",
  "specialist_type": "string or null"
}}
Each medication/condition/allergy MUST be an object, never a plain string.
Be precise and clinical. Never introduce facts not present in the data below.
Do NOT invent safety flags.

Patient data:
{truth_summary}
"""
        try:
            from google.genai import types

            response, _model = await generate_content_with_fallback(
                self._client(),
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="medium"),
                    response_mime_type="application/json",
                ),
            )
            content = json.loads(response.text)
            for k in ("one_line", "chief_concern"):
                if not content.get(k):
                    raise ValueError(f"missing {k}")
            return content
        except Exception as exc:  # noqa: BLE001
            logger.warning("gemini brief failed (%s)", exc)
            raise

    async def generate_summary(self, current_truth: CurrentTruthDTO, brief: dict, lang: str) -> dict:
        # Patient summary is no longer in the pipeline; ABC still requires it.
        from app.services.reasoning.mock import MockReasoner
        return await MockReasoner().generate_summary(current_truth, brief, lang)
