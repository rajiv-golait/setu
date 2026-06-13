"""Document upload + retrieval. Upload starts the pipeline via BackgroundTasks."""
from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import jobs_store
from app.db.models import Document, Extraction, Patient
from app.db.session import get_db
from app.errors import not_found
from app.ids import new_id
from app.schemas.claims import ClaimsJSON
from app.schemas.common import DocumentDTO, DocumentUploadResponse
from app.services import ingestion
from app.services.orchestrator import run_pipeline

router = APIRouter(tags=["documents"])


@router.post("/documents", response_model=DocumentUploadResponse, status_code=202)
async def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient is None:
        raise not_found("Patient", patient_id)

    storage_path, mime, doc_type = await ingestion.store_upload(file)
    doc = await ingestion.create_document(db, patient_id, storage_path, mime, doc_type)
    await db.commit()

    job_id = new_id("job")
    state = jobs_store.new_job_state(job_id, doc.id)
    await jobs_store.save(state)

    # Kick the pipeline AFTER the response is sent.
    background.add_task(run_pipeline, job_id, doc.id, patient_id)

    return DocumentUploadResponse(document_id=doc.id, job_id=job_id, status="queued")


@router.get("/documents/{document_id}", response_model=DocumentDTO)
async def get_document(document_id: str, db: AsyncSession = Depends(get_db)) -> DocumentDTO:
    doc = (
        await db.execute(select(Document).where(Document.id == document_id))
    ).scalar_one_or_none()
    if doc is None:
        raise not_found("Document", document_id)

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
