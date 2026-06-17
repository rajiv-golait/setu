"""Document upload + retrieval. Upload starts the pipeline via BackgroundTasks."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import jobs_store
from app.db.models import Document, Extraction, Patient
from app.db.session import get_db
from app.deps import _check_patient_access, get_auth_user_id, require_patient_access
from app.errors import not_found
from app.ids import new_id
from app.schemas.claims import ClaimsJSON
from app.schemas.common import DocumentDTO, DocumentListItem, DocumentUploadResponse
from app.services import ingestion, retention
from app.services.orchestrator import run_pipeline

router = APIRouter(tags=["documents"])

_DOC_TYPE_MAP = {
    "lab report": "lab_report",
    "lab_report": "lab_report",
    "prescription": "prescription",
    "discharge summary": "discharge_summary",
    "discharge_summary": "discharge_summary",
}


def _normalize_doc_type(raw: str | None, mime: str) -> str:
    if raw:
        key = raw.strip().lower().replace("_", " ")
        if key in _DOC_TYPE_MAP:
            return _DOC_TYPE_MAP[key]
        if raw in _DOC_TYPE_MAP.values():
            return raw
    return "lab_report" if mime == "application/pdf" else "prescription"


@router.post("/documents", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    doc_type: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> DocumentUploadResponse:
    await _check_patient_access(patient_id, db, auth_user_id)
    await ingestion.require_consent(db, patient_id)

    storage_path, mime, guessed_type, original_hash = await ingestion.store_upload(file)
    resolved_type = _normalize_doc_type(doc_type, mime) if doc_type else guessed_type
    doc = await ingestion.create_document(
        db, patient_id, storage_path, mime, resolved_type, original_hash
    )
    await db.commit()

    job_id = new_id("job")
    state = jobs_store.new_job_state(job_id, doc.id)
    await jobs_store.save(state)

    background.add_task(run_pipeline, job_id, doc.id, patient_id)

    return DocumentUploadResponse(document_id=doc.id, job_id=job_id, status="queued")


@router.get("/patients/{patient_id}/documents", response_model=list[DocumentListItem])
async def list_patient_documents(
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
) -> list[DocumentListItem]:
    rows = (
        await db.execute(
            select(Document)
            .where(Document.patient_id == patient.id)
            .order_by(Document.uploaded_at.desc())
        )
    ).scalars().all()
    return [
        DocumentListItem(
            id=doc.id,
            patient_id=doc.patient_id,
            doc_type=doc.doc_type,
            mime=doc.mime,
            source=doc.source,
            status=doc.status,
            uploaded_at=doc.uploaded_at,
        )
        for doc in rows
    ]


@router.get("/documents/{document_id}", response_model=DocumentDTO)
async def get_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> DocumentDTO:
    doc = (
        await db.execute(select(Document).where(Document.id == document_id))
    ).scalar_one_or_none()
    if doc is None:
        raise not_found("Document", document_id)

    await _check_patient_access(doc.patient_id, db, auth_user_id)

    extraction = (
        await db.execute(
            select(Extraction)
            .where(Extraction.document_id == document_id)
            .order_by(Extraction.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    claims = ClaimsJSON.model_validate(extraction.raw_json) if extraction else None
    return DocumentDTO(
        id=doc.id,
        patient_id=doc.patient_id,
        doc_type=doc.doc_type,
        mime=doc.mime,
        source=doc.source,
        status=doc.status,
        uploaded_at=doc.uploaded_at,
        extraction=claims,
    )


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> dict:
    doc = (
        await db.execute(select(Document).where(Document.id == document_id))
    ).scalar_one_or_none()
    if doc is None:
        raise not_found("Document", document_id)

    await _check_patient_access(doc.patient_id, db, auth_user_id)

    removed = await retention.purge_document(db, doc)
    await db.commit()
    return {
        "document_id": doc.id,
        "status": doc.status,
        "raw_file_removed": removed,
        "claims_retained": True,
        "original_hash": doc.original_hash,
    }
