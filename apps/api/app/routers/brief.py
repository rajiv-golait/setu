"""Doctor Brief routes. GET latest; POST regenerates from current truth."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.deps import get_auth_user_id, get_user_role, require_patient_or_provider_access
from app.errors import NOT_FOUND, AppError
from app.schemas.brief import DoctorBriefDTO
from app.schemas.exports import EsanjeewaniExportDTO, FhirExportDTO
from app.services import persistence
from app.services.audit_phi import audit_phi_read
from app.services.brief import build_brief
from app.services.esanjeewani_export import brief_to_esanjeewani_text
from app.services.fhir_export import brief_to_fhir_bundle
from app.services.memory.persistence import load_current_truth, recompute_current_truth
from app.services.orchestrator import _source_documents
from app.services.reasoning.factory import get_reasoner

router = APIRouter(prefix="/patients", tags=["brief"])


@router.get("/{patient_id}/brief", response_model=DoctorBriefDTO)
async def get_brief(
    request: Request,
    patient: Patient = Depends(require_patient_or_provider_access),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
    role: str = Depends(get_user_role),
) -> DoctorBriefDTO:
    patient_id = patient.id
    brief = await persistence.latest_brief(db, patient_id)
    if brief is None:
        raise AppError(NOT_FOUND, "No brief generated yet", details={"patient_id": patient_id}, retryable=False)
    await audit_phi_read(
        db,
        patient_id=patient_id,
        resource="brief",
        actor_id=auth_user_id,
        actor_role=role,
        request=request,
    )
    await db.commit()
    return brief


@router.post("/{patient_id}/brief", response_model=DoctorBriefDTO, status_code=201)
async def regenerate_brief(
    patient: Patient = Depends(require_patient_or_provider_access),
    db: AsyncSession = Depends(get_db),
) -> DoctorBriefDTO:
    truth = await recompute_current_truth(db, patient.id)
    reasoner = get_reasoner()
    source_docs = await _source_documents(db, patient.id)
    brief = await build_brief(patient.id, truth, reasoner, source_docs)
    await persistence.persist_brief(db, brief)
    await db.commit()
    return brief


async def _load_brief_for_patient(
    db: AsyncSession, patient: Patient
) -> tuple[DoctorBriefDTO, str]:
    patient_id = patient.id
    brief = await persistence.latest_brief(db, patient_id)
    if brief is None:
        raise AppError(NOT_FOUND, "No brief generated yet", details={"patient_id": patient_id}, retryable=False)
    label = patient.display_name or "Patient"
    return brief, label


@router.get("/{patient_id}/brief/fhir", response_model=FhirExportDTO)
async def get_brief_fhir(
    patient: Patient = Depends(require_patient_or_provider_access),
    db: AsyncSession = Depends(get_db),
) -> FhirExportDTO:
    brief, label = await _load_brief_for_patient(db, patient)
    truth = await load_current_truth(db, brief.patient_id)
    bundle = brief_to_fhir_bundle(brief, truth=truth, patient_display=label)
    return FhirExportDTO(patient_id=brief.patient_id, brief_id=brief.brief_id, bundle=bundle)


@router.get("/{patient_id}/brief/exports/esanjeewani", response_model=EsanjeewaniExportDTO)
async def get_brief_esanjeewani(
    patient: Patient = Depends(require_patient_or_provider_access),
    db: AsyncSession = Depends(get_db),
) -> EsanjeewaniExportDTO:
    brief, label = await _load_brief_for_patient(db, patient)
    text = brief_to_esanjeewani_text(brief, patient_label=label)
    return EsanjeewaniExportDTO(patient_id=brief.patient_id, brief_id=brief.brief_id, text=text)


@router.get("/{patient_id}/brief/fhir/download")
async def download_brief_fhir(
    patient: Patient = Depends(require_patient_or_provider_access),
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    brief, label = await _load_brief_for_patient(db, patient)
    truth = await load_current_truth(db, brief.patient_id)
    bundle = brief_to_fhir_bundle(brief, truth=truth, patient_display=label)
    return JSONResponse(
        content=bundle,
        headers={
            "Content-Disposition": f'attachment; filename="setu-{brief.brief_id}.fhir.json"'
        },
    )


@router.get("/{patient_id}/brief/exports/esanjeewani/download")
async def download_brief_esanjeewani(
    patient: Patient = Depends(require_patient_or_provider_access),
    db: AsyncSession = Depends(get_db),
) -> PlainTextResponse:
    brief, label = await _load_brief_for_patient(db, patient)
    text = brief_to_esanjeewani_text(brief, patient_label=label)
    return PlainTextResponse(
        content=text,
        headers={
            "Content-Disposition": f'attachment; filename="setu-{brief.brief_id}-esanjeewani.txt"'
        },
    )
