"""Cloud extractor — Gemini Flash (free-tier chain) with OpenAI fallback.

Multimodal OCR + structured JSON via generateContent. Model order is defined in
gemini_models.GEMINI_MODEL_CHAIN (quality-first: 3.5 → 2.5 → …).
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import date, datetime, timezone

import httpx

from app.config import settings
from app.schemas.claims import ClaimsJSON
from app.services.extraction.base import ExtractorProvider
from app.services.extraction.qwen import EXTRACTION_PROMPT, _coerce_claims
from app.services.gemini_client import generate_content_with_fallback, is_quota_exhausted
from app.services.gemini_models import GEMINI_DEFAULT_MODEL

logger = logging.getLogger("setu.cloud")


class ExtractionError(RuntimeError):
    """Raised on a cloud extraction failure; retryable failures fall through the chain."""

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.retryable = retryable


GEMINI_MODEL = GEMINI_DEFAULT_MODEL

GEMINI_EXTRACTION_PROMPT = """\
You are a medical document parser. Extract all medical claims from this image.
The document may be handwritten, printed, in English, Hindi, Marathi, or mixed.

Return ONLY valid JSON — no prose, no markdown, no backticks.

Schema:
{
  "document_type": "prescription|lab_result|discharge_summary|other",
  "overall_confidence": 0.0-1.0,
  "claims": [
    {
      "claim_id": "optional — server assigns a unique id",
      "type": "medication|lab_result|diagnosis|allergy|vital|procedure|advice",
      "fields": { ... },
      "confidence": 0.0-1.0,
      "observed_at": "YYYY-MM-DD or null",
      "needs_review": false
    }
  ]
}

Required fields per type: medication(name,dose,dose_unit,frequency),
lab_result(test_name,value,unit), diagnosis(condition,status),
allergy(substance), vital(name,value,unit), procedure(name), advice(text).

Rules:
1. If a field is unclear or unreadable, OMIT it — never guess.
2. Set confidence < 0.7 for any unclear claim and needs_review: true.
3. overall_confidence = mean of all claim confidences.
4. If the image is unreadable: return overall_confidence < 0.4 and claims: [].
"""


def _coerce_gemini(raw: dict, document_id: str, patient_id: str, *, model: str) -> ClaimsJSON:
    """Like qwen._coerce_claims, but PRESERVES the model's overall_confidence
    when present (the abstain-on-unreadable path at <0.4 depends on it)."""
    coerced = _coerce_claims(raw, document_id, patient_id, model)
    model_overall = raw.get("overall_confidence")
    if model_overall is not None:
        try:
            coerced.overall_confidence = max(0.0, min(1.0, float(model_overall)))
        except (TypeError, ValueError):
            pass
    return coerced


class CloudExtractor(ExtractorProvider):
    name = "cloud"

    async def extract(
        self, file_path: str, mime: str, *, patient_id: str, document_id: str
    ) -> ClaimsJSON:
        provider = settings.CLOUD_API_PROVIDER
        if provider == "gemini":
            if not settings.GOOGLE_API_KEY:
                raise ExtractionError("Gemini not configured (GOOGLE_API_KEY)", retryable=False)
            try:
                raw, model_used = await self._call_gemini(file_path, mime)
                return _coerce_gemini(raw, document_id, patient_id, model=model_used)
            except ExtractionError:
                if settings.OPENAI_API_KEY:
                    logger.warning("gemini chain failed; trying OpenAI extraction fallback")
                    raw = await self._call_openai(file_path, mime)
                    return _coerce_claims(raw, document_id, patient_id, "cloud:openai")
                raise
        if provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ExtractionError("OpenAI not configured (OPENAI_API_KEY)", retryable=False)
            raw = await self._call_openai(file_path, mime)
            return _coerce_claims(raw, document_id, patient_id, "cloud:openai")
        raise ExtractionError(f"unknown CLOUD_API_PROVIDER: {provider!r}", retryable=False)

    async def _call_gemini(self, file_path: str, mime: str) -> tuple[dict, str]:
        from google import genai
        from google.genai import types

        with open(file_path, "rb") as f:
            image_bytes = f.read()

        client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        try:
            response, model_used = await generate_content_with_fallback(
                client,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type=mime),
                    types.Part.from_text(text=GEMINI_EXTRACTION_PROMPT),
                ],
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_level="low"),
                    response_mime_type="application/json",
                ),
            )
            return json.loads(response.text), model_used
        except json.JSONDecodeError as e:
            raise ExtractionError(f"Gemini returned invalid JSON: {e}", retryable=True) from e
        except RuntimeError as e:
            quota_hit = is_quota_exhausted(e.__cause__ or e)
            hint = ""
            if quota_hit:
                hint = (
                    " Gemini API quota exhausted — enable billing at "
                    "https://aistudio.google.com/apikey and update GOOGLE_API_KEY, "
                    "or set OPENAI_API_KEY for OpenAI fallback."
                )
            raise ExtractionError(f"Gemini extraction failed: {e}.{hint}", retryable=not quota_hit) from e

    async def _call_openai(self, file_path: str, mime: str) -> dict:
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        payload = {
            "model": "gpt-4o",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    ],
                }
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
        headers = {"Authorization": f"Bearer {settings.OPENAI_API_KEY}"}
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions", json=payload, headers=headers
                )
                resp.raise_for_status()
                content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)
        except Exception as e:  # noqa: BLE001
            raise ExtractionError(f"OpenAI extraction failed: {e}", retryable=True) from e


# keep timestamp import used (mirrors qwen module structure)
_ = (date, datetime.now(timezone.utc))
