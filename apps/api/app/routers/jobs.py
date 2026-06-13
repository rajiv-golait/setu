"""Job status polling. Job state lives in Redis only."""
from __future__ import annotations

from fastapi import APIRouter

from app import jobs_store
from app.errors import not_found
from app.schemas.jobs import JobStatusDTO

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusDTO)
async def get_job(job_id: str) -> JobStatusDTO:
    state = await jobs_store.load(job_id)
    if state is None:
        raise not_found("Job", job_id)
    return state
