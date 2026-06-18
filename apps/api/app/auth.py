"""Supabase access-token verification for FastAPI.

Primary path: local HS256 verify when SUPABASE_JWT_SECRET is the real dashboard
secret (tests + legacy projects). Fallback: call Supabase Auth ``/auth/v1/user``
so we still work when only URL + anon key are configured (common mis-paste of
project id instead of JWT secret).
"""
from __future__ import annotations

import logging

import httpx
import jwt

from app.config import settings
from app.errors import UNAUTHORIZED, AppError

logger = logging.getLogger("setu.auth")


def _decode_local_jwt(token: str) -> dict:
    if not settings.SUPABASE_JWT_SECRET:
        raise AppError(
            UNAUTHORIZED,
            "Auth is enabled but SUPABASE_JWT_SECRET is not configured",
            retryable=False,
        )
    return jwt.decode(
        token,
        settings.SUPABASE_JWT_SECRET,
        algorithms=["HS256"],
        audience="authenticated",
    )


def _verify_local_jwt(token: str) -> str:
    payload = _decode_local_jwt(token)
    sub = payload.get("sub")
    if not sub:
        raise AppError(UNAUTHORIZED, "Token missing subject", retryable=False)
    return str(sub)


async def _fetch_supabase_user(token: str) -> dict:
    """Return the Supabase user object (includes id + app_metadata)."""
    if not settings.SUPABASE_URL or not settings.SUPABASE_ANON_KEY:
        raise AppError(UNAUTHORIZED, "Invalid or expired token", retryable=False)

    url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/user"
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "apikey": settings.SUPABASE_ANON_KEY,
            },
        )

    if response.status_code != 200:
        logger.debug("supabase auth user check failed: %s", response.status_code)
        raise AppError(UNAUTHORIZED, "Invalid or expired token", retryable=False)

    return response.json()


async def _verify_via_supabase_api(token: str) -> str:
    user = await _fetch_supabase_user(token)
    user_id = user.get("id")
    if not user_id:
        raise AppError(UNAUTHORIZED, "Token missing subject", retryable=False)
    return str(user_id)


async def verify_supabase_token(token: str) -> str:
    """Validate token and return Supabase user id (sub)."""
    if settings.SUPABASE_JWT_SECRET:
        try:
            return _verify_local_jwt(token)
        except jwt.PyJWTError:
            logger.info("local JWT verify failed; falling back to Supabase /auth/v1/user")

    return await _verify_via_supabase_api(token)


def _role_from_claims(claims: dict) -> str:
    """Read app_metadata.role, defaulting to 'patient'. The Supabase /user object
    and the JWT both expose app_metadata, so this works for either path."""
    app_metadata = claims.get("app_metadata") or {}
    role = app_metadata.get("role")
    if role:
        return str(role)
    if not settings.PRODUCTION and settings.DEV_ADMIN_EMAIL:
        email = str(claims.get("email") or "").strip().lower()
        if email and email == settings.DEV_ADMIN_EMAIL.strip().lower():
            return "admin"
    return "patient"


async def verify_supabase_role(token: str) -> str:
    """Validate token and return the caller's role from app_metadata.role.

    Mirrors verify_supabase_token's two-path design: local HS256 decode first
    (tests + projects with the JWT secret), then the Supabase /auth/v1/user
    fallback. Defaults to 'patient' when no role claim is present.
    """
    if settings.SUPABASE_JWT_SECRET:
        try:
            return _role_from_claims(_decode_local_jwt(token))
        except jwt.PyJWTError:
            logger.info("local JWT verify failed; falling back to Supabase /auth/v1/user")

    return _role_from_claims(await _fetch_supabase_user(token))


# Back-compat alias for any internal imports.
verify_supabase_jwt = _verify_local_jwt
