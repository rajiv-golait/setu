"""Web Push VAPID key distribution and subscription management."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import PushSubscription
from app.deps import get_auth_user_id, get_db
from app.ids import new_id

router = APIRouter(prefix="/push", tags=["push"])


class SubscribeRequest(BaseModel):
    endpoint: str
    p256dh: str
    auth: str


class UnsubscribeRequest(BaseModel):
    endpoint: str


@router.get("/vapid-key")
async def get_vapid_key() -> dict:
    if not settings.VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=503, detail="Push not configured")
    return {"public_key": settings.VAPID_PUBLIC_KEY}


@router.post("/subscribe", status_code=201)
async def subscribe(
    body: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Depends(get_auth_user_id),
) -> dict:
    if not user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    # Upsert: delete stale row for this endpoint if it exists under a different user.
    await db.execute(
        delete(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )
    sub = PushSubscription(
        id=new_id("ps"),
        user_id=user_id,
        endpoint=body.endpoint,
        p256dh=body.p256dh,
        auth=body.auth,
    )
    db.add(sub)
    await db.commit()
    return {"ok": True}


@router.delete("/subscribe")
async def unsubscribe(
    body: UnsubscribeRequest,
    db: AsyncSession = Depends(get_db),
    user_id: str | None = Depends(get_auth_user_id),
) -> dict:
    await db.execute(
        delete(PushSubscription).where(
            PushSubscription.endpoint == body.endpoint,
            PushSubscription.user_id == user_id,
        )
    )
    await db.commit()
    return {"ok": True}
