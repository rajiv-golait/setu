"""Admin routes — grant/revoke doctor (provider) accounts."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Provider, ProviderCredential
from app.db.session import get_db
from app.deps import require_admin
from app.errors import not_found
from app.ids import new_id
from app.schemas.admin_providers import (
    AdminProviderDTO,
    AdminProviderGrant,
    AdminProviderPatch,
    AdminVerifyRequest,
)
from app.services import supabase_admin

router = APIRouter(prefix="/admin/providers", tags=["admin"])


def _dto(row: Provider) -> AdminProviderDTO:
    return AdminProviderDTO(
        id=row.id,
        supabase_user_id=row.supabase_user_id,
        phone=row.phone,
        display_name=row.display_name,
        specialty=row.specialty,
        facility=row.facility,
        verification_status=row.verification_status,
        created_at=row.created_at,
    )


@router.get("", response_model=list[AdminProviderDTO])
async def list_providers(
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminProviderDTO]:
    rows = (
        await db.execute(select(Provider).order_by(Provider.created_at.desc()))
    ).scalars().all()
    return [_dto(r) for r in rows]


@router.post("", response_model=AdminProviderDTO, status_code=201)
async def grant_provider(
    body: AdminProviderGrant,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminProviderDTO:
    phone = supabase_admin.normalize_phone(body.phone)
    user_id = await supabase_admin.ensure_user_with_role(phone, role="provider")

    existing = (
        await db.execute(select(Provider).where(Provider.supabase_user_id == user_id))
    ).scalar_one_or_none()
    if existing is None:
        row = Provider(
            id=new_id("prv"),
            supabase_user_id=user_id,
            phone=phone,
            display_name=body.display_name,
            specialty=body.specialty,
            facility=body.facility,
            verification_status="approved",
            approved_at=datetime.now(timezone.utc),
        )
        db.add(row)
    else:
        row = existing
        row.phone = phone
        row.verification_status = "approved"
        row.approved_at = datetime.now(timezone.utc)
        if body.display_name is not None:
            row.display_name = body.display_name
        if body.specialty is not None:
            row.specialty = body.specialty
        if body.facility is not None:
            row.facility = body.facility

    await db.commit()
    await db.refresh(row)
    return _dto(row)


@router.get("/{provider_id}", response_model=AdminProviderDTO)
async def get_provider(
    provider_id: str,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminProviderDTO:
    row = (
        await db.execute(select(Provider).where(Provider.id == provider_id))
    ).scalar_one_or_none()
    if row is None:
        raise not_found("Provider", provider_id)
    return _dto(row)


@router.get("/{provider_id}/credentials")
async def list_provider_credentials(
    provider_id: str,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    rows = (
        await db.execute(
            select(ProviderCredential).where(ProviderCredential.provider_id == provider_id)
        )
    ).scalars().all()
    return [
        {"id": c.id, "doc_type": c.doc_type, "status": c.status, "created_at": c.created_at.isoformat()}
        for c in rows
    ]


@router.patch("/{provider_id}", response_model=AdminProviderDTO)
async def patch_provider(
    provider_id: str,
    body: AdminProviderPatch,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminProviderDTO:
    row = (
        await db.execute(select(Provider).where(Provider.id == provider_id))
    ).scalar_one_or_none()
    if row is None:
        raise not_found("Provider", provider_id)
    if body.display_name is not None:
        row.display_name = body.display_name
    if body.specialty is not None:
        row.specialty = body.specialty
    if body.facility is not None:
        row.facility = body.facility
    if body.verification_status is not None:
        row.verification_status = body.verification_status
        if body.verification_status == "approved":
            row.approved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    return _dto(row)


@router.post("/{provider_id}/verify", response_model=AdminProviderDTO)
async def verify_provider(
    provider_id: str,
    body: AdminVerifyRequest,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AdminProviderDTO:
    row = (
        await db.execute(select(Provider).where(Provider.id == provider_id))
    ).scalar_one_or_none()
    if row is None:
        raise not_found("Provider", provider_id)
    row.verification_status = body.status
    if body.status == "approved":
        row.approved_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(row)
    return _dto(row)


@router.delete("/{provider_id}", status_code=204)
async def revoke_provider(
    provider_id: str,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    row = (
        await db.execute(select(Provider).where(Provider.id == provider_id))
    ).scalar_one_or_none()
    if row is None:
        raise not_found("Provider", provider_id)
    await supabase_admin.set_user_role(row.supabase_user_id, "patient")
    await db.delete(row)
    await db.commit()
