"""Ingestion: validate upload, store file to disk, create document + job rows.

Storage is a local volume (STORAGE_PATH). S3 is intentionally out of scope for MVP.
"""
from __future__ import annotations

import os

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Document
from app.errors import VALIDATION_ERROR, AppError
from app.ids import new_id

_ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp", "application/pdf"}
_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
}


def _guess_doc_type(mime: str) -> str:
    return "lab_report" if mime == "application/pdf" else "prescription"


async def store_upload(file: UploadFile) -> tuple[str, str, str]:
    """Validate + persist the uploaded file. Returns (storage_path, mime, doc_type)."""
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

    os.makedirs(settings.STORAGE_PATH, exist_ok=True)
    doc_id = new_id("doc")
    path = os.path.join(settings.STORAGE_PATH, f"{doc_id}{_EXT.get(mime, '')}")
    with open(path, "wb") as f:
        f.write(data)
    return path, mime, _guess_doc_type(mime)


async def create_document(
    db: AsyncSession, patient_id: str, storage_path: str, mime: str, doc_type: str
) -> Document:
    doc = Document(
        id=storage_path_to_id(storage_path),
        patient_id=patient_id,
        doc_type=doc_type,
        storage_path=storage_path,
        mime=mime,
        source="upload",
        status="pending",
    )
    db.add(doc)
    await db.flush()
    return doc


def storage_path_to_id(storage_path: str) -> str:
    """The document id is the filename stem chosen in store_upload."""
    base = os.path.basename(storage_path)
    return os.path.splitext(base)[0]
