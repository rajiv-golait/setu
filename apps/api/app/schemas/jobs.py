"""Job status DTO. Job state lives in Redis only."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel

JobStatus = Literal["queued", "running", "completed", "failed"]

# Canonical pipeline stage order.
STAGES: list[str] = ["extraction", "validation", "memory", "brief", "summary", "share"]


class JobStatusDTO(BaseModel):
    job_id: str
    status: JobStatus
    stage: str | None = None
    stages: list[str] = STAGES
    completed_stages: list[str] = []
    progress: float = 0.0
    failed_at: str | None = None
    error: dict[str, Any] | None = None
    document_id: str | None = None
    result: dict[str, Any] = {}
