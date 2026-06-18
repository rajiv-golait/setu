"""Job status polling and retry. Job state lives in Redis only."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import jobs_store
from app.config import settings
from app.db.models import Patient
from app.db.session import get_db
from app.deps import get_auth_user_id
from app.errors import FORBIDDEN, UNAUTHORIZED, VALIDATION_ERROR, AppError, not_found
from app.schemas.jobs import JobStatusDTO

router = APIRouter(prefix="/jobs", tags=["jobs"])


async def _assert_job_owner(
    state: JobStatusDTO,
    auth_user_id: str | None,
    db: AsyncSession,
) -> None:
    """When Supabase auth is on, verify the caller owns the job's patient record."""
    if not settings.SUPABASE_ENABLED:
        return
    if auth_user_id is None:
        raise AppError(UNAUTHORIZED, "Authentication required", retryable=False)
    if not state.patient_id:
        # Job has no patient association — allow (e.g. legacy jobs).
        return
    patient = (
        await db.execute(
            select(Patient).where(Patient.id == state.patient_id)
        )
    ).scalar_one_or_none()
    if patient is None or patient.supabase_user_id != auth_user_id:
        raise AppError(FORBIDDEN, "You do not have access to this job", retryable=False)


@router.get("/{job_id}", response_model=JobStatusDTO)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> JobStatusDTO:
    state = await jobs_store.load(job_id)
    if state is None:
        raise not_found("Job", job_id)

    await _assert_job_owner(state, auth_user_id, db)

    # Stale-job detection: surface a failed view so the frontend can show retry.
    if (
        state.status == "running"
        and state.started_at is not None
        and (datetime.now(timezone.utc) - state.started_at).total_seconds()
        > settings.PIPELINE_TIMEOUT_SECONDS + 30
    ):
        state.status = "failed"
        state.failed_at = state.stage
        state.error = {
            "code": "PIPELINE_TIMEOUT",
            "message": "Processing timed out — please try again",
            "details": {"stage": state.stage},
            "retryable": True,
        }
    return state


@router.post("/{job_id}/retry", response_model=JobStatusDTO)
async def retry_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    auth_user_id: str | None = Depends(get_auth_user_id),
) -> JobStatusDTO:
    """Re-enqueue a failed job without re-uploading the document."""
    state = await jobs_store.load(job_id)
    if state is None:
        raise not_found("Job", job_id)

    await _assert_job_owner(state, auth_user_id, db)

    if state.status != "failed":
        raise AppError(VALIDATION_ERROR, "Only failed jobs can be retried", retryable=False)
    if not state.document_id:
        raise AppError(VALIDATION_ERROR, "Job has no associated document", retryable=False)

    new_state = jobs_store.new_job_state(job_id, state.document_id, state.patient_id)
    await jobs_store.save(new_state)

    from app.services.job_queue import release_pipeline_guard, schedule_pipeline

    await release_pipeline_guard(state.document_id)
    await schedule_pipeline(job_id, state.document_id, state.patient_id or "")

    return new_state
