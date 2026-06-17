"""Notification preferences and outbox processing."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import InAppNotification, NotificationPreference
from app.db.session import get_db
from app.deps import require_admin, require_auth_user_id
from app.ids import new_id
from app.services import notifications as notify

router = APIRouter(prefix="/notifications", tags=["notifications"])


class PreferenceDTO(BaseModel):
    channel: str
    enabled: bool


class PreferenceUpdate(BaseModel):
    channel: str
    enabled: bool


class InAppNotificationDTO(BaseModel):
    id: str
    title: str
    body: str
    data: dict | None
    status: str
    created_at: datetime


@router.get("", response_model=list[InAppNotificationDTO])
async def list_notifications(
    limit: int = Query(default=20, le=50),
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[InAppNotificationDTO]:
    rows = (
        await db.execute(
            select(InAppNotification)
            .where(InAppNotification.user_id == auth_user_id)
            .order_by(InAppNotification.created_at.desc())
            .limit(limit)
        )
    ).scalars().all()
    return [
        InAppNotificationDTO(
            id=r.id,
            title=r.title,
            body=r.body,
            data=r.data,
            status=r.status,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.get("/unread-count")
async def unread_count(
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    count = (
        await db.execute(
            select(func.count())
            .select_from(InAppNotification)
            .where(
                InAppNotification.user_id == auth_user_id,
                InAppNotification.status == "pending",
            )
        )
    ).scalar_one()
    return {"count": count}


@router.patch("/{notification_id}/read")
async def mark_read(
    notification_id: str,
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> dict:
    from app.errors import not_found

    row = (
        await db.execute(
            select(InAppNotification).where(
                InAppNotification.id == notification_id,
                InAppNotification.user_id == auth_user_id,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise not_found("Notification", notification_id)
    row.status = "read"
    row.read_at = datetime.now(timezone.utc)
    await db.commit()
    return {"id": notification_id, "status": "read"}


@router.get("/preferences", response_model=list[PreferenceDTO])
async def list_preferences(
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> list[PreferenceDTO]:
    rows = (
        await db.execute(
            select(NotificationPreference).where(NotificationPreference.user_id == auth_user_id)
        )
    ).scalars().all()
    return [PreferenceDTO(channel=r.channel, enabled=r.enabled) for r in rows]


@router.put("/preferences", response_model=PreferenceDTO)
async def upsert_preference(
    body: PreferenceUpdate,
    auth_user_id: str = Depends(require_auth_user_id),
    db: AsyncSession = Depends(get_db),
) -> PreferenceDTO:
    row = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == auth_user_id,
                NotificationPreference.channel == body.channel,
            )
        )
    ).scalar_one_or_none()
    if row is None:
        row = NotificationPreference(
            id=new_id("npref"),
            user_id=auth_user_id,
            channel=body.channel,
            enabled=body.enabled,
        )
        db.add(row)
    else:
        row.enabled = body.enabled
    await db.commit()
    return PreferenceDTO(channel=body.channel, enabled=body.enabled)


@router.post("/process-outbox")
async def process_outbox(
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    sent = await notify.process_outbox(db)
    return {"sent": sent}
