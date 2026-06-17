"""Web Push notification sender (pywebpush + VAPID).

Returns False immediately if VAPID keys are not configured — no-op for local dev.
Blocking pywebpush call is run in a thread executor to avoid blocking the event loop.
"""
from __future__ import annotations

import asyncio
import logging

logger = logging.getLogger("setu.push")


async def send_push(endpoint: str, p256dh: str, auth: str, *, title: str, body: str) -> bool:
    from app.config import settings

    if not settings.VAPID_PRIVATE_KEY or not settings.VAPID_PUBLIC_KEY:
        return False

    def _send() -> bool:
        try:
            from pywebpush import WebPusher, webpush

            webpush(
                subscription_info={
                    "endpoint": endpoint,
                    "keys": {"p256dh": p256dh, "auth": auth},
                },
                data=f'{{"title":"{title}","body":"{body}"}}',
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_CONTACT_EMAIL}"},
            )
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("push failed for %s: %s", endpoint[:40], exc)
            return False

    return await asyncio.get_event_loop().run_in_executor(None, _send)
