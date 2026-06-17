"""Patient routes — Supabase-linked records + legacy anonymous create."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import AccessLog, Patient, PatientProfile
from app.db.session import get_db
from app.deps import require_auth_user_id, require_patient_access
from app.errors import FORBIDDEN, AppError, not_found
from app.ids import new_id, new_token
from app.schemas.access_log import AccessLogDTO
from app.schemas.common import PatientCreateRequest, PatientDTO, PatientUpdateRequest
from app.schemas.patient_profile import PatientProfileDTO, PatientProfileUpdate
from app.services import retention

router = APIRouter(prefix="/patients", tags=["patients"])


def _patient_dto(patient: Patient, *, include_token: bool = False) -> PatientDTO:
    return PatientDTO(
        id=patient.id,
        display_name=patient.display_name,
        lang_pref=patient.lang_pref,
        created_at=patient.created_at,
        patient_token=patient.patient_token if include_token else None,
    )


@router.get("/me", response_model=PatientDTO)
async def get_or_create_me(
    db: AsyncSession = Depends(get_db),
    auth_user_id: str = Depends(require_auth_user_id),
) -> PatientDTO:
    """Find or create the patient record linked to the authenticated Supabase user."""
    patient = (
        await db.execute(select(Patient).where(Patient.supabase_user_id == auth_user_id))
    ).scalar_one_or_none()
    if patient is None:
        patient = Patient(
            id=new_id("pat"),
            display_name=None,
            lang_pref="mr",
            patient_token=new_token(16),
            supabase_user_id=auth_user_id,
        )
        db.add(patient)
        await db.commit()
        await db.refresh(patient)
    return _patient_dto(patient)


@router.patch("/me", response_model=PatientDTO)
async def update_me(
    body: PatientUpdateRequest,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str = Depends(require_auth_user_id),
) -> PatientDTO:
    patient = (
        await db.execute(select(Patient).where(Patient.supabase_user_id == auth_user_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", auth_user_id)
    if body.display_name is not None:
        patient.display_name = body.display_name
    if body.lang_pref is not None:
        patient.lang_pref = body.lang_pref
    await db.commit()
    await db.refresh(patient)
    return _patient_dto(patient)


@router.post("", response_model=PatientDTO, status_code=201)
async def create_patient(body: PatientCreateRequest, db: AsyncSession = Depends(get_db)) -> PatientDTO:
    """Legacy anonymous patient create — disabled when Supabase auth is enabled."""
    if settings.SUPABASE_ENABLED:
        raise AppError(
            FORBIDDEN,
            "Anonymous patient creation is disabled. Sign in and use GET /patients/me.",
            retryable=False,
        )
    token = new_token(16)
    patient = Patient(
        id=new_id("pat"),
        display_name=body.display_name,
        lang_pref=body.lang_pref,
        patient_token=token,
    )
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return _patient_dto(patient, include_token=True)


@router.get("/{patient_id}", response_model=PatientDTO)
async def get_patient(
    patient: Patient = Depends(require_patient_access),
) -> PatientDTO:
    return _patient_dto(patient)


@router.delete("/{patient_id}/data")
async def delete_my_data(
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """DPDP erasure: purge ALL raw images for this patient."""
    return await retention.delete_patient_data(db, patient.id)


@router.get("/{patient_id}/access-log", response_model=list[AccessLogDTO])
async def list_access_log(
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
) -> list[AccessLogDTO]:
    patient_id = settings.SEED_PATIENT_ID if settings.DEMO_MODE else patient.id
    rows = (
        await db.execute(
            select(AccessLog)
            .where(AccessLog.patient_id == patient_id)
            .order_by(AccessLog.created_at.desc())
            .limit(min(limit, 100))
        )
    ).scalars().all()
    return [
        AccessLogDTO(
            id=r.id,
            actor_role=r.actor_role,
            action=r.action,
            resource=r.resource,
            created_at=r.created_at,
        )
        for r in rows
    ]


def _profile_dto(row: PatientProfile) -> PatientProfileDTO:
    return PatientProfileDTO(
        patient_id=row.patient_id,
        date_of_birth=row.date_of_birth,
        gender=row.gender,
        blood_group=row.blood_group,
        allergies_known=row.allergies_known,
        chronic_conditions=row.chronic_conditions,
        emergency_contact=row.emergency_contact,
        district=row.district,
        state=row.state,
        updated_at=row.updated_at,
    )


@router.get("/me/profile", response_model=PatientProfileDTO)
async def get_my_profile(
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> PatientProfileDTO:
    patient = (
        await db.execute(select(Patient).where(Patient.supabase_user_id == auth_user_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", auth_user_id)
    row = (
        await db.execute(select(PatientProfile).where(PatientProfile.patient_id == patient.id))
    ).scalar_one_or_none()
    if row is None:
        row = PatientProfile(patient_id=patient.id)
        db.add(row)
        await db.commit()
        await db.refresh(row)
    return _profile_dto(row)


@router.patch("/me/profile", response_model=PatientProfileDTO)
async def update_my_profile(
    body: PatientProfileUpdate,
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> PatientProfileDTO:
    from datetime import datetime, timezone

    patient = (
        await db.execute(select(Patient).where(Patient.supabase_user_id == auth_user_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", auth_user_id)
    row = (
        await db.execute(select(PatientProfile).where(PatientProfile.patient_id == patient.id))
    ).scalar_one_or_none()
    if row is None:
        row = PatientProfile(patient_id=patient.id)
        db.add(row)
    for field in body.model_fields:
        val = getattr(body, field, None)
        if val is not None:
            setattr(row, field, val)
    row.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    return _profile_dto(row)
