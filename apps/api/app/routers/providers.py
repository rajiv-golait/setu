"""Provider routes (Phase 1 — role foundation).

Only GET /providers/me for now: fetch the authenticated provider's profile,
auto-provisioning the row on first call (mirrors patient GET /me). The
doctor-side appointment/portal endpoints build on this in later phases.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Provider
from app.db.session import get_db
from app.deps import require_provider
from app.schemas.provider import ProviderDTO, ProviderUpdateRequest

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/me", response_model=ProviderDTO)
async def get_or_create_me(provider: Provider = Depends(require_provider)) -> ProviderDTO:
    return ProviderDTO(
        id=provider.id,
        display_name=provider.display_name,
        specialty=provider.specialty,
        facility=provider.facility,
        created_at=provider.created_at,
    )


@router.patch("/me", response_model=ProviderDTO)
async def update_me(
    body: ProviderUpdateRequest,
    provider: Provider = Depends(require_provider),
    db: AsyncSession = Depends(get_db),
) -> ProviderDTO:
    if body.display_name is not None:
        provider.display_name = body.display_name
    if body.specialty is not None:
        provider.specialty = body.specialty
    if body.facility is not None:
        provider.facility = body.facility
    await db.commit()
    await db.refresh(provider)
    return ProviderDTO(
        id=provider.id,
        display_name=provider.display_name,
        specialty=provider.specialty,
        facility=provider.facility,
        created_at=provider.created_at,
    )
