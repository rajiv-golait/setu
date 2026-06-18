"""Vitals routes (Phase 6 F5) — patient or linked health worker."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.deps import (
    _check_patient_access,
    get_auth_user_id,
    get_or_create_health_worker,
    get_user_role,
    require_worker_patient_link,
)
from app.errors import FORBIDDEN, UNAUTHORIZED, AppError
from app.schemas.vitals import VitalCreate, VitalDTO, VitalsSummaryDTO
from app.services import vitals as svc

router = APIRouter(prefix="/patients", tags=["vitals"])

FLAG_MESSAGE = svc.FLAG_MESSAGE


def _to_dto(row, *, source: str) -> VitalDTO:
    return VitalDTO(
        id=row.id,
        patient_id=row.patient_id,
        vital_type=row.vital_type,
        value=row.value,
        unit=row.unit or "",
        measured_at=row.measured_at,
        source=source,
        created_at=row.created_at,
        flag=row.flag,
        flag_message=FLAG_MESSAGE if row.flag == "out_of_range" else None,
    )


async def _require_vitals_access(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    role: str = Depends(get_user_role),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> tuple[Patient, str]:
    """Return (patient, source_label) for patient or linked health worker."""
    if role == "health_worker":
        if auth_user_id is None:
            raise AppError(UNAUTHORIZED, "Authentication required", retryable=False)
        worker = await get_or_create_health_worker(db, auth_user_id)
        patient = await require_worker_patient_link(patient_id, db, worker)
        return patient, "health_worker"
    if role == "patient":
        patient = await _check_patient_access(patient_id, db, auth_user_id)
        return patient, "patient"
    raise AppError(FORBIDDEN, f"Role {role!r} may not access vitals", retryable=False)


@router.post("/{patient_id}/vitals", response_model=VitalDTO, status_code=201)
async def create_vital(
    body: VitalCreate,
    access: tuple[Patient, str] = Depends(_require_vitals_access),
    db: AsyncSession = Depends(get_db),
) -> VitalDTO:
    patient, source = access
    patient_id = patient.id
    recorded_by = body.source or source
    row = await svc.record(
        db,
        patient_id=patient_id,
        vital_type=body.vital_type.value,
        value=body.value,
        unit=body.unit,
        measured_at=body.measured_at,
        recorded_by=recorded_by,
    )
    await db.commit()
    await db.refresh(row)
    return _to_dto(row, source=recorded_by)


@router.get("/{patient_id}/vitals", response_model=list[VitalDTO])
async def list_patient_vitals(
    vital_type: str | None = Query(default=None),
    access: tuple[Patient, str] = Depends(_require_vitals_access),
    db: AsyncSession = Depends(get_db),
) -> list[VitalDTO]:
    patient, source = access
    patient_id = patient.id
    rows = await svc.list_vitals(db, patient_id, vital_type)
    return [_to_dto(r, source=r.recorded_by or source) for r in rows]


@router.get("/{patient_id}/vitals/summary", response_model=VitalsSummaryDTO)
async def vitals_summary(
    access: tuple[Patient, str] = Depends(_require_vitals_access),
    db: AsyncSession = Depends(get_db),
) -> VitalsSummaryDTO:
    patient, source = access
    patient_id = patient.id
    latest: dict[str, VitalDTO] = {}
    trends: dict[str, str] = {}
    for vt in ("blood_pressure", "blood_sugar", "spo2", "heart_rate"):
        series = await svc.series(db, patient_id, vt)
        if series:
            latest[vt] = _to_dto(series[-1], source=series[-1].recorded_by or source)
            trends[vt] = svc.trend_direction(series)
    return VitalsSummaryDTO(patient_id=patient_id, latest=latest, trends=trends)
