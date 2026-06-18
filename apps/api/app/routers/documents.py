"""Document upload + retrieval. Upload enqueues pipeline work for the background worker."""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Document, Extraction, Patient
from app.db.session import get_db
from app.deps import _check_patient_access, get_auth_user_id, get_user_role, require_patient_access
from app.errors import VALIDATION_ERROR, AppError, not_found
from app.ids import new_id
from app.schemas.claims import ClaimsJSON
from app.schemas.common import (
    BatchUploadResponse,
    DocumentDTO,
    DocumentListItem,
    DocumentUploadResponse,
)
from app.services import retention
from app.services.audit_phi import audit_phi_read
from app.services.document_upload import upload_document_for_patient

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
    file: UploadFile = File(...),
    patient_id: str = Form(...),
    doc_type: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> DocumentUploadResponse:
    await _check_patient_access(patient_id, db, auth_user_id)
    mime = file.content_type or "application/octet-stream"
    resolved_type = _normalize_doc_type(doc_type, mime) if doc_type else None
    result = await upload_document_for_patient(db, patient_id, file, resolved_type)
    await db.commit()
    return result


@router.post("/documents/batch", response_model=BatchUploadResponse, status_code=202)
async def upload_documents_batch(
    files: list[UploadFile] = File(...),
    patient_id: str = Form(...),
    doc_type: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> BatchUploadResponse:
    await _check_patient_access(patient_id, db, auth_user_id)
    if not files:
        raise AppError(VALIDATION_ERROR, "At least one file is required", retryable=False)
    if len(files) > settings.MAX_BATCH_UPLOAD_FILES:
        raise AppError(
            VALIDATION_ERROR,
            f"Maximum {settings.MAX_BATCH_UPLOAD_FILES} files per batch",
            retryable=False,
        )

    batch_id = new_id("batch")
    items: list[DocumentUploadResponse] = []
    for upload in files:
        mime = upload.content_type or "application/octet-stream"
        resolved_type = _normalize_doc_type(doc_type, mime) if doc_type else None
        items.append(await upload_document_for_patient(db, patient_id, upload, resolved_type))
    await db.commit()
    return BatchUploadResponse(batch_id=batch_id, items=items)


@router.get("/patients/{patient_id}/documents", response_model=list[DocumentListItem])
async def list_patient_documents(
    request: Request,
    patient: Patient = Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
    role: str = Depends(get_user_role),
) -> list[DocumentListItem]:
    await audit_phi_read(
        db,
        patient_id=patient.id,
        resource="documents",
        actor_id=auth_user_id,
        actor_role=role,
        request=request,
    )
    rows = (
        await db.execute(
            select(Document)
            .where(Document.patient_id == patient.id)
            .order_by(Document.uploaded_at.desc())
        )
    ).scalars().all()
    items = [
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
    await db.commit()
    return items


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
