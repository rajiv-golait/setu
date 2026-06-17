"""PHI access audit helpers — log every read of patient health data."""
from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.audit import log_access


async def audit_phi_read(
    db: AsyncSession,
    *,
    patient_id: str,
    resource: str,
    actor_id: str | None,
    actor_role: str,
    request: Request | None = None,
) -> None:
    await log_access(
        db,
        actor_id=actor_id,
        actor_role=actor_role,
        patient_id=patient_id,
        resource=resource,
        action="read",
        request=request,
    )


def phi_resource(resource: str) -> Callable:
    """Decorator for route handlers that have patient, db, request in kwargs."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = await fn(*args, **kwargs)
            patient = kwargs.get("patient")
            db: AsyncSession | None = kwargs.get("db")
            request: Request | None = kwargs.get("request")
            auth_user_id = kwargs.get("auth_user_id")
            role = kwargs.get("role", "patient")
            if patient is not None and db is not None:
                await audit_phi_read(
                    db,
                    patient_id=patient.id,
                    resource=resource,
                    actor_id=auth_user_id,
                    actor_role=role if auth_user_id else "system",
                    request=request,
                )
                await db.commit()
            return result

        return wrapper

    return decorator
