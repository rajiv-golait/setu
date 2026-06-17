"""Health worker routes (Phase 6 F4) — proxy register, upload, share."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import jobs_store
from app.db.models import HealthWorker, Patient, PatientLink
from app.db.session import get_db
from app.deps import require_health_worker, require_worker_patient_link
from app.errors import NOT_FOUND, AppError
from app.ids import new_id, new_token
from app.schemas.common import PatientDTO
from app.schemas.consent import consent_text
from app.schemas.health_worker import AssignedPatientDTO, ProxyPatientCreate, WorkerDTO
from app.schemas.share import ShareDTO
from app.services import ingestion, persistence
from app.services.audit import log_access
from app.services.memory.persistence import load_current_truth
from app.services.orchestrator import run_pipeline
from app.services.sharing import build_snapshot, make_qr_svg, share_url

router = APIRouter(prefix="/workers", tags=["health-workers"])

_DOC_TYPE_MAP = {
    "lab report": "lab_report",
    "lab_report": "lab_report",
    "prescription": "prescription",
    "discharge summary": "discharge_summary",
    "discharge_summary": "discharge_summary",
}


def _worker_dto(worker: HealthWorker) -> WorkerDTO:
    return WorkerDTO(
        id=worker.id,
        display_name=worker.display_name,
        facility_name=worker.facility,
        facility_type="phc" if worker.phc_code else None,
        district=worker.phc_code,
        created_at=worker.created_at,
    )


def _normalize_doc_type(raw: str | None, mime: str) -> str:
    if raw:
        key = raw.strip().lower().replace("_", " ")
        if key in _DOC_TYPE_MAP:
            return _DOC_TYPE_MAP[key]
        if raw in _DOC_TYPE_MAP.values():
            return raw
    return "lab_report" if mime == "application/pdf" else "prescription"


@router.get("/me", response_model=WorkerDTO)
async def get_worker_me(worker: HealthWorker = Depends(require_health_worker)) -> WorkerDTO:
    return _worker_dto(worker)


@router.post("/patients", response_model=PatientDTO, status_code=201)
async def register_patient(
    body: ProxyPatientCreate,
    request: Request,
    worker: HealthWorker = Depends(require_health_worker),
    db: AsyncSession = Depends(get_db),
) -> PatientDTO:
    patient = Patient(
        id=new_id("pat"),
        display_name=body.display_name,
        lang_pref=body.lang_pref,
        patient_token=new_token(16),
        registered_by_worker_id=worker.id,
        is_rural=body.is_rural,
    )
    db.add(patient)
    await db.flush()

    link = PatientLink(
        id=new_id("lnk"),
        health_worker_id=worker.id,
        patient_id=patient.id,
        relationship="registered_by",
    )
    db.add(link)

    text = consent_text("document_processing", body.lang_pref)
    await persistence.record_consent(
        db, patient.id, "document_processing", text, body.lang_pref, "health_worker"
    )
    await log_access(
        db,
        actor_id=worker.id,
        actor_role="health_worker",
        patient_id=patient.id,
        resource="patient",
        action="register_patient",
        request=request,
    )
    await db.commit()
    await db.refresh(patient)
    return PatientDTO(
        id=patient.id,
        display_name=patient.display_name,
        lang_pref=patient.lang_pref,
        created_at=patient.created_at,
        patient_token=patient.patient_token,
    )


@router.get("/patients", response_model=list[AssignedPatientDTO])
async def list_assigned_patients(
    worker: HealthWorker = Depends(require_health_worker),
    db: AsyncSession = Depends(get_db),
) -> list[AssignedPatientDTO]:
    rows = (
        await db.execute(
            select(PatientLink, Patient)
            .join(Patient, Patient.id == PatientLink.patient_id)
            .where(PatientLink.health_worker_id == worker.id, PatientLink.active.is_(True))
            .order_by(PatientLink.created_at.desc())
        )
    ).all()
    return [
        AssignedPatientDTO(
            id=patient.id,
            display_name=patient.display_name,
            lang_pref=patient.lang_pref,
            is_rural=patient.is_rural,
            assigned_at=link.created_at,
        )
        for link, patient in rows
    ]


@router.post("/patients/{patient_id}/documents", status_code=202)
async def proxy_upload(
    patient_id: str,
    background: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    doc_type: str | None = Form(default=None),
    patient: Patient = Depends(require_worker_patient_link),
    worker: HealthWorker = Depends(require_health_worker),
    db: AsyncSession = Depends(get_db),
) -> dict:
    await ingestion.require_consent(db, patient.id)

    storage_path, mime, guessed_type, original_hash, enc_key = await ingestion.store_upload(file)
    resolved_type = _normalize_doc_type(doc_type, mime) if doc_type else guessed_type
    doc = await ingestion.create_document(
        db, patient.id, storage_path, mime, resolved_type, original_hash, enc_key
    )
    await log_access(
        db,
        actor_id=worker.id,
        actor_role="health_worker",
        patient_id=patient.id,
        resource="document",
        action="proxy_upload",
        request=request,
    )
    await db.commit()

    job_id = new_id("job")
    state = jobs_store.new_job_state(job_id, doc.id, patient.id)
    await jobs_store.save(state)
    background.add_task(run_pipeline, job_id, doc.id, patient.id)

    return {"document_id": doc.id, "job_id": job_id, "status": "queued"}


@router.post("/patients/{patient_id}/share", response_model=ShareDTO, status_code=201)
async def proxy_share(
    patient_id: str,
    request: Request,
    patient: Patient = Depends(require_worker_patient_link),
    worker: HealthWorker = Depends(require_health_worker),
    db: AsyncSession = Depends(get_db),
) -> ShareDTO:
    brief = await persistence.latest_brief(db, patient.id)
    if brief is None:
        raise AppError(
            NOT_FOUND, "No brief to share yet", details={"patient_id": patient.id}, retryable=False
        )
    truth = await load_current_truth(db, patient.id)
    patient_ref = f"Patient ({patient.display_name})" if patient.display_name else "Patient"
    snapshot = build_snapshot(
        share_id="pending",
        token="pending",
        created_at=datetime.now(timezone.utc),
        expires_at=None,
        patient_ref=patient_ref,
        brief=brief,
        current_truth=truth,
    )
    row = await persistence.create_share(db, patient.id, snapshot.model_dump(mode="json"), None)
    row.snapshot_json["share_id"] = row.id
    row.snapshot_json["token"] = row.token
    row.snapshot_json["created_at"] = row.created_at.isoformat()
    row.snapshot_json["expires_at"] = row.expires_at.isoformat() if row.expires_at else None
    await log_access(
        db,
        actor_id=worker.id,
        actor_role="health_worker",
        patient_id=patient.id,
        resource="share",
        action="proxy_share",
        request=request,
    )
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
