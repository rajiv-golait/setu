"""Provider availability and appointment slot generation."""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AppointmentSlot, ProviderAvailability
from app.ids import new_id


def _parse_hm(s: str) -> time:
    h, m = s.split(":")
    return time(int(h), int(m))


async def list_availability(db: AsyncSession, provider_id: str) -> list[ProviderAvailability]:
    return list(
        (
            await db.execute(
                select(ProviderAvailability).where(ProviderAvailability.provider_id == provider_id)
            )
        ).scalars().all()
    )


async def set_availability(
    db: AsyncSession,
    provider_id: str,
    rules: list[dict],
) -> list[ProviderAvailability]:
    existing = await list_availability(db, provider_id)
    for row in existing:
        await db.delete(row)
    out: list[ProviderAvailability] = []
    for r in rules:
        row = ProviderAvailability(
            id=new_id("avail"),
            provider_id=provider_id,
            day_of_week=r["day_of_week"],
            start_time=r["start_time"],
            end_time=r["end_time"],
            slot_minutes=r.get("slot_minutes", 30),
            timezone=r.get("timezone", "Asia/Kolkata"),
        )
        db.add(row)
        out.append(row)
    await db.flush()
    return out


async def generate_slots(
    db: AsyncSession,
    provider_id: str,
    *,
    from_date: date,
    to_date: date,
) -> list[AppointmentSlot]:
    rules = await list_availability(db, provider_id)
    if not rules:
        return []

    created: list[AppointmentSlot] = []
    day = from_date
    while day <= to_date:
        dow = day.weekday()
        for rule in rules:
            if rule.day_of_week != dow:
                continue
            start = datetime.combine(day, _parse_hm(rule.start_time), tzinfo=timezone.utc)
            end = datetime.combine(day, _parse_hm(rule.end_time), tzinfo=timezone.utc)
            cursor = start
            delta = timedelta(minutes=rule.slot_minutes)
            while cursor + delta <= end:
                exists = (
                    await db.execute(
                        select(AppointmentSlot).where(
                            AppointmentSlot.provider_id == provider_id,
                            AppointmentSlot.starts_at == cursor,
                        )
                    )
                ).scalar_one_or_none()
                if exists is None:
                    slot = AppointmentSlot(
                        id=new_id("slot"),
                        provider_id=provider_id,
                        starts_at=cursor,
                        ends_at=cursor + delta,
                        status="open",
                    )
                    db.add(slot)
                    created.append(slot)
                cursor += delta
        day += timedelta(days=1)
    await db.flush()
    return created


async def list_open_slots(
    db: AsyncSession,
    provider_id: str,
    *,
    from_dt: datetime,
    to_dt: datetime,
) -> list[AppointmentSlot]:
    return list(
        (
            await db.execute(
                select(AppointmentSlot)
                .where(
                    AppointmentSlot.provider_id == provider_id,
                    AppointmentSlot.status == "open",
                    AppointmentSlot.starts_at >= from_dt,
                    AppointmentSlot.starts_at <= to_dt,
                )
                .order_by(AppointmentSlot.starts_at)
            )
        ).scalars().all()
    )


async def book_slot(db: AsyncSession, slot_id: str) -> AppointmentSlot:
    slot = (
        await db.execute(select(AppointmentSlot).where(AppointmentSlot.id == slot_id))
    ).scalar_one_or_none()
    if slot is None:
        raise ValueError("slot not found")
    if slot.status != "open":
        raise ValueError("slot not available")
    slot.status = "booked"
    await db.flush()
    return slot


async def release_slot(db: AsyncSession, slot_id: str | None) -> None:
    if not slot_id:
        return
    slot = (
        await db.execute(select(AppointmentSlot).where(AppointmentSlot.id == slot_id))
    ).scalar_one_or_none()
    if slot is not None:
        slot.status = "open"
        await db.flush()
