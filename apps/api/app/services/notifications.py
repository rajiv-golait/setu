"""Notification outbox — SMS, email, WhatsApp adapters."""
from __future__ import annotations

import logging
from datetime import datetime, timezone

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import (
    InAppNotification,
    NotificationOutbox,
    NotificationPreference,
    Patient,
    Provider,
)
from app.ids import new_id

logger = logging.getLogger("setu.notifications")


async def create_in_app(
    db: AsyncSession,
    *,
    user_id: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> InAppNotification:
    row = InAppNotification(
        id=new_id("ian"),
        user_id=user_id,
        title=title,
        body=body,
        data=data,
        status="pending",
    )
    db.add(row)
    await db.flush()
    return row


async def resolve_patient_user_id(db: AsyncSession, patient_id: str) -> str:
    patient = (
        await db.execute(select(Patient).where(Patient.id == patient_id))
    ).scalar_one_or_none()
    if patient and patient.supabase_user_id:
        return patient.supabase_user_id
    return patient_id


async def notify_patient_in_app(
    db: AsyncSession,
    *,
    patient_id: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> InAppNotification:
    uid = await resolve_patient_user_id(db, patient_id)
    return await create_in_app(db, user_id=uid, title=title, body=body, data=data)


async def notify_provider_in_app(
    db: AsyncSession,
    *,
    provider_id: str,
    title: str,
    body: str,
    data: dict | None = None,
) -> InAppNotification:
    provider = (
        await db.execute(select(Provider).where(Provider.id == provider_id))
    ).scalar_one_or_none()
    uid = provider.supabase_user_id if provider else provider_id
    return await create_in_app(db, user_id=uid, title=title, body=body, data=data)


async def channel_enabled(db: AsyncSession, user_id: str, channel: str) -> bool:
    row = (
        await db.execute(
            select(NotificationPreference).where(
                NotificationPreference.user_id == user_id,
                NotificationPreference.channel == channel,
            )
        )
    ).scalar_one_or_none()
    return row.enabled if row is not None else False


async def enqueue(
    db: AsyncSession,
    *,
    event_type: str,
    recipient: str,
    channel: str,
    payload: dict,
    scheduled_for: datetime | None = None,
) -> NotificationOutbox:
    row = NotificationOutbox(
        id=new_id("ntf"),
        event_type=event_type,
        recipient=recipient,
        channel=channel,
        payload=payload,
        scheduled_for=scheduled_for,
    )
    db.add(row)
    await db.flush()
    return row


async def _send_sms(recipient: str, body: str) -> bool:
    if settings.SMS_PROVIDER == "twilio" and settings.TWILIO_ACCOUNT_SID:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                url,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN),
                data={"To": recipient, "From": settings.TWILIO_FROM_NUMBER, "Body": body},
            )
            return r.status_code < 300
    if settings.SMS_PROVIDER == "msg91" and settings.MSG91_AUTH_KEY:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.msg91.com/api/v5/flow/",
                headers={"authkey": settings.MSG91_AUTH_KEY},
                json={
                    "template_id": "setu_default",
                    "recipients": [{"mobiles": recipient.lstrip("+"), "var": body}],
                },
            )
            return r.status_code < 300
    logger.info("sms stub to %s: %s", recipient, body[:80])
    return True


async def _send_email(recipient: str, subject: str, body: str) -> bool:
    if settings.SENDGRID_API_KEY:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": recipient}]}],
                    "from": {"email": settings.NOTIFICATION_FROM_EMAIL},
                    "subject": subject,
                    "content": [{"type": "text/plain", "value": body}],
                },
            )
            return r.status_code < 300
    logger.info("email stub to %s: %s", recipient, subject)
    return True


async def _send_whatsapp(recipient: str, body: str) -> bool:
    if settings.WHATSAPP_API_URL and settings.WHATSAPP_API_TOKEN:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(
                settings.WHATSAPP_API_URL,
                headers={"Authorization": f"Bearer {settings.WHATSAPP_API_TOKEN}"},
                json={"to": recipient, "text": body},
            )
            return r.status_code < 300
    logger.info("whatsapp stub to %s", recipient)
    return True


async def deliver_row(row: NotificationOutbox) -> bool:
    body = row.payload.get("body", "")
    subject = row.payload.get("subject", "Setu notification")
    if row.channel == "sms":
        return await _send_sms(row.recipient, body)
    if row.channel == "email":
        return await _send_email(row.recipient, subject, body)
    if row.channel == "whatsapp":
        return await _send_whatsapp(row.recipient, body)
    if row.channel == "in_app":
        return True
    return False


async def process_outbox(db: AsyncSession, *, limit: int = 50) -> int:
    now = datetime.now(timezone.utc)
    rows = list(
        (
            await db.execute(
                select(NotificationOutbox)
                .where(
                    NotificationOutbox.status == "pending",
                    (NotificationOutbox.scheduled_for.is_(None))
                    | (NotificationOutbox.scheduled_for <= now),
                )
                .order_by(NotificationOutbox.created_at)
                .limit(limit)
            )
        ).scalars().all()
    )
    sent = 0
    for row in rows:
        ok = await deliver_row(row)
        row.status = "sent" if ok else "failed"
        if ok:
            row.sent_at = now
            sent += 1
    if rows:
        await db.commit()
    return sent


async def notify_appointment_event(
    db: AsyncSession,
    *,
    event_type: str,
    phone: str | None,
    email: str | None,
    message: str,
    user_id: str | None = None,
) -> None:
    if user_id and await channel_enabled(db, user_id, "sms") and phone:
        await enqueue(
            db,
            event_type=event_type,
            recipient=phone,
            channel="sms",
            payload={"body": message},
        )
    elif phone and not user_id:
        await enqueue(
            db,
            event_type=event_type,
            recipient=phone,
            channel="sms",
            payload={"body": message},
        )
    if user_id and await channel_enabled(db, user_id, "email") and email:
        await enqueue(
            db,
            event_type=event_type,
            recipient=email,
            channel="email",
            payload={"subject": f"Setu: {event_type}", "body": message},
        )
    elif email and not user_id:
        await enqueue(
            db,
            event_type=event_type,
            recipient=email,
            channel="email",
            payload={"subject": f"Setu: {event_type}", "body": message},
        )
