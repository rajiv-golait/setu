"""Supabase JWT auth on patient-scoped routes."""
from __future__ import annotations

import time

import jwt
import pytest

pytestmark = pytest.mark.asyncio


def _mint_token(sub: str, secret: str = "test-jwt-secret-thirty-two-bytes!!") -> str:
    payload = {
        "sub": sub,
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
        "iat": int(time.time()),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture
def auth_settings(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", "test-jwt-secret-thirty-two-bytes!!")
    yield


async def _patient(session_factory, pid: str, user_id: str | None = None):
    from app.db.models import Patient

    async with session_factory() as db:
        db.add(
            Patient(
                id=pid,
                display_name="Auth Test",
                lang_pref="mr",
                patient_token=f"tok_{pid}",
                supabase_user_id=user_id,
            )
        )
        await db.commit()
    return pid


async def test_patient_route_requires_token_when_auth_enabled(client, session_factory, auth_settings):
    await _patient(session_factory, "pat_auth1", user_id="user-a")
    r = await client.get("/api/v1/patients/pat_auth1")
    assert r.status_code == 401


async def test_wrong_user_gets_forbidden(client, session_factory, auth_settings):
    await _patient(session_factory, "pat_auth2", user_id="user-owner")
    token = _mint_token("user-other")
    r = await client.get(
        "/api/v1/patients/pat_auth2",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "FORBIDDEN"


async def test_owner_can_access_patient(client, session_factory, auth_settings):
    await _patient(session_factory, "pat_auth3", user_id="user-owner")
    token = _mint_token("user-owner")
    r = await client.get(
        "/api/v1/patients/pat_auth3",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["id"] == "pat_auth3"


async def test_get_or_create_me(client, session_factory, auth_settings):
    token = _mint_token("user-new")
    r = await client.get("/api/v1/patients/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["id"].startswith("pat_")

    r2 = await client.get("/api/v1/patients/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.json()["id"] == body["id"]
