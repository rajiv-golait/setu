"""Admin appointment listing."""
from __future__ import annotations

import jwt
import pytest

from app.db.models import Patient

pytestmark = pytest.mark.asyncio

_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(sub: str, role: str) -> str:
    return jwt.encode(
        {"sub": sub, "aud": "authenticated", "app_metadata": {"role": role}},
        _SECRET,
        algorithm="HS256",
    )


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_enabled(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", _SECRET)


async def test_non_admin_cannot_list_all_appointments(client, auth_enabled):
    r = await client.get(
        "/api/v1/admin/appointments",
        headers=_bearer(_token("u", "patient")),
    )
    assert r.status_code == 403, r.text


async def test_admin_lists_appointments(client, session_factory, auth_enabled):
    async with session_factory() as db:
        db.add(
            Patient(
                id="pat_ad",
                display_name="A",
                lang_pref="en",
                patient_token="tok_ad",
                supabase_user_id="u_pat_ad",
            )
        )
        await db.commit()

    pat = _bearer(_token("u_pat_ad", "patient"))
    admin = _bearer(_token("u_admin", "admin"))

    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": "pat_ad", "specialty": "cardiology"},
        headers=pat,
    )
    assert r.status_code == 201, r.text

    r = await client.get("/api/v1/admin/appointments", headers=admin)
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) >= 1
    assert items[0]["specialty"] == "cardiology"
