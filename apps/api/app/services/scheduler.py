"""Reminder push scheduler — fires web push for due reminders every 60 s.

Only runs when VAPID keys are configured (no-op in local dev without keys).
Never blocks the event loop: DB queries are async, push call uses executor.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

logger = logging.getLogger("setu.scheduler")

# Canonical time-of-day → 24-h hour (IST assumed — server should run in IST or UTC+5:30).
_SLOT_HOURS: dict[str, int] = {
    "morning": 8,
    "afternoon": 13,
    "evening": 19,
    "night": 21,
    "bedtime": 21,
    "now": 0,  # STAT — fire immediately; will only trigger once per schedule entry
}

_WINDOW_MINUTES = 5  # push fires if current_minute within ±5 of the slot hour's :00


def _is_due(times_of_day: list[str], now_hour: int, now_minute: int) -> bool:
    for slot in times_of_day:
        target_hour = _SLOT_HOURS.get(slot)
        if target_hour is None:
            continue
        if target_hour == now_hour and abs(now_minute) <= _WINDOW_MINUTES:
            return True
    return False


async def reminder_push_loop() -> None:
    from app.config import settings

    if not settings.VAPID_PRIVATE_KEY:
        logger.info("push scheduler skipped (no VAPID_PRIVATE_KEY)")
        return

    logger.info("push scheduler started")

    from sqlalchemy import select

    from app.db.models import Patient, PushSubscription, Reminder
    from app.db.session import SessionLocal
    from app.services.push_notifier import send_push

    while True:
        await asyncio.sleep(60)
        now = datetime.now(timezone.utc)
        now_hour = now.hour
        now_minute = now.minute

        try:
            async with SessionLocal() as db:
                reminders = (await db.execute(select(Reminder))).scalars().all()
                for reminder in reminders:
                    sched = reminder.schedule or {}
                    times = sched.get("times_of_day", [])
                    if not times or reminder.needs_confirmation:
                        continue
                    if not _is_due(times, now_hour, now_minute):
                        continue

                    # Look up the patient's Supabase user_id for push lookup.
                    patient = (
                        await db.execute(
                            select(Patient).where(Patient.id == reminder.patient_id)
                        )
                    ).scalar_one_or_none()
                    if not patient or not patient.supabase_user_id:
                        continue

                    subs = (
                        await db.execute(
                            select(PushSubscription).where(
                                PushSubscription.user_id == patient.supabase_user_id
                            )
                        )
                    ).scalars().all()

                    label = reminder.label or "Medication"
                    food = sched.get("relative_to_food") or ""
                    body = f"Time to take {label}" + (f" ({food})" if food else "")

                    for sub in subs:
                        await send_push(
                            sub.endpoint,
                            sub.p256dh,
                            sub.auth,
                            title="Setu Reminder",
                            body=body,
                        )
        except Exception as exc:  # noqa: BLE001 — never crash the loop
            logger.warning("scheduler tick error: %s", exc)
