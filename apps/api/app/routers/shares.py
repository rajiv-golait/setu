"""Share routes. POST creates a frozen snapshot + QR. GET /{token} is PUBLIC."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.errors import NOT_FOUND, AppError, not_found
from app.schemas.share import ShareCreateRequest, ShareDTO, ShareSnapshotDTO
from app.services import persistence
from app.services.memory.persistence import load_current_truth
from app.services.sharing import build_snapshot, make_qr_svg, share_url

router = APIRouter(tags=["shares"])


async def _fetch_share_snapshot(db: AsyncSession, token: str) -> ShareSnapshotDTO:
    row = await persistence.get_share(db, token)
    if row is None:
        raise not_found("Share", token)
    if row.expires_at is not None:
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise AppError(NOT_FOUND, "Share has expired", details={"token": token}, retryable=False)

    row.view_count = (row.view_count or 0) + 1
    await db.commit()
    return ShareSnapshotDTO.model_validate(row.snapshot_json)


def _with_audience(snapshot: ShareSnapshotDTO, view: str | None) -> ShareSnapshotDTO:
    audience = "specialist" if view == "specialist" else "patient"
    return snapshot.model_copy(update={"audience": audience})


@router.post("/shares", response_model=ShareDTO, status_code=201)
async def create_share(body: ShareCreateRequest, db: AsyncSession = Depends(get_db)) -> ShareDTO:
    patient = (
        await db.execute(select(Patient).where(Patient.id == body.patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", body.patient_id)

    brief = await persistence.latest_brief(db, body.patient_id)
    if brief is None:
        raise AppError(NOT_FOUND, "No brief to share yet", details={"patient_id": body.patient_id}, retryable=False)
    truth = await load_current_truth(db, body.patient_id)

    # Freeze a snapshot (immutable copies). Token + url + QR generated on top.
    patient_ref = f"Patient ({patient.display_name})" if patient.display_name else "Patient"
    snapshot = build_snapshot(
        share_id="pending", token="pending",
        created_at=datetime.now(timezone.utc), expires_at=None,
        patient_ref=patient_ref, brief=brief, current_truth=truth,
    )
    row = await persistence.create_share(db, body.patient_id, snapshot.model_dump(mode="json"), body.expires_in)
    # Backfill real ids into the stored snapshot for consistency.
    row.snapshot_json["share_id"] = row.id
    row.snapshot_json["token"] = row.token
    row.snapshot_json["created_at"] = row.created_at.isoformat()
    row.snapshot_json["expires_at"] = row.expires_at.isoformat() if row.expires_at else None
    await db.commit()

    url = share_url(row.token)
    return ShareDTO(
        share_id=row.id,
        token=row.token,
        url=url,
        qr_svg=make_qr_svg(url),
        created_at=row.created_at,
        expires_at=row.expires_at,
    )


@router.get("/shares/{token}", response_model=ShareSnapshotDTO)
async def get_share(token: str, db: AsyncSession = Depends(get_db)) -> ShareSnapshotDTO:
    """PUBLIC — no token header required."""
    return await _fetch_share_snapshot(db, token)


@router.get("/brief/{token}", response_model=ShareSnapshotDTO)
async def get_brief_snapshot(
    token: str,
    view: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ShareSnapshotDTO:
    """PUBLIC — same frozen snapshot as /shares/{token}; ?view=specialist echoes audience."""
    snapshot = await _fetch_share_snapshot(db, token)
    return _with_audience(snapshot, view)
