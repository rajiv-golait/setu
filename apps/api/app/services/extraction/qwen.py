"""Qwen3-VL-8B extractor over an OpenAI-compatible vision endpoint.

The model is reached via QWEN_ENDPOINT and never loaded in-process. The image is
sent as a base64 data URL. Output is coerced into Claims JSON; on any failure the
caller's routing chain (qwen -> cloud -> seeded) takes over.
"""
from __future__ import annotations

import base64
import json
import logging
from datetime import date, datetime, timezone

import httpx

from app.config import settings
from app.schemas.claims import Claim, ClaimsJSON
from app.services.extraction.base import ExtractorProvider
from app.services.memory.reducer import grouping_key  # noqa: F401 (reuse intent)

logger = logging.getLogger("setu.qwen")

EXTRACTION_PROMPT = (
    "You are a medical document extractor. Read this prescription / lab report / "
    "discharge summary and return ONLY JSON: {\"document_type\":..., \"claims\":[...]}. "
    "Each claim: {claim_id, type, fields, confidence (0-1), observed_at (YYYY-MM-DD), "
    "needs_review}. Claim types and required fields: medication(name,dose,dose_unit,"
    "frequency), lab_result(test_name,value,unit), diagnosis(condition,status), "
    "allergy(substance), vital(name,value,unit), procedure(name), advice(text). "
    "If a value is unreadable, OMIT it and set needs_review=true. Never guess."
)


def _data_url(file_path: str, mime: str) -> str:
    with open(file_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("ascii")
    return f"data:{mime};base64,{b64}"


def _coerce_claims(raw: dict, document_id: str, patient_id: str, provider: str) -> ClaimsJSON:
    claims = []
    for i, c in enumerate(raw.get("claims", [])):
        observed = c.get("observed_at")
        try:
            obs_date = date.fromisoformat(observed) if observed else None
        except ValueError:
            obs_date = None
        claims.append(
            Claim(
                claim_id=c.get("claim_id") or f"clm_{i:03d}",
                type=c["type"],
                fields=c.get("fields", {}),
                confidence=float(c.get("confidence", 0.5)),
                observed_at=obs_date,
                needs_review=bool(c.get("needs_review", False)),
            )
        )
    overall = round(sum(float(c.confidence) for c in claims) / len(claims), 2) if claims else 0.0
    return ClaimsJSON(
        document_id=document_id,
        patient_id=patient_id,
        extracted_at=datetime.now(timezone.utc),
        provider=provider,
        document_type=raw.get("document_type", "other"),
        overall_confidence=overall,
        claims=claims,
    )


class QwenExtractor(ExtractorProvider):
    name = "qwen3-vl-8b"

    async def extract(self, file_path: str, mime: str, *, patient_id: str, document_id: str) -> ClaimsJSON:
        payload = {
            "model": "qwen3-vl-8b",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": EXTRACTION_PROMPT},
                        {"type": "image_url", "image_url": {"url": _data_url(file_path, mime)}},
                    ],
                }
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{settings.QWEN_ENDPOINT.rstrip('/')}/chat/completions", json=payload
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            raw = json.loads(content)
        return _coerce_claims(raw, document_id, patient_id, self.name)
