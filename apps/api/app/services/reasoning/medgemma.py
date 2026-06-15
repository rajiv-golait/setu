"""MedGemma-4B reasoner over an OpenAI-compatible HTTP endpoint.

The model is NEVER loaded in-process — it is reached via MEDGEMMA_ENDPOINT.
On ANY failure (network, malformed JSON, schema mismatch) we fall back to the
deterministic MockReasoner so the pipeline never ships empty/garbled output.
"""
from __future__ import annotations

import json
import logging

import httpx

from app.config import settings
from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO
from app.schemas.summary import PatientSummaryDTO
from app.services.reasoning.base import ReasonerProvider
from app.services.reasoning.mock import MockReasoner

logger = logging.getLogger("setu.medgemma")

_BRIEF_SYSTEM = (
    "You are a clinical scribe. Given a patient's structured Current Truth, write "
    "concise doctor-facing prose. Return ONLY JSON with keys: one_line, "
    "chief_concern, active_medications, recent_labs, active_conditions, allergies, "
    "timeline, suggested_questions. Do NOT invent safety flags."
)
_SUMMARY_SYSTEM = (
    "You translate a clinical brief into plain, reassuring patient language in the "
    "requested language. Return ONLY JSON with keys: greeting, what_we_found, "
    "your_medicines, what_to_watch, next_steps, disclaimer."
)


class MedGemmaReasoner(ReasonerProvider):
    name = "medgemma-4b"

    def __init__(self) -> None:
        self._fallback = MockReasoner()

    async def _chat(self, system: str, user: str) -> dict:
        payload = {
            "model": "medgemma-4b",
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{settings.MEDGEMMA_ENDPOINT.rstrip('/')}/chat/completions", json=payload
            )
            resp.raise_for_status()
            content = resp.json()["choices"][0]["message"]["content"]
            return json.loads(content)

    async def generate_brief(self, current_truth: CurrentTruthDTO) -> dict:
        user = json.dumps(current_truth.model_dump(mode="json"), ensure_ascii=False)
        try:
            content = await self._chat(_BRIEF_SYSTEM, user)
            # Validate against the brief content shape by trial-merging required keys.
            for k in ("one_line", "chief_concern"):
                if not content.get(k):
                    raise ValueError(f"missing {k}")
            return content
        except Exception as exc:  # noqa: BLE001 — any failure routes to fallback
            logger.warning("medgemma brief failed (%s); using mock fallback", exc)
            return await self._fallback.generate_brief(current_truth)

    async def generate_summary(self, current_truth: CurrentTruthDTO, brief: dict, lang: str) -> dict:
        user = json.dumps({"brief": brief, "lang": lang}, ensure_ascii=False)
        try:
            content = await self._chat(_SUMMARY_SYSTEM, user)
            # Schema-validate; on failure, deterministic template fallback.
            PatientSummaryDTO(
                summary_id="sum_probe",
                patient_id=current_truth.patient_id,
                language=lang,
                generated_at=current_truth.generated_at,
                model=self.name,
                greeting=content["greeting"],
                what_we_found=content.get("what_we_found", []),
                your_medicines=content.get("your_medicines", []),
                what_to_watch=content.get("what_to_watch", []),
                next_steps=content.get("next_steps", []),
                disclaimer=content["disclaimer"],
            )
            return content
        except Exception as exc:  # noqa: BLE001
            logger.warning("medgemma summary failed (%s); using template fallback", exc)
            return await self._fallback.generate_summary(current_truth, brief, lang)

    async def generate_explanation(
        self, current_truth: CurrentTruthDTO, lang: str, doc_type: str
    ) -> str:
        # MedGemma has no dedicated explanation path; delegate to the deterministic
        # mock so it stays consistent with the actual patient data.
        return await self._fallback.generate_explanation(current_truth, lang, doc_type)


# satisfy type-checkers that DoctorBriefDTO import is intentional (shape reference)
_ = DoctorBriefDTO
