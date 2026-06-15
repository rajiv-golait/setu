"""Register SETU's Telegram webhook from container settings.

Usage:
  docker compose -f infra/docker-compose.yml exec api python scripts/register_telegram_webhook.py
"""
from __future__ import annotations

import asyncio
import sys

import httpx

from app.config import settings


async def main() -> int:
    if not settings.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN is not set", file=sys.stderr)
        return 1
    if not settings.PUBLIC_URL:
        print("PUBLIC_URL is not set (need a public HTTPS URL, e.g. cloudflared tunnel)", file=sys.stderr)
        return 1

    webhook_url = f"{settings.PUBLIC_URL.rstrip('/')}/telegram/webhook"
    payload: dict = {
        "url": webhook_url,
        "allowed_updates": ["message", "edited_message"],
    }
    if settings.TELEGRAM_SECRET:
        payload["secret_token"] = settings.TELEGRAM_SECRET

    base = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        reg = await client.post(f"{base}/setWebhook", json=payload)
        info = await client.get(f"{base}/getWebhookInfo")

    print("setWebhook:", reg.json())
    print("getWebhookInfo:", info.json())
    return 0 if reg.json().get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
