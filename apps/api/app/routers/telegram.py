"""Telegram webhook. Mounted WITHOUT the /api/v1 prefix.

Register with Telegram via:
  POST https://api.telegram.org/bot{TOKEN}/setWebhook
       url={PUBLIC_URL}/telegram/webhook
       secret_token={TELEGRAM_SECRET}   (optional)

The endpoint ALWAYS returns 200 immediately (Telegram retries on non-200) and
processes the Update in the background.
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Header, Request

from app.config import settings
from app.services.telegram import handle_update

logger = logging.getLogger("setu.telegram")

router = APIRouter(tags=["telegram"])


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    background: BackgroundTasks,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict:
    # Optional shared-secret verification.
    if settings.TELEGRAM_SECRET and x_telegram_bot_api_secret_token != settings.TELEGRAM_SECRET:
        logger.warning("telegram webhook: bad secret token")
        # Still 200 — we just drop the update rather than triggering retries.
        return {"ok": True}

    try:
        update = await request.json()
    except Exception:  # noqa: BLE001 — malformed body, drop it
        logger.warning("telegram webhook: invalid JSON body")
        return {"ok": True}

    background.add_task(handle_update, update)
    return {"ok": True}
