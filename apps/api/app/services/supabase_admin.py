"""Supabase Auth Admin API — grant/revoke app_metadata roles (server-side only)."""
from __future__ import annotations

import logging
import re

import httpx

from app.config import settings
from app.errors import VALIDATION_ERROR, AppError

logger = logging.getLogger("setu.supabase_admin")

_ALLOWED_ROLES = frozenset({"patient", "provider", "health_worker", "admin"})


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw.strip())
    if raw.strip().startswith("+"):
        return f"+{digits}"
    if len(digits) == 10:
        return f"+91{digits}"
    if digits.startswith("91") and len(digits) == 12:
        return f"+{digits}"
    raise AppError(VALIDATION_ERROR, "Enter a valid 10-digit mobile number", retryable=False)


def _admin_headers() -> dict[str, str]:
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise AppError(
            VALIDATION_ERROR,
            "SUPABASE_SERVICE_ROLE_KEY is not configured on the API",
            retryable=False,
        )
    key = settings.SUPABASE_SERVICE_ROLE_KEY
    return {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }


def _admin_url(path: str) -> str:
    return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1{path}"


async def find_user_by_phone(phone: str) -> dict | None:
    headers = _admin_headers()
    page = 1
    async with httpx.AsyncClient(timeout=20.0) as client:
        while page <= 10:
            response = await client.get(
                _admin_url("/admin/users"),
                headers=headers,
                params={"page": page, "per_page": 200},
            )
            if response.status_code != 200:
                logger.warning("supabase list users failed: %s", response.status_code)
                raise AppError(
                    VALIDATION_ERROR,
                    "Could not look up user in Supabase",
                    retryable=True,
                )
            payload = response.json()
            users = payload.get("users") if isinstance(payload, dict) else payload
            if not users:
                return None
            for user in users:
                if user.get("phone") == phone:
                    return user
            if len(users) < 200:
                return None
            page += 1
    return None


async def create_phone_user(phone: str, *, role: str) -> dict:
    headers = _admin_headers()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            _admin_url("/admin/users"),
            headers=headers,
            json={
                "phone": phone,
                "phone_confirm": True,
                "app_metadata": {"role": role},
            },
        )
    if response.status_code not in (200, 201):
        logger.warning("supabase create user failed: %s %s", response.status_code, response.text)
        raise AppError(
            VALIDATION_ERROR,
            "Could not create doctor account in Supabase",
            details={"status": response.status_code},
            retryable=False,
        )
    return response.json()


async def set_user_role(user_id: str, role: str) -> None:
    if role not in _ALLOWED_ROLES:
        raise AppError(VALIDATION_ERROR, f"Invalid role: {role!r}", retryable=False)
    headers = _admin_headers()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.put(
            _admin_url(f"/admin/users/{user_id}"),
            headers=headers,
            json={"app_metadata": {"role": role}},
        )
    if response.status_code != 200:
        logger.warning("supabase update user failed: %s %s", response.status_code, response.text)
        raise AppError(
            VALIDATION_ERROR,
            "Could not update user role in Supabase",
            details={"status": response.status_code},
            retryable=False,
        )


async def ensure_user_with_role(phone: str, *, role: str) -> str:
    """Return Supabase user id with the given app_metadata.role."""
    existing = await find_user_by_phone(phone)
    if existing is not None:
        await set_user_role(existing["id"], role)
        return str(existing["id"])
    created = await create_phone_user(phone, role=role)
    return str(created["id"])
