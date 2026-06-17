"""Redis-backed durable job enqueue (optional upgrade from BackgroundTasks)."""
from __future__ import annotations

import json
import logging

from app import jobs_store
from app.config import settings

logger = logging.getLogger("setu.job_queue")

QUEUE_KEY = "setu:pipeline:queue"


async def enqueue_pipeline(job_id: str, document_id: str, patient_id: str) -> None:
    """Push pipeline job to Redis list for worker consumption."""
    try:
        redis = jobs_store._redis()
        payload = json.dumps(
            {"job_id": job_id, "document_id": document_id, "patient_id": patient_id}
        )
        await redis.rpush(QUEUE_KEY, payload)
    except Exception as exc:  # noqa: BLE001
        logger.warning("queue enqueue failed, caller should use BackgroundTasks: %s", exc)


async def dequeue_pipeline() -> dict | None:
    try:
        redis = jobs_store._redis()
        raw = await redis.lpop(QUEUE_KEY)
        if raw:
            return json.loads(raw)
    except Exception as exc:  # noqa: BLE001
        logger.warning("queue dequeue failed: %s", exc)
    return None
