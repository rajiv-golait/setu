"""Shared document upload: hash dedup, job creation, queue-only pipeline scheduling."""
from __future__ import annotations

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import jobs_store
from app.db.models import Document
from app.ids import new_id
from app.schemas.common import DocumentUploadResponse
from app.schemas.jobs import STAGES
from app.services import ingestion
from app.services.job_queue import schedule_pipeline


async def find_document_by_hash(
    db: AsyncSession, patient_id: str, original_hash: str
) -> Document | None:
    return (
        await db.execute(
            select(Document)
            .where(
                Document.patient_id == patient_id,
                Document.original_hash == original_hash,
                Document.status != "purged",
            )
            .order_by(Document.uploaded_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()


async def _job_for_existing_document(db: AsyncSession, doc: Document) -> DocumentUploadResponse:
    """Return the best job view for a duplicate upload (no new row, no re-queue)."""
    job_id = await jobs_store.load_document_job(doc.id)
    if job_id:
        state = await jobs_store.load(job_id)
        if state:
            if state.status in ("queued", "running", "completed", "failed"):
                return DocumentUploadResponse(
                    document_id=doc.id,
                    job_id=job_id,
                    status=state.status,
                    duplicate=True,
                )

    if doc.status in ("extracted", "completed"):
        job_id = new_id("job")
        state = jobs_store.new_job_state(job_id, doc.id, doc.patient_id)
        state.status = "completed"
        state.completed_stages = list(STAGES)
        state.progress = 1.0
        state.result = {"document_id": doc.id, "duplicate": True}
        await jobs_store.save(state)
        await jobs_store.save_document_job(doc.id, job_id)
        return DocumentUploadResponse(
            document_id=doc.id,
            job_id=job_id,
            status="completed",
            duplicate=True,
        )

    job_id = new_id("job")
    state = jobs_store.new_job_state(job_id, doc.id, doc.patient_id)
    await jobs_store.save(state)
    from app.services.job_queue import release_pipeline_guard, schedule_pipeline

    await release_pipeline_guard(doc.id)
    await schedule_pipeline(job_id, doc.id, doc.patient_id)
    return DocumentUploadResponse(
        document_id=doc.id,
        job_id=job_id,
        status="queued",
        duplicate=True,
    )


async def upload_document_for_patient(
    db: AsyncSession,
    patient_id: str,
    file: UploadFile,
    resolved_doc_type: str | None,
    *,
    reply_chat_id: str | None = None,
) -> DocumentUploadResponse:
    await ingestion.require_consent(db, patient_id)

    data, mime = await ingestion.read_upload(file)
    original_hash = ingestion.sha256_hex(data)

    existing = await find_document_by_hash(db, patient_id, original_hash)
    if existing is not None:
        return await _job_for_existing_document(db, existing)

    storage_path, mime, guessed_type, _, enc_key = ingestion.store_bytes(data, mime)
    doc_type = resolved_doc_type or guessed_type
    doc = await ingestion.create_document(
        db, patient_id, storage_path, mime, doc_type, original_hash, enc_key
    )
    await db.flush()

    job_id = new_id("job")
    state = jobs_store.new_job_state(job_id, doc.id, patient_id)
    await jobs_store.save(state)
    await schedule_pipeline(job_id, doc.id, patient_id, reply_chat_id=reply_chat_id)

    return DocumentUploadResponse(
        document_id=doc.id,
        job_id=job_id,
        status="queued",
        duplicate=False,
    )
