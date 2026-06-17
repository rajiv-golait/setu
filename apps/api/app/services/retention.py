"""Document retention + purge (B7) — DPDP erasure + trust.

Decision (implemented, not redesigned): the raw uploaded image is TRANSIENT.
It is kept through a configurable retention window (RAW_RETENTION_DAYS, default
60) — or until the user deletes it — then the raw FILE is purged from storage.
The structured claims and a sha256 hash of the original are kept PERMANENTLY, so
the brief stays auditable to its source even after the image is gone.

What this gives us:
  - "verify against original" works during the care window (image still on disk)
  - DPDP erasure after the window (raw image removed; only derived data remains)
  - a "delete my data" path that purges all raw files for a patient

NO raw image is retained beyond the window. We never delete the claims here —
that is the durable medical record. Deleting the patient entirely is a separate,
explicit cascade.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Document
from app.services.storage import get_storage

logger = logging.getLogger("setu.retention")


def _remove_file(path: str | None) -> bool:
    if not path:
        return False
    return get_storage().delete(path)


async def purge_document(db: AsyncSession, doc: Document) -> bool:
    """Purge ONE document's raw file. Keeps the row, claims, and hash.

    Marks status=purged and stamps purged_at. Idempotent — re-purging a
    purged doc is a no-op. Returns True if a raw file was actually removed.
    """
    removed = _remove_file(doc.storage_path)
    if doc.status != "purged":
        doc.status = "purged"
        doc.purged_at = datetime.now(timezone.utc)
    await db.flush()
    return removed


async def purge_expired_documents(db: AsyncSession) -> int:
    """Purge raw files for all documents older than the retention window.

    This is the scheduled purge job (can be called on a cron/timer or lazily).
    Returns the number of documents purged.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.RAW_RETENTION_DAYS)
    rows = (
        await db.execute(
            select(Document).where(
                Document.uploaded_at < cutoff,
                Document.status != "purged",
            )
        )
    ).scalars().all()
    count = 0
    for doc in rows:
        await purge_document(db, doc)
        count += 1
    if count:
        await db.commit()
        logger.info("purged %d expired raw documents (retention=%dd)", count, settings.RAW_RETENTION_DAYS)
    return count


async def delete_patient_data(db: AsyncSession, patient_id: str) -> dict:
    """'Delete my data' cascade: purge ALL raw files for a patient.

    Removes every raw image for the patient and marks the documents purged.
    Claims/brief/hash are retained as the medical record (the raw images are
    the erasable artifact). Returns a small summary for the caller.
    """
    rows = (
        await db.execute(select(Document).where(Document.patient_id == patient_id))
    ).scalars().all()
    purged_files = 0
    for doc in rows:
        if await purge_document(db, doc):
            purged_files += 1
    await db.commit()
    return {"patient_id": patient_id, "documents": len(rows), "raw_files_purged": purged_files}
