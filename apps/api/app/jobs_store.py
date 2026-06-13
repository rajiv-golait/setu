"""Redis-backed job state. Job state lives ONLY here (never in Postgres).

Key: job:{job_id}    TTL: 24h
"""
from __future__ import annotations

import json

import redis.asyncio as redis

from app.config import settings
from app.schemas.jobs import STAGES, JobStatusDTO

_TTL = 86400  # 24h
_client: redis.Redis | None = None


def _redis() -> redis.Redis:
    global _client
    if _client is None:
        _client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _client


def _key(job_id: str) -> str:
    return f"job:{job_id}"


def new_job_state(job_id: str, document_id: str) -> JobStatusDTO:
    return JobStatusDTO(
        job_id=job_id,
        status="queued",
        stage=None,
        stages=list(STAGES),
        completed_stages=[],
        progress=0.0,
        failed_at=None,
        error=None,
        document_id=document_id,
        result={},
    )


async def save(state: JobStatusDTO) -> None:
    await _redis().set(_key(state.job_id), state.model_dump_json(), ex=_TTL)


async def load(job_id: str) -> JobStatusDTO | None:
    raw = await _redis().get(_key(job_id))
    if raw is None:
        return None
    return JobStatusDTO.model_validate(json.loads(raw))
