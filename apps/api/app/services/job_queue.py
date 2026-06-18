"""Redis-backed durable pipeline queue with duplicate-run guards."""
from __future__ import annotations

import json
import logging

from app import jobs_store
from app.config import settings

logger = logging.getLogger("setu.job_queue")

QUEUE_KEY = "setu:pipeline:queue"
_GUARD_PREFIX = "setu:pipeline:guard:"
_PROCESSING_PREFIX = "setu:pipeline:processing:"


def _guard_ttl() -> int:
    return settings.PIPELINE_TIMEOUT_SECONDS + 300


def _processing_ttl() -> int:
    return settings.PIPELINE_TIMEOUT_SECONDS + 120


async def schedule_pipeline(
    job_id: str,
    document_id: str,
    patient_id: str,
    *,
    reply_chat_id: str | None = None,
) -> bool:
    """Enqueue one pipeline job. Returns False if this document is already queued/running."""
    await jobs_store.save_document_job(document_id, job_id)

    try:
        redis = jobs_store._redis()
        guard_key = f"{_GUARD_PREFIX}{document_id}"
        acquired = await redis.set(guard_key, job_id, nx=True, ex=_guard_ttl())
        if not acquired:
            existing = await redis.get(guard_key)
            logger.info(
                "pipeline already scheduled for document %s (active job %s, skipped %s)",
                document_id,
                existing,
                job_id,
            )
            return False

        payload = json.dumps(
            {
                "job_id": job_id,
                "document_id": document_id,
                "patient_id": patient_id,
                "reply_chat_id": reply_chat_id,
            }
        )
        await redis.rpush(QUEUE_KEY, payload)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("queue enqueue failed: %s", exc)
        return False


async def enqueue_pipeline(
    job_id: str,
    document_id: str,
    patient_id: str,
    *,
    reply_chat_id: str | None = None,
) -> None:
    """Backward-compatible alias — always attempts schedule_pipeline."""
    await schedule_pipeline(job_id, document_id, patient_id, reply_chat_id=reply_chat_id)


async def dequeue_pipeline(timeout_seconds: int = 0) -> dict | None:
    """Pop one job, or None if the queue is empty.

    Connection/transport errors are NOT swallowed here — they propagate to the
    single caller (pipeline_worker_loop) so it can back off and throttle logging
    instead of emitting a warning on every poll when Redis is unreachable.
    """
    redis = jobs_store._redis()
    if timeout_seconds > 0 and hasattr(redis, "blpop"):
        result = await redis.blpop(QUEUE_KEY, timeout=timeout_seconds)
        if result:
            _, raw = result
            return json.loads(raw)
        return None
    raw = await redis.lpop(QUEUE_KEY)
    if raw:
        return json.loads(raw)
    return None


async def try_acquire_processing_lock(document_id: str, job_id: str) -> bool:
    try:
        redis = jobs_store._redis()
        key = f"{_PROCESSING_PREFIX}{document_id}"
        return bool(await redis.set(key, job_id, nx=True, ex=_processing_ttl()))
    except Exception as exc:  # noqa: BLE001
        logger.warning("processing lock failed: %s", exc)
        return True


async def release_processing_lock(document_id: str) -> None:
    try:
        await jobs_store._redis().delete(f"{_PROCESSING_PREFIX}{document_id}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("release processing lock failed: %s", exc)


async def release_pipeline_guard(document_id: str) -> None:
    try:
        await jobs_store._redis().delete(f"{_GUARD_PREFIX}{document_id}")
    except Exception as exc:  # noqa: BLE001
        logger.warning("release pipeline guard failed: %s", exc)
