"""Job status polling and retry. Job state lives in Redis only."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks

from app import jobs_store
from app.config import settings
from app.errors import VALIDATION_ERROR, AppError, not_found
from app.schemas.jobs import JobStatusDTO

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusDTO)
async def get_job(job_id: str) -> JobStatusDTO:
    state = await jobs_store.load(job_id)
    if state is None:
        raise not_found("Job", job_id)

    # Stale-job detection: if running too long, surface a failed view so the
    # frontend can show the retry button. We don't mutate Redis — the background
    # task may still complete and will overwrite the state when it does.
    if (
        state.status == "running"
        and state.started_at is not None
        and (datetime.now(timezone.utc) - state.started_at).total_seconds()
        > settings.PIPELINE_TIMEOUT_SECONDS + 30
    ):
        state.status = "failed"
        state.error = {
            "code": "PIPELINE_TIMEOUT",
            "message": "Processing timed out — please try again",
            "details": {"stage": state.stage},
            "retryable": True,
        }
    return state


@router.post("/{job_id}/retry", response_model=JobStatusDTO)
async def retry_job(job_id: str, background: BackgroundTasks) -> JobStatusDTO:
    """Re-enqueue a failed job without re-uploading the document."""
    state = await jobs_store.load(job_id)
    if state is None:
        raise not_found("Job", job_id)
    if state.status != "failed":
        raise AppError(VALIDATION_ERROR, "Only failed jobs can be retried", retryable=False)
    if not state.document_id:
        raise AppError(VALIDATION_ERROR, "Job has no associated document", retryable=False)

    new_state = jobs_store.new_job_state(job_id, state.document_id, state.patient_id)
    await jobs_store.save(new_state)

    from app.services.orchestrator import run_pipeline
    background.add_task(run_pipeline, job_id, state.document_id, state.patient_id or "")

    return new_state
