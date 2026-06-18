"""Web-chat fallback API. Mirrors the Telegram bot for the Next.js web-chat UI.
Mounted under /api/v1.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import jobs_store
from app.config import settings
from app.db.models import Patient
from app.db.session import get_db
from app.errors import not_found
from app.ids import new_id
from app.schemas.jobs import JobStatusDTO
from app.services.document_upload import upload_document_for_patient

router = APIRouter(prefix="/webchat", tags=["webchat"])

_SUMMARY_WORDS = {"summary", "सारांश"}


@router.post("/message")
async def webchat_message(
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    patient_id: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if file is not None:
        pid = patient_id or await _ensure_anon_patient(db)
        result = await upload_document_for_patient(db, pid, file, None)
        await db.commit()
        return {
            "job_id": result.job_id,
            "status": "processing",
            "message": "वाचत आहे...",
            "duplicate": result.duplicate,
        }

    if (text or "").strip().lower() in _SUMMARY_WORDS:
        token = await _brief_token(db, patient_id)
        if token is None:
            return {"type": "text", "message": "अजून कोणताही रिपोर्ट नाही. एक फोटो पाठवा."}
        return {"type": "link", "url": f"{settings.BRIEF_BASE_URL.rstrip('/')}/brief/{token}"}

    return {"type": "text", "message": "फोटो पाठवा किंवा 'summary' लिहा."}


@router.get("/job/{job_id}", response_model=JobStatusDTO)
async def webchat_job(job_id: str) -> JobStatusDTO:
    state = await jobs_store.load(job_id)
    if state is None:
        raise not_found("Job", job_id)
    return state


@router.get("/explanation/{document_id}")
async def webchat_explanation(document_id: str) -> dict:
    cached = await jobs_store.load_explanation(document_id)
    if cached is None:
        raise not_found("Explanation", document_id)
    return cached


async def _ensure_anon_patient(db: AsyncSession) -> str:
    """Create a throwaway patient for an anonymous web-chat upload."""
    from app.ids import new_token

    pid = new_id("pat")
    db.add(Patient(id=pid, display_name=None, lang_pref="mr", patient_token=new_token(10)))
    await db.flush()
    return pid


async def _brief_token(db: AsyncSession, patient_id: str | None) -> str | None:
    if not patient_id:
        return None
    from app.db.models import Share

    share = (
        await db.execute(
            select(Share)
            .where(Share.patient_id == patient_id)
            .order_by(Share.created_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()
    return share.token if share else None
