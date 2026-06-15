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


# --- Explanation cache (keyed by document_id) ----------------------------- #
# The caregiver explanation is free text, not a DB artifact; like job state it
# lives in Redis (expl:{document_id}, 24h TTL) so the web-chat polling endpoint
# can fetch it after the pipeline completes — no new table / migration.
def _expl_key(document_id: str) -> str:
    return f"expl:{document_id}"


async def save_explanation(document_id: str, explanation: str, confidence: float) -> None:
    payload = json.dumps({"explanation": explanation, "confidence": confidence})
    await _redis().set(_expl_key(document_id), payload, ex=_TTL)


async def load_explanation(document_id: str) -> dict | None:
    raw = await _redis().get(_expl_key(document_id))
    if raw is None:
        return None
    return json.loads(raw)


# --- DEMO_MODE Path B: a synthetic "demo_job" that advances through stages -- #
# On the first poll we record a start timestamp; each subsequent poll computes
# how many stages should be complete (one every DEMO_STAGE_SECONDS). No real
# pipeline runs — this is the offline web-chat fallback for the live demo.
DEMO_JOB_ID = "demo_job"
DEMO_STAGE_SECONDS = 2.0
_DEMO_START_KEY = "demo_job:start"


async def demo_job_state(seeded_explanation: str) -> JobStatusDTO:
    """Synthesize the demo job's status, advancing one stage per poll-interval."""
    import time

    r = _redis()
    raw_start = await r.get(_DEMO_START_KEY)
    try:
        start = float(raw_start) if raw_start else None
    except (TypeError, ValueError):
        start = None
    if start is None:
        start = time.time()
        await r.set(_DEMO_START_KEY, str(start), ex=_TTL)

    elapsed = time.time() - start
    n_done = min(len(STAGES), int(elapsed // DEMO_STAGE_SECONDS))
    completed = STAGES[:n_done]
    done = n_done >= len(STAGES)

    state = new_job_state(DEMO_JOB_ID, document_id="demo_doc")
    state.completed_stages = completed
    state.progress = round(n_done / len(STAGES), 2)
    if done:
        state.status = "completed"
        state.stage = None
        state.progress = 1.0
        state.result = {"explanation": seeded_explanation, "share_token": None}
    else:
        state.status = "running"
        state.stage = STAGES[n_done] if n_done < len(STAGES) else None
    return state


async def reset_demo_job() -> None:
    await _redis().set(_DEMO_START_KEY, "", ex=1)
