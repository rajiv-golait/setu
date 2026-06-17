"""Access audit logging — DPDP who-viewed-my-data trail."""
from __future__ import annotations

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AccessLog
from app.ids import new_id


def _client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    if request.client is not None:
        return request.client.host
    return None


async def log_access(
    db: AsyncSession,
    *,
    actor_id: str | None,
    actor_role: str,
    patient_id: str,
    resource: str,
    action: str,
    request: Request | None = None,
) -> AccessLog:
    row = AccessLog(
        id=new_id("log"),
        actor_id=actor_id,
        actor_role=actor_role,
        patient_id=patient_id,
        resource=resource,
        action=action,
        ip=_client_ip(request),
    )
    db.add(row)
    await db.flush()
    return row
