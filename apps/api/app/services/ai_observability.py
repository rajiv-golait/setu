"""AI request observability logging."""
from __future__ import annotations

import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AiRequestLog
from app.ids import new_id


@asynccontextmanager
async def track_ai_request(
    db: AsyncSession,
    *,
    request_type: str,
    provider_name: str | None = None,
    patient_id: str | None = None,
) -> AsyncIterator[Callable[[bool, bool], None]]:
    started = time.perf_counter()

    def finish(success: bool, fallback_used: bool = False) -> None:
        latency = int((time.perf_counter() - started) * 1000)
        row = AiRequestLog(
            id=new_id("ail"),
            request_type=request_type,
            provider_name=provider_name,
            patient_id=patient_id,
            latency_ms=latency,
            success=success,
            fallback_used=fallback_used,
        )
        db.add(row)

    yield finish
