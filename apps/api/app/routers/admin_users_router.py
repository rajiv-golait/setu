"""Admin — set a phone user's portal role (patient or doctor) for testing."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Provider
from app.db.session import get_db
from app.deps import require_admin
from app.ids import new_id
from app.schemas.admin_users import SetUserRoleRequest, SetUserRoleResponse
from app.services import supabase_admin

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.post("/set-role", response_model=SetUserRoleResponse)
async def set_user_role(
    body: SetUserRoleRequest,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> SetUserRoleResponse:
    """Switch a mobile user between patient and doctor portals."""
    phone = supabase_admin.normalize_phone(body.phone)
    user_id = await supabase_admin.ensure_user_with_role(phone, role=body.role)

    provider_id: str | None = None
    existing = (
        await db.execute(select(Provider).where(Provider.supabase_user_id == user_id))
    ).scalar_one_or_none()

    if body.role == "provider":
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
        provider_id = row.id
    else:
        if existing is not None:
            await db.delete(existing)
            await db.commit()

    return SetUserRoleResponse(
        supabase_user_id=user_id,
        phone=phone,
        role=body.role,
        provider_id=provider_id,
    )
