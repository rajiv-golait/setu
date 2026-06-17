"""Shared FastAPI dependencies — Supabase JWT auth + patient access control."""
from __future__ import annotations

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_supabase_role, verify_supabase_token
from app.config import settings
from app.db.models import Appointment, HealthWorker, Patient, Provider, ProviderAccessGrant
from app.db.session import get_db
from app.errors import FORBIDDEN, NOT_FOUND, UNAUTHORIZED, VALIDATION_ERROR, AppError, not_found
from app.ids import new_id

_bearer = HTTPBearer(auto_error=False)


async def get_auth_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str | None:
    """Return Supabase user id when auth is enabled; None in legacy dev mode."""
    if not settings.SUPABASE_ENABLED:
        return None
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(UNAUTHORIZED, "Missing Authorization Bearer token", retryable=False)
    return await verify_supabase_token(credentials.credentials)


async def require_auth_user_id(auth_user_id: str | None = Depends(get_auth_user_id)) -> str:
    """Require a valid Supabase user (for /patients/me)."""
    if not settings.SUPABASE_ENABLED:
        raise AppError(
            VALIDATION_ERROR,
            "Supabase auth is disabled; use POST /patients in dev mode",
            retryable=False,
        )
    if auth_user_id is None:
        raise AppError(UNAUTHORIZED, "Authentication required", retryable=False)
    return auth_user_id


async def _check_patient_access(
    patient_id: str,
    db: AsyncSession,
    auth_user_id: str | None,
) -> Patient:
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)
    if settings.SUPABASE_ENABLED:
        if auth_user_id is None:
            raise AppError(UNAUTHORIZED, "Authentication required", retryable=False)
        if patient.supabase_user_id != auth_user_id:
            raise AppError(
                FORBIDDEN,
                "You do not have access to this patient record",
                details={"patient_id": patient_id},
                retryable=False,
            )
    return patient


async def require_patient_access(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> Patient:
    """Ensure the patient exists and the caller owns the record when auth is on."""
    return await _check_patient_access(patient_id, db, auth_user_id)


# Legacy token header (Telegram/webchat adapters — not used by the web app).
async def get_patient_token(x_patient_token: str | None = Header(default=None)) -> str:
    if not x_patient_token:
        raise AppError(VALIDATION_ERROR, "Missing X-Patient-Token header", retryable=False)
    return x_patient_token


async def require_patient_by_token(
    token: str = Depends(get_patient_token),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    patient = (
        await db.execute(select(Patient).where(Patient.patient_token == token))
    ).scalar_one_or_none()
    if patient is None:
        raise AppError(NOT_FOUND, "Patient not found for token", retryable=False)
    return patient


# --- Role-based access (Phase 1) ----------------------------------------- #
# Role is stored in Supabase app_metadata.role ("patient" | "provider" | "admin";
# "health_worker" is added later in F4). Kept as a plain string comparison so new
# roles slot in without touching this code. require_patient_access above is
# unaffected — patient ownership is independent of these role checks.


async def get_user_role(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Return the caller's role from app_metadata.role. Defaults to 'patient'
    (in both legacy/dev mode and when no role claim is present)."""
    if not settings.SUPABASE_ENABLED:
        return "patient"
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AppError(UNAUTHORIZED, "Missing Authorization Bearer token", retryable=False)
    return await verify_supabase_role(credentials.credentials)


async def require_provider(
    auth_user_id: str = Depends(require_auth_user_id),
    role: str = Depends(get_user_role),
    db: AsyncSession = Depends(get_db),
) -> Provider:
    """Require the 'provider' role and return the Provider row."""
    if role not in ("provider", "admin"):
        raise AppError(FORBIDDEN, "Provider role required", retryable=False)
    if role == "admin":
        # Admins may act as providers in tests; return or create a stub provider row.
        row = (
            await db.execute(select(Provider).where(Provider.supabase_user_id == auth_user_id))
        ).scalar_one_or_none()
        if row is None:
            row = Provider(
                id=new_id("prv"),
                supabase_user_id=auth_user_id,
                verification_status="approved",
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)
        return row
    return await get_or_create_provider(db, auth_user_id)


async def require_approved_provider(
    provider: Provider = Depends(require_provider),
) -> Provider:
    """Block unverified doctors from clinical actions."""
    if provider.verification_status not in ("approved",):
        raise AppError(
            FORBIDDEN,
            "Provider account is not verified yet",
            details={"verification_status": provider.verification_status},
            retryable=False,
        )
    return provider


async def require_provider_patient_access(
    patient_id: str,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    """Provider may read patient data when an active grant or appointment exists."""
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)

    grant = (
        await db.execute(
            select(ProviderAccessGrant).where(
                ProviderAccessGrant.provider_id == provider.id,
                ProviderAccessGrant.patient_id == patient_id,
            )
        )
    ).scalar_one_or_none()
    appt = (
        await db.execute(
            select(Appointment).where(
                Appointment.provider_id == provider.id,
                Appointment.patient_id == patient_id,
                Appointment.status.in_(("accepted", "confirmed", "completed")),
            )
        )
    ).scalar_one_or_none()
    if grant is None and appt is None:
        raise AppError(
            FORBIDDEN,
            "No access grant for this patient",
            details={"patient_id": patient_id},
            retryable=False,
        )
    return patient


async def get_or_create_provider(db: AsyncSession, auth_user_id: str) -> Provider:
    provider = (
        await db.execute(select(Provider).where(Provider.supabase_user_id == auth_user_id))
    ).scalar_one_or_none()
    if provider is None:
        status = "approved" if not settings.SUPABASE_ENABLED else "pending"
        provider = Provider(
            id=new_id("prv"),
            supabase_user_id=auth_user_id,
            verification_status=status,
        )
        db.add(provider)
        await db.commit()
        await db.refresh(provider)
    return provider


async def get_or_create_health_worker(db: AsyncSession, auth_user_id: str) -> HealthWorker:
    worker = (
        await db.execute(
            select(HealthWorker).where(HealthWorker.supabase_user_id == auth_user_id)
        )
    ).scalar_one_or_none()
    if worker is None:
        worker = HealthWorker(id=new_id("hw"), supabase_user_id=auth_user_id, display_name="Worker")
        db.add(worker)
        await db.commit()
        await db.refresh(worker)
    return worker


async def require_health_worker(
    auth_user_id: str = Depends(require_auth_user_id),
    role: str = Depends(get_user_role),
    db: AsyncSession = Depends(get_db),
) -> HealthWorker:
    if role != "health_worker":
        raise AppError(FORBIDDEN, "Health worker role required", retryable=False)
    return await get_or_create_health_worker(db, auth_user_id)


async def require_worker_patient_link(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    worker: HealthWorker = Depends(require_health_worker),
) -> Patient:
    from app.db.models import PatientLink

    link = (
        await db.execute(
            select(PatientLink).where(
                PatientLink.health_worker_id == worker.id,
                PatientLink.patient_id == patient_id,
                PatientLink.active.is_(True),
            )
        )
    ).scalar_one_or_none()
    if link is None:
        raise AppError(
            FORBIDDEN,
            "No active link to this patient",
            details={"patient_id": patient_id},
            retryable=False,
        )
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)
    return patient


async def require_admin(role: str = Depends(get_user_role)) -> str:
    if role != "admin":
        raise AppError(FORBIDDEN, "Admin role required", retryable=False)
    return role
