"""Triage routes (Phase 6 F1) — NON-DIAGNOSTIC care routing.

POST runs the deterministic engine and persists the result; GET returns the
history (latest first) for audit and the patient UI. priority/recommendation
come from services/triage_service.assess() — never from a model.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Patient
from app.db.models import TriageResult as TriageRow
from app.db.session import get_db
from app.deps import (
    _check_patient_access,
    get_auth_user_id,
    get_or_create_health_worker,
    get_user_role,
    require_worker_patient_link,
)
from app.errors import FORBIDDEN, UNAUTHORIZED, AppError
from app.ids import new_id
from app.schemas.triage import TriageRequest, TriageResultDTO
from app.services.triage_service import RULESET_VERSION, assess, message_for

router = APIRouter(prefix="/patients", tags=["triage"])


async def _require_triage_access(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(get_user_role),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> tuple[Patient, str]:
    if role == "health_worker":
        if auth_user_id is None:
            raise AppError(UNAUTHORIZED, "Authentication required", retryable=False)
        worker = await get_or_create_health_worker(db, auth_user_id)
        patient = await require_worker_patient_link(patient_id, db, worker)
        return patient, worker.id
    if role == "patient":
        patient = await _check_patient_access(patient_id, db, auth_user_id)
        return patient, "patient"
    raise AppError(FORBIDDEN, f"Role {role!r} may not run triage", retryable=False)


def _to_dto(row: TriageRow) -> TriageResultDTO:
    return TriageResultDTO(
        id=row.id,
        patient_id=row.patient_id,
        priority=row.priority,
        recommendation=row.recommendation,
        rationale=row.rationale,
        message=row.message,
        lang=row.lang,
        engine_version=row.engine_version,
        created_at=row.created_at,
    )


@router.post("/{patient_id}/triage", response_model=TriageResultDTO, status_code=201)
async def run_triage(
    body: TriageRequest,
    access: tuple[Patient, str] = Depends(_require_triage_access),
    db: AsyncSession = Depends(get_db),
) -> TriageResultDTO:
    patient, created_by = access
    patient_id = patient.id
    lang = patient.lang_pref or "mr"

    decision = assess(body.symptoms, body.age, body.existing_conditions)
    message = message_for(decision.recommendation, lang)

    row = TriageRow(
        id=new_id("trg"),
        patient_id=patient_id,
        inputs=body.model_dump(mode="json"),
        priority=decision.priority,
        recommendation=decision.recommendation,
        rationale=decision.rationale(),
        message=message,
        lang=lang,
        engine_version=RULESET_VERSION,
        created_by=created_by,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _to_dto(row)


@router.get("/{patient_id}/triage", response_model=list[TriageResultDTO])
async def list_triage(
    access: tuple[Patient, str] = Depends(_require_triage_access),
    db: AsyncSession = Depends(get_db),
) -> list[TriageResultDTO]:
    patient, _created_by = access
    patient_id = patient.id
    rows = (
        await db.execute(
            select(TriageRow)
            .where(TriageRow.patient_id == patient_id)
            .order_by(TriageRow.created_at.desc())
        )
    ).scalars().all()
    return [_to_dto(r) for r in rows]
