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


def phone_match_key(phone: str) -> str:
    """Last 10 digits for matching Indian mobiles across +91 / 91 / bare formats."""
    digits = re.sub(r"\D", "", phone)
    if len(digits) >= 10:
        return digits[-10:]
    return digits


def phones_match(a: str, b: str) -> bool:
    return phone_match_key(a) == phone_match_key(b) and bool(phone_match_key(a))


def _supabase_error_message(response: httpx.Response) -> str:
    try:
        payload = response.json()
        if isinstance(payload, dict):
            for key in ("msg", "message", "error_description", "error"):
                value = payload.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
    except Exception:  # noqa: BLE001
        pass
    text = response.text.strip()
    return text[:240] if text else f"HTTP {response.status_code}"


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
                user_phone = user.get("phone") or user.get("phone_number") or ""
                if phones_match(str(user_phone), phone):
                    return user
            if len(users) < 200:
                return None
            page += 1
    return None


async def find_user_by_email(email: str) -> dict | None:
    headers = _admin_headers()
    target = email.strip().lower()
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
                if str(user.get("email", "")).lower() == target:
                    return user
            if len(users) < 200:
                return None
            page += 1
    return None


async def create_email_user(email: str, password: str, *, role: str) -> dict:
    if role not in _ALLOWED_ROLES:
        raise AppError(VALIDATION_ERROR, f"Invalid role: {role!r}", retryable=False)
    headers = _admin_headers()
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.post(
            _admin_url("/admin/users"),
            headers=headers,
            json={
                "email": email.strip(),
                "password": password,
                "email_confirm": True,
                "app_metadata": {"role": role},
            },
        )
    if response.status_code not in (200, 201):
        logger.warning("supabase create email user failed: %s %s", response.status_code, response.text)
        raise AppError(
            VALIDATION_ERROR,
            "Could not create admin account in Supabase",
            details={"status": response.status_code},
            retryable=False,
        )
    return response.json()


async def ensure_email_admin(email: str, password: str) -> str:
    """Return Supabase user id for an admin account (create or update role + password)."""
    existing = await find_user_by_email(email)
    if existing is not None:
        user_id = str(existing["id"])
        await set_user_role(user_id, "admin")
        headers = _admin_headers()
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.put(
                _admin_url(f"/admin/users/{user_id}"),
                headers=headers,
                json={"password": password, "app_metadata": {"role": "admin"}},
            )
        if response.status_code != 200:
            logger.warning("supabase update admin failed: %s %s", response.status_code, response.text)
            raise AppError(VALIDATION_ERROR, "Could not update admin password", retryable=False)
        return user_id
    created = await create_email_user(email, password, role="admin")
    return str(created["id"])


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
        reason = _supabase_error_message(response)
        logger.warning("supabase create user failed: %s %s", response.status_code, response.text)
        hint = ""
        lower = reason.lower()
        if "phone" in lower and ("exist" in lower or "registered" in lower or "duplicate" in lower):
            hint = " This number may already exist — try saving again."
        elif "phone" in lower and ("disabled" in lower or "provider" in lower):
            hint = " Enable Phone auth in Supabase → Authentication → Providers."
        raise AppError(
            VALIDATION_ERROR,
            f"Could not create doctor account in Supabase: {reason}.{hint}",
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
    normalized = normalize_phone(phone)
    existing = await find_user_by_phone(normalized)
    if existing is not None:
        await set_user_role(existing["id"], role)
        return str(existing["id"])
    try:
        created = await create_phone_user(normalized, role=role)
        return str(created["id"])
    except AppError:
        # User may exist under a different phone format — re-scan before failing.
        existing = await find_user_by_phone(normalized)
        if existing is not None:
            await set_user_role(existing["id"], role)
            return str(existing["id"])
        raise
