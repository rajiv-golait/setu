"""Admin set-role tests."""
from __future__ import annotations

import jwt
import pytest
from sqlalchemy import select

from app.db.models import Provider

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
    monkeypatch.setattr(config.settings, "SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setattr(config.settings, "SUPABASE_SERVICE_ROLE_KEY", "service-role-test-key")


async def test_admin_sets_doctor_role(client, session_factory, auth_enabled, monkeypatch):
    async def fake_ensure(phone: str, *, role: str) -> str:
        assert phone == "+919876543210"
        assert role == "provider"
        return "supa_test_doc"

    monkeypatch.setattr(
        "app.routers.admin_users_router.supabase_admin.ensure_user_with_role",
        fake_ensure,
    )

    r = await client.post(
        "/api/v1/admin/users/set-role",
        headers=_bearer(_token("u_admin", "admin")),
        json={"phone": "9876543210", "role": "provider", "display_name": "Dr. Test"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["role"] == "provider"
    assert body["provider_id"].startswith("prv_")

    async with session_factory() as db:
        row = (await db.execute(select(Provider))).scalar_one()
    assert row.supabase_user_id == "supa_test_doc"


async def test_admin_sets_patient_role_removes_provider(
    client, session_factory, auth_enabled, monkeypatch
):
    async with session_factory() as db:
        db.add(
            Provider(
                id="prv_old",
                supabase_user_id="supa_pat",
                phone="+919696106244",
                verification_status="approved",
            )
        )
        await db.commit()

    async def fake_ensure(phone: str, *, role: str) -> str:
        assert role == "patient"
        return "supa_pat"

    monkeypatch.setattr(
        "app.routers.admin_users_router.supabase_admin.ensure_user_with_role",
        fake_ensure,
    )

    r = await client.post(
        "/api/v1/admin/users/set-role",
        headers=_bearer(_token("u_admin", "admin")),
        json={"phone": "9696106244", "role": "patient"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["role"] == "patient"

    async with session_factory() as db:
        rows = (await db.execute(select(Provider))).scalars().all()
    assert rows == []
