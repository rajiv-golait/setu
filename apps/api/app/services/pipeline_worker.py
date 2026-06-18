"""Background pipeline worker — drains the Redis queue with bounded concurrency.

Upload handlers enqueue work only; this loop is the single execution path so
pipelines are not started twice (no BackgroundTasks + queue double-run).
"""
from __future__ import annotations

import asyncio
import logging

from app.config import settings
from app.services.job_queue import (
    dequeue_pipeline,
    release_pipeline_guard,
    release_processing_lock,
    try_acquire_processing_lock,
)
from app.services.orchestrator import run_pipeline

logger = logging.getLogger("setu.pipeline_worker")

_semaphore: asyncio.Semaphore | None = None


def _concurrency_semaphore() -> asyncio.Semaphore:
    global _semaphore
    if _semaphore is None:
        n = max(1, settings.PIPELINE_WORKER_CONCURRENCY)
        _semaphore = asyncio.Semaphore(n)
    return _semaphore


async def _run_one(payload: dict) -> None:
    job_id = payload["job_id"]
    document_id = payload["document_id"]
    patient_id = payload["patient_id"]
    reply_chat_id = payload.get("reply_chat_id")

    if not await try_acquire_processing_lock(document_id, job_id):
        logger.info(
            "document %s already processing — skipping duplicate job %s",
            document_id,
            job_id,
        )
        await release_pipeline_guard(document_id)
        return

    try:
        async with _concurrency_semaphore():
            await run_pipeline(job_id, document_id, patient_id, reply_chat_id)
    finally:
        await release_processing_lock(document_id)
        await release_pipeline_guard(document_id)


async def pipeline_worker_loop() -> None:
    logger.info(
        "pipeline worker started (concurrency=%s)",
        settings.PIPELINE_WORKER_CONCURRENCY,
    )
    failures = 0
    backoff = 1.0
    while True:
        try:
            payload = await dequeue_pipeline(timeout_seconds=5)
            if failures:
                logger.info("pipeline queue reachable again after %s failed attempt(s)", failures)
                failures = 0
                backoff = 1.0
            if payload is None:
                await asyncio.sleep(0.25)
                continue
            asyncio.create_task(_run_one(payload))
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001
            failures += 1
            # Redis being down (e.g. not running in local dev) would otherwise log on
            # every poll. Warn on the first failure with an actionable hint, then stay
            # quiet and back off exponentially until it recovers.
            if failures == 1:
                logger.warning(
                    "pipeline queue unavailable: %s — uploads will not process until "
                    "Redis is reachable at %s. Start Redis, or ignore if intentional.",
                    exc,
                    settings.REDIS_URL,
                )
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30.0)
