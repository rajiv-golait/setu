"""Patient routes. Anonymous record + opaque token (no accounts)."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.errors import not_found
from app.ids import new_id, new_token
from app.schemas.common import PatientCreateRequest, PatientDTO

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("", response_model=PatientDTO, status_code=201)
async def create_patient(body: PatientCreateRequest, db: AsyncSession = Depends(get_db)) -> PatientDTO:
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
    # token returned ONLY on creation.
    return PatientDTO(
        id=patient.id,
        display_name=patient.display_name,
        lang_pref=patient.lang_pref,
        created_at=patient.created_at,
        patient_token=token,
    )


@router.get("/{patient_id}", response_model=PatientDTO)
async def get_patient(patient_id: str, db: AsyncSession = Depends(get_db)) -> PatientDTO:
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)
    return PatientDTO(
        id=patient.id,
        display_name=patient.display_name,
        lang_pref=patient.lang_pref,
        created_at=patient.created_at,
        patient_token=None,
    )
