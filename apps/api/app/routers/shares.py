"""Share routes. POST creates a frozen snapshot + QR. GET /{token} is PUBLIC."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import _check_patient_access, get_auth_user_id
from app.errors import NOT_FOUND, AppError, not_found
from app.schemas.share import ShareCreateRequest, ShareDTO, ShareSnapshotDTO
from app.services import persistence
from app.services.audit import log_access
from app.services.esanjeewani_export import brief_to_esanjeewani_text
from app.services.fhir_export import brief_to_fhir_bundle
from app.services.memory.persistence import load_current_truth
from app.services.sharing import build_snapshot, make_qr_svg, share_url

router = APIRouter(tags=["shares"])


async def _fetch_share_snapshot(
    db: AsyncSession,
    token: str,
    *,
    request: Request | None = None,
    audit_view: bool = False,
) -> ShareSnapshotDTO:
    row = await persistence.get_share(db, token)
    if row is None:
        raise not_found("Share", token)
    if row.expires_at is not None:
        expires = row.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < datetime.now(timezone.utc):
            raise AppError(NOT_FOUND, "Share has expired", details={"token": token}, retryable=False)

    if audit_view:
        await log_access(
            db,
            actor_id=None,
            actor_role="public",
            patient_id=row.patient_id,
            resource="brief",
            action="view",
            request=request,
        )

    row.view_count = (row.view_count or 0) + 1
    await db.commit()
    return ShareSnapshotDTO.model_validate(row.snapshot_json)


def _with_audience(snapshot: ShareSnapshotDTO, view: str | None) -> ShareSnapshotDTO:
    audience = "specialist" if view == "specialist" else "patient"
    return snapshot.model_copy(update={"audience": audience})


def _share_dto_from_row(row) -> ShareDTO:
    url = share_url(row.token)
    return ShareDTO(
        share_id=row.id,
        token=row.token,
        url=url,
        qr_svg=make_qr_svg(url),
        created_at=row.created_at,
        expires_at=row.expires_at,
    )


@router.get("/patients/{patient_id}/share", response_model=ShareDTO)
async def get_latest_patient_share(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> ShareDTO:
    """Latest valid share link + QR for this patient (created during upload or on /share)."""
    patient = await _check_patient_access(patient_id, db, auth_user_id)
    row = await persistence.latest_share(db, patient.id)
    if row is None:
        raise not_found("Share", patient_id)
    return _share_dto_from_row(row)


@router.post("/shares", response_model=ShareDTO, status_code=201)
async def create_share(
    body: ShareCreateRequest,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> ShareDTO:
    patient = await _check_patient_access(body.patient_id, db, auth_user_id)

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

    return _share_dto_from_row(row)


@router.get("/shares/{token}", response_model=ShareSnapshotDTO)
async def get_share(token: str, db: AsyncSession = Depends(get_db)) -> ShareSnapshotDTO:
    """PUBLIC — no token header required."""
    return await _fetch_share_snapshot(db, token)


@router.get("/brief/{token}", response_model=ShareSnapshotDTO)
async def get_brief_snapshot(
    token: str,
    request: Request,
    view: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
) -> ShareSnapshotDTO:
    """PUBLIC — same frozen snapshot as /shares/{token}; ?view=specialist echoes audience."""
    snapshot = await _fetch_share_snapshot(db, token, request=request, audit_view=True)
    return _with_audience(snapshot, view)


@router.get("/brief/{token}/fhir")
async def get_public_brief_fhir(token: str, db: AsyncSession = Depends(get_db)) -> JSONResponse:
    """PUBLIC — FHIR Bundle for a frozen share snapshot."""
    snapshot = await _fetch_share_snapshot(db, token)
    bundle = brief_to_fhir_bundle(
        snapshot.brief,
        truth=snapshot.current_truth,
        patient_display=snapshot.patient_ref,
    )
    return JSONResponse(content=bundle)


@router.get("/brief/{token}/exports/esanjeewani")
async def get_public_brief_esanjeewani(
    token: str, db: AsyncSession = Depends(get_db)
) -> PlainTextResponse:
    """PUBLIC — eSanjeevani-formatted text for a frozen share snapshot."""
    snapshot = await _fetch_share_snapshot(db, token)
    text = brief_to_esanjeewani_text(snapshot.brief, patient_label=snapshot.patient_ref)
    return PlainTextResponse(content=text)
