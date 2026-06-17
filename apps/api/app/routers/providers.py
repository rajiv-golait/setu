"""Provider routes — profile, directory, dashboard, patient access."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Appointment, Encounter, Patient, Provider, ProviderCredential
from app.db.session import get_db
from app.deps import (
    get_auth_user_id,
    require_approved_provider,
    require_auth_user_id,
    require_provider,
    require_provider_patient_access,
)
from app.errors import NOT_FOUND, VALIDATION_ERROR, AppError, not_found
from app.ids import new_id
from app.schemas.brief import DoctorBriefDTO
from app.schemas.provider import (
    CredentialUploadResponse,
    ProviderDashboardDTO,
    ProviderDTO,
    ProviderPublicDTO,
    ProviderRegisterRequest,
    ProviderUpdateRequest,
)
from app.services import ingestion, persistence, supabase_admin
from app.services.audit_phi import audit_phi_read

router = APIRouter(prefix="/providers", tags=["providers"])


def _dto(p: Provider) -> ProviderDTO:
    langs = p.languages if isinstance(p.languages, list) else None
    fee = float(p.consultation_fee) if p.consultation_fee is not None else None
    return ProviderDTO(
        id=p.id,
        display_name=p.display_name,
        specialty=p.specialty,
        facility=p.facility,
        verification_status=p.verification_status,
        experience_years=p.experience_years,
        languages=langs,
        location=p.location,
        consultation_fee=fee,
        bio=p.bio,
        created_at=p.created_at,
    )


def _public(p: Provider) -> ProviderPublicDTO:
    langs = p.languages if isinstance(p.languages, list) else None
    fee = float(p.consultation_fee) if p.consultation_fee is not None else None
    return ProviderPublicDTO(
        id=p.id,
        display_name=p.display_name,
        specialty=p.specialty,
        facility=p.facility,
        experience_years=p.experience_years,
        languages=langs,
        location=p.location,
        consultation_fee=fee,
        bio=p.bio,
    )


@router.get("/me", response_model=ProviderDTO)
async def get_or_create_me(provider: Provider = Depends(require_provider)) -> ProviderDTO:
    return _dto(provider)


@router.post("/register", response_model=ProviderDTO, status_code=201)
async def register_provider(
    body: ProviderRegisterRequest,
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> ProviderDTO:
    """Self-register as a pending doctor (admin must approve before clinical access)."""
    existing = (
        await db.execute(select(Provider).where(Provider.supabase_user_id == auth_user_id))
    ).scalar_one_or_none()
    if existing is not None:
        raise AppError(VALIDATION_ERROR, "Already registered as a provider", retryable=False)
    await supabase_admin.set_user_role(auth_user_id, "provider")
    row = Provider(
        id=new_id("prv"),
        supabase_user_id=auth_user_id,
        display_name=body.display_name,
        specialty=body.specialty,
        facility=body.facility,
        verification_status="pending",
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return _dto(row)


@router.patch("/me", response_model=ProviderDTO)
async def update_me(
    body: ProviderUpdateRequest,
    provider: Provider = Depends(require_provider),
    db: AsyncSession = Depends(get_db),
) -> ProviderDTO:
    for field in (
        "display_name",
        "specialty",
        "facility",
        "experience_years",
        "languages",
        "location",
        "consultation_fee",
        "bio",
    ):
        val = getattr(body, field, None)
        if val is not None:
            setattr(provider, field, val)
    await db.commit()
    await db.refresh(provider)
    return _dto(provider)


@router.get("/me/dashboard", response_model=ProviderDashboardDTO)
async def provider_dashboard(
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> ProviderDashboardDTO:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    pending = (
        await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(Appointment.status == "requested", Appointment.provider_id == provider.id)
        )
    ).scalar_one()

    today = (
        await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.provider_id == provider.id,
                Appointment.scheduled_for >= today_start,
                Appointment.scheduled_for < today_start + timedelta(days=1),
            )
        )
    ).scalar_one()

    completed = (
        await db.execute(
            select(func.count())
            .select_from(Appointment)
            .where(
                Appointment.provider_id == provider.id,
                Appointment.status == "completed",
                Appointment.updated_at >= week_start,
            )
        )
    ).scalar_one()

    patients = (
        await db.execute(
            select(func.count(func.distinct(Appointment.patient_id)))
            .select_from(Appointment)
            .where(Appointment.provider_id == provider.id)
        )
    ).scalar_one()

    follow_ups = (
        await db.execute(
            select(func.count())
            .select_from(Encounter)
            .where(Encounter.provider_id == provider.id, Encounter.status == "open")
        )
    ).scalar_one()

    return ProviderDashboardDTO(
        pending_requests=pending,
        today_appointments=today,
        completed_this_week=completed,
        patient_count=patients,
        follow_ups_due=follow_ups,
    )


@router.get("/me/patients")
async def list_my_patients(
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    rows = (
        await db.execute(
            select(Patient.id, Patient.display_name, func.max(Appointment.updated_at))
            .join(Appointment, Appointment.patient_id == Patient.id)
            .where(Appointment.provider_id == provider.id)
            .group_by(Patient.id, Patient.display_name)
            .order_by(func.max(Appointment.updated_at).desc())
        )
    ).all()
    return [{"id": r[0], "display_name": r[1]} for r in rows]


@router.get("/me/credentials")
async def list_my_credentials(
    provider: Provider = Depends(require_provider),
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    rows = (
        await db.execute(
            select(ProviderCredential).where(ProviderCredential.provider_id == provider.id)
        )
    ).scalars().all()
    return [
        {"id": c.id, "doc_type": c.doc_type, "status": c.status, "created_at": c.created_at.isoformat()}
        for c in rows
    ]


@router.post("/me/credentials", response_model=CredentialUploadResponse, status_code=201)
async def upload_credential(
    doc_type: str = Form(...),
    file: UploadFile = File(...),
    provider: Provider = Depends(require_provider),
    db: AsyncSession = Depends(get_db),
) -> CredentialUploadResponse:
    path, _mime, _gt, _hash, _enc = await ingestion.store_upload(file)
    cred = ProviderCredential(
        id=new_id("cred"),
        provider_id=provider.id,
        doc_type=doc_type,
        storage_path=path,
        status="pending",
    )
    db.add(cred)
    await db.commit()
    return CredentialUploadResponse(id=cred.id, doc_type=doc_type, status=cred.status)


@router.get("/patients/{patient_id}/brief", response_model=DoctorBriefDTO)
async def provider_patient_brief(
    request: Request,
    patient: Patient = Depends(require_provider_patient_access),
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> DoctorBriefDTO:
    brief = await persistence.latest_brief(db, patient.id)
    if brief is None:
        raise AppError(NOT_FOUND, "No brief generated yet", retryable=False)
    await audit_phi_read(
        db,
        patient_id=patient.id,
        resource="brief",
        actor_id=provider.id,
        actor_role="provider",
        request=request,
    )
    await db.commit()
    return brief


@router.get("", response_model=list[ProviderPublicDTO])
async def search_providers(
    specialty: str | None = None,
    location: str | None = None,
    lang: str | None = None,
    limit: int = Query(default=20, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[ProviderPublicDTO]:
    stmt = select(Provider).where(Provider.verification_status == "approved")
    if specialty:
        stmt = stmt.where(Provider.specialty.ilike(f"%{specialty}%"))
    if location:
        stmt = stmt.where(Provider.location.ilike(f"%{location}%"))
    rows = (await db.execute(stmt.order_by(Provider.created_at.desc()).limit(limit))).scalars().all()
    if lang:
        rows = [r for r in rows if lang in (r.languages or [])]
    return [_public(r) for r in rows]


@router.get("/{provider_id}", response_model=ProviderPublicDTO)
async def get_provider_public(provider_id: str, db: AsyncSession = Depends(get_db)) -> ProviderPublicDTO:
    row = (
        await db.execute(
            select(Provider).where(
                Provider.id == provider_id,
                Provider.verification_status == "approved",
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise not_found("Provider", provider_id)
    return _public(row)
