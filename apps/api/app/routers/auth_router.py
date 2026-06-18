"""Unified auth session endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import HealthWorker, Patient, Provider
from app.db.session import get_db
from app.deps import get_auth_user_id, get_user_role
from app.errors import UNAUTHORIZED, AppError
from app.schemas.auth import AuthMeDTO

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=AuthMeDTO)
async def auth_me(
    auth_user_id: str | None = Depends(get_auth_user_id),
    role: str = Depends(get_user_role),
    db: AsyncSession = Depends(get_db),
) -> AuthMeDTO:
    if auth_user_id is None:
        raise AppError(UNAUTHORIZED, "Authentication required", retryable=False)

    patient_id = None
    provider_id = None
    worker_id = None
    verification_status = None

    if role == "patient":
        row = (
            await db.execute(select(Patient).where(Patient.supabase_user_id == auth_user_id))
        ).scalar_one_or_none()
        if row:
            patient_id = row.id
    elif role == "provider":
        row = (
            await db.execute(select(Provider).where(Provider.supabase_user_id == auth_user_id))
        ).scalar_one_or_none()
        if row:
            provider_id = row.id
            verification_status = row.verification_status
    elif role == "health_worker":
        row = (
            await db.execute(select(HealthWorker).where(HealthWorker.supabase_user_id == auth_user_id))
        ).scalar_one_or_none()
        if row:
            worker_id = row.id
    elif role == "admin":
        verification_status = "approved"

    return AuthMeDTO(
        user_id=auth_user_id,
        role=role,
        verification_status=verification_status,
        provider_id=provider_id,
        patient_id=patient_id,
        health_worker_id=worker_id,
    )


@router.post("/dev/ensure-admin")
async def ensure_dev_admin() -> dict:
    """Create or reset the dev admin account (local only). No auth required."""
    if settings.PRODUCTION:
        raise AppError(UNAUTHORIZED, "Not available in production", retryable=False)
    if not settings.SUPABASE_SERVICE_ROLE_KEY:
        return {
            "ok": False,
            "message": (
                "SUPABASE_SERVICE_ROLE_KEY not set in apps/api/.env. "
                "Add it from Supabase → Project Settings → API → service_role (secret), "
                "restart the API, then sign in again."
            ),
        }
    from app.services import supabase_admin

    user_id = await supabase_admin.ensure_email_admin(
        settings.DEV_ADMIN_EMAIL,
        settings.DEV_ADMIN_PASSWORD,
    )
    return {
        "ok": True,
        "email": settings.DEV_ADMIN_EMAIL,
        "user_id": user_id,
    }
