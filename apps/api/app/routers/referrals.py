"""Referral routes. Auto-derive reason from the latest brief when omitted."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient, Referral
from app.db.session import get_db
from app.errors import not_found
from app.ids import new_id
from app.schemas.common import ReferralCreateRequest, ReferralDTO
from app.services import persistence

router = APIRouter(tags=["referrals"])


@router.post("/referrals", response_model=ReferralDTO, status_code=201)
async def create_referral(body: ReferralCreateRequest, db: AsyncSession = Depends(get_db)) -> ReferralDTO:
    patient = (
        await db.execute(select(Patient).where(Patient.id == body.patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", body.patient_id)

    brief = await persistence.latest_brief(db, body.patient_id)
    reason = body.reason
    if not reason and brief is not None:
        reason = brief.chief_concern or brief.one_line

    referral = Referral(
        id=new_id("ref"),
        patient_id=body.patient_id,
        brief_id=brief.brief_id if brief else None,
        specialty=body.specialty,
        reason=reason,
        snapshot_json=brief.model_dump(mode="json") if brief else None,
    )
    db.add(referral)
    await db.commit()
    await db.refresh(referral)
    return ReferralDTO(
        id=referral.id,
        patient_id=referral.patient_id,
        brief_id=referral.brief_id,
        specialty=referral.specialty,
        reason=referral.reason,
        created_at=referral.created_at,
    )
