"""Phase 1 — provider role foundation tests.

Auth is exercised with real local HS256 tokens (the same path tests use in
production-like config). Each test opts into Supabase auth by overriding the
autouse `_disable_supabase_auth` fixture via monkeypatch and signing a token
that carries app_metadata.role.
"""
from __future__ import annotations

import jwt
import pytest

from app.auth import _role_from_claims, verify_supabase_role

_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(sub: str, role: str | None = None) -> str:
    claims: dict = {"sub": sub, "aud": "authenticated"}
    if role is not None:
        claims["app_metadata"] = {"role": role}
    return jwt.encode(claims, _SECRET, algorithm="HS256")


@pytest.fixture
def auth_enabled(monkeypatch):
    """Turn on Supabase auth with a known local JWT secret for the test."""
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", _SECRET)


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# --- role claim parsing --------------------------------------------------- #


def test_role_from_claims_reads_app_metadata():
    assert _role_from_claims({"app_metadata": {"role": "provider"}}) == "provider"
    assert _role_from_claims({"app_metadata": {"role": "admin"}}) == "admin"


def test_role_from_claims_defaults_to_patient():
    assert _role_from_claims({}) == "patient"
    assert _role_from_claims({"app_metadata": {}}) == "patient"


@pytest.mark.asyncio
async def test_verify_supabase_role_reads_token(auth_enabled):
    assert await verify_supabase_role(_token("u_prov", "provider")) == "provider"
    assert await verify_supabase_role(_token("u_anon")) == "patient"


# --- require_provider via the HTTP surface -------------------------------- #


@pytest.mark.asyncio
async def test_patient_role_rejected_from_provider_route(client, auth_enabled):
    r = await client.get("/api/v1/providers/me", headers=_bearer(_token("u_pat", "patient")))
    assert r.status_code == 403, r.text
    assert r.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_provider_me_auto_provisions(client, session_factory, auth_enabled):
    from sqlalchemy import select

    from app.db.models import Provider

    headers = _bearer(_token("u_prov", "provider"))
    r = await client.get("/api/v1/providers/me", headers=headers)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"].startswith("prv_")
    pid = body["id"]

    # Row was persisted.
    async with session_factory() as db:
        rows = (await db.execute(select(Provider))).scalars().all()
    assert len(rows) == 1
    assert rows[0].supabase_user_id == "u_prov"

    # Second call returns the same provider (no duplicate provisioning).
    r2 = await client.get("/api/v1/providers/me", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["id"] == pid

    async with session_factory() as db:
        rows = (await db.execute(select(Provider))).scalars().all()
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_provider_route_requires_auth(client, auth_enabled):
    r = await client.get("/api/v1/providers/me")  # no bearer token
    assert r.status_code == 401, r.text


@pytest.mark.asyncio
async def test_provider_patch_updates_profile(client, session_factory, auth_enabled):
    headers = _bearer(_token("u_prov_patch", "provider"))
    r = await client.patch(
        "/api/v1/providers/me",
        headers=headers,
        json={"display_name": "Dr. Test", "specialty": "cardiology", "facility": "PHC Pune"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["display_name"] == "Dr. Test"
    assert body["specialty"] == "cardiology"
    assert body["facility"] == "PHC Pune"
