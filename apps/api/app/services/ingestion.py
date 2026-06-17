"""Ingestion: validate upload, store via pluggable backend, create document row."""
from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Document
from app.errors import CONSENT_REQUIRED, VALIDATION_ERROR, AppError
from app.ids import new_id
from app.services.storage import get_storage

_CONSENT_PURPOSE = "document_processing"

_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


def _guess_doc_type(mime: str) -> str:
    return "lab_report" if mime == "application/pdf" else "prescription"


async def require_consent(db: AsyncSession, patient_id: str) -> None:
    """Reject document processing unless DPDP consent is on record (DPDP gateway).

    DEMO_MODE bypasses the gate — the seeded demo path never runs the real
    pipeline and must work with zero setup. Imported here (not at module top) to
    avoid a circular import with persistence.
    """
    if settings.DEMO_MODE:
        return
    from app.services import persistence

    if not await persistence.has_consent(db, patient_id, _CONSENT_PURPOSE):
        raise AppError(
            CONSENT_REQUIRED,
            "Consent is required before processing documents.",
            details={"patient_id": patient_id, "purpose": _CONSENT_PURPOSE},
            retryable=False,
        )


async def store_upload(file: UploadFile) -> tuple[str, str, str, str, str | None]:
    """Validate + persist the uploaded file.

    Returns (storage_path, mime, doc_type, original_hash). The hash is a
    permanent sha256 of the raw bytes so claims stay auditable to the source
    even after the raw image is purged (retention/erasure).
    """
    mime = file.content_type or "application/octet-stream"
    if mime not in _ALLOWED_MIME:
        raise AppError(VALIDATION_ERROR, f"Unsupported file type: {mime}", details={"mime": mime})

    data = await file.read()
    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    if len(data) > max_bytes:
        raise AppError(
            VALIDATION_ERROR,
            f"File exceeds {settings.MAX_UPLOAD_MB}MB limit",
            details={"size": len(data)},
        )

    original_hash = hashlib.sha256(data).hexdigest()
    doc_id = new_id("doc")
    storage = get_storage()
    path, key_id = storage.put(data, mime=mime, doc_id=doc_id)
    return path, mime, _guess_doc_type(mime), original_hash, key_id


async def create_document(
    db: AsyncSession,
    patient_id: str,
    storage_path: str,
    mime: str,
    doc_type: str,
    original_hash: str | None = None,
    encryption_key_id: str | None = None,
) -> Document:
    doc = Document(
        id=storage_path_to_id(storage_path),
        patient_id=patient_id,
        doc_type=doc_type,
        storage_path=storage_path,
        encryption_key_id=encryption_key_id,
        mime=mime,
        source="upload",
        status="pending",
        original_hash=original_hash,
    )
    db.add(doc)
    await db.flush()
    return doc


def storage_path_to_id(storage_path: str) -> str:
    """The document id is the filename stem chosen in store_upload."""
    base = Path(storage_path).name
    return Path(base).stem
