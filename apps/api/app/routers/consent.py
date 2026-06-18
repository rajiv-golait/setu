"""DPDP consent endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import _check_patient_access, get_auth_user_id
from app.schemas.consent import (
    ConsentCreateRequest,
    ConsentDTO,
    ConsentStatusDTO,
    ConsentWithdrawRequest,
    ConsentWithdrawResponse,
    consent_text,
)
from app.services import persistence
from app.services.audit import log_access

router = APIRouter(prefix="/consent", tags=["consent"])


@router.get("/status", response_model=ConsentStatusDTO)
async def consent_status(
    patient_id: str,
    purpose: str = "document_processing",
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> ConsentStatusDTO:
    """Whether this patient already granted consent (survives logout / new browser)."""
    patient = await _check_patient_access(patient_id, db, auth_user_id)
    granted = await persistence.has_consent(db, patient.id, purpose)
    return ConsentStatusDTO(patient_id=patient.id, purpose=purpose, granted=granted)


@router.post("", response_model=ConsentDTO, status_code=201)
async def grant_consent(
    body: ConsentCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> ConsentDTO:
    patient = await _check_patient_access(body.patient_id, db, auth_user_id)

    if await persistence.has_consent(db, patient.id, body.purpose):
        row = await persistence.get_latest_consent(db, patient.id, body.purpose)
        assert row is not None
        return ConsentDTO(
            consent_id=row.id,
            patient_id=row.patient_id,
            purpose=row.purpose,
            consent_text=row.consent_text,
            lang=row.lang,
            channel=row.channel,
            granted_at=row.granted_at,
        )

    text = consent_text(body.purpose, body.lang)
    row = await persistence.record_consent(
        db, patient.id, body.purpose, text, body.lang, body.channel
    )
    await log_access(
        db,
        actor_id=auth_user_id,
        actor_role="patient",
        patient_id=patient.id,
        resource="consent",
        action="grant_consent",
        request=request,
    )
    await db.commit()

    return ConsentDTO(
        consent_id=row.id,
        patient_id=row.patient_id,
        purpose=row.purpose,
        consent_text=row.consent_text,
        lang=row.lang,
        channel=row.channel,
        granted_at=row.granted_at,
    )


@router.post("/withdraw", response_model=ConsentWithdrawResponse)
async def withdraw_consent(
    body: ConsentWithdrawRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> ConsentWithdrawResponse:
    patient = await _check_patient_access(body.patient_id, db, auth_user_id)
    withdrawn = await persistence.revoke_consent(db, patient.id, body.purpose)
    if withdrawn:
        await log_access(
            db,
            actor_id=auth_user_id,
            actor_role="patient",
            patient_id=patient.id,
            resource="consent",
            action="withdraw_consent",
            request=request,
        )
    await db.commit()
    return ConsentWithdrawResponse(
        withdrawn=withdrawn,
        patient_id=patient.id,
        purpose=body.purpose,
    )
