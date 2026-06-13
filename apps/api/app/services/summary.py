"""Patient Summary engine. Reasoner writes content; we validate + assemble.

If reasoner output fails schema validation the reasoner itself falls back to a
deterministic template (see MockReasoner / MedGemmaReasoner), so this layer
always receives valid content.
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.ids import new_id
from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO
from app.schemas.summary import PatientSummaryDTO
from app.services.reasoning.base import ReasonerProvider


async def build_summary(
    patient_id: str,
    truth: CurrentTruthDTO,
    brief: DoctorBriefDTO,
    reasoner: ReasonerProvider,
    lang: str = "mr",
) -> PatientSummaryDTO:
    content = await reasoner.generate_summary(truth, brief.model_dump(mode="json"), lang)
    return PatientSummaryDTO(
        summary_id=new_id("sum", 3),
        patient_id=patient_id,
        language=lang,
        generated_at=datetime.now(timezone.utc),
        model=getattr(reasoner, "name", "mock"),
        greeting=content["greeting"],
        what_we_found=content.get("what_we_found", []),
        your_medicines=content.get("your_medicines", []),
        what_to_watch=content.get("what_to_watch", []),
        next_steps=content.get("next_steps", []),
        disclaimer=content["disclaimer"],
    )
