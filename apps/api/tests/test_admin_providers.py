"""Admin provider grant/revoke tests."""
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


async def test_non_admin_cannot_list_providers(client, auth_enabled):
    r = await client.get("/api/v1/admin/providers", headers=_bearer(_token("u", "patient")))
    assert r.status_code == 403, r.text


async def test_admin_grants_provider(client, session_factory, auth_enabled, monkeypatch):
    async def fake_ensure(phone: str, *, role: str) -> str:
        assert phone == "+919876543210"
        assert role == "provider"
        return "supa_doc_1"

    monkeypatch.setattr(
        "app.routers.admin_providers_router.supabase_admin.ensure_user_with_role",
        fake_ensure,
    )

    headers = _bearer(_token("u_admin", "admin"))
    r = await client.post(
        "/api/v1/admin/providers",
        headers=headers,
        json={
            "phone": "9876543210",
            "display_name": "Dr. Patel",
            "specialty": "dermatology",
            "facility": "PHC Pune",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["id"].startswith("prv_")
    assert body["phone"] == "+919876543210"
    assert body["display_name"] == "Dr. Patel"
    assert body["specialty"] == "dermatology"

    async with session_factory() as db:
        rows = (await db.execute(select(Provider))).scalars().all()
    assert len(rows) == 1
    assert rows[0].supabase_user_id == "supa_doc_1"


async def test_admin_revokes_provider(client, session_factory, auth_enabled, monkeypatch):
    revoked: list[str] = []

    async def fake_set_role(user_id: str, role: str) -> None:
        revoked.append(user_id)

    monkeypatch.setattr(
        "app.routers.admin_providers_router.supabase_admin.set_user_role",
        fake_set_role,
    )

    async with session_factory() as db:
        db.add(
            Provider(
                id="prv_revoke",
                supabase_user_id="supa_x",
                phone="+919999999999",
                display_name="Dr. X",
            )
        )
        await db.commit()

    r = await client.delete(
        "/api/v1/admin/providers/prv_revoke",
        headers=_bearer(_token("u_admin", "admin")),
    )
    assert r.status_code == 204, r.text
    assert revoked == ["supa_x"]

    async with session_factory() as db:
        rows = (await db.execute(select(Provider))).scalars().all()
    assert rows == []
