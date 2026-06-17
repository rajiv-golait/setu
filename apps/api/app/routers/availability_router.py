"""Availability and slot routes."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import require_approved_provider, require_provider
from app.db.models import Provider
from app.services import scheduling as sched

router = APIRouter(prefix="/providers", tags=["scheduling"])


class AvailabilityRule(BaseModel):
    day_of_week: int
    start_time: str
    end_time: str
    slot_minutes: int = 30
    timezone: str = "Asia/Kolkata"


class AvailabilitySetRequest(BaseModel):
    rules: list[AvailabilityRule]


class SlotDTO(BaseModel):
    id: str
    provider_id: str
    starts_at: datetime
    ends_at: datetime
    status: str


@router.get("/{provider_id}/slots", response_model=list[SlotDTO])
async def list_provider_slots(
    provider_id: str,
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    db: AsyncSession = Depends(get_db),
) -> list[SlotDTO]:
    now = datetime.now(timezone.utc)
    start = from_dt or now
    end = to_dt or (now + timedelta(days=14))
    await sched.generate_slots(
        db,
        provider_id,
        from_date=start.date(),
        to_date=end.date(),
    )
    await db.commit()
    rows = await sched.list_open_slots(db, provider_id, from_dt=start, to_dt=end)
    return [
        SlotDTO(
            id=s.id,
            provider_id=s.provider_id,
            starts_at=s.starts_at,
            ends_at=s.ends_at,
            status=s.status,
        )
        for s in rows
    ]


@router.put("/me/availability", response_model=list[AvailabilityRule])
async def set_my_availability(
    body: AvailabilitySetRequest,
    provider: Provider = Depends(require_approved_provider),
    db: AsyncSession = Depends(get_db),
) -> list[AvailabilityRule]:
    rules = [r.model_dump() for r in body.rules]
    await sched.set_availability(db, provider.id, rules)
    await db.commit()
    return body.rules


@router.get("/me/availability", response_model=list[AvailabilityRule])
async def get_my_availability(
    provider: Provider = Depends(require_provider),
    db: AsyncSession = Depends(get_db),
) -> list[AvailabilityRule]:
    rows = await sched.list_availability(db, provider.id)
    return [
        AvailabilityRule(
            day_of_week=r.day_of_week,
            start_time=r.start_time,
            end_time=r.end_time,
            slot_minutes=r.slot_minutes,
            timezone=r.timezone,
        )
        for r in rows
    ]
