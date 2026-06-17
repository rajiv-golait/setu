"""In-app notification list, unread count, and read marking."""
from __future__ import annotations

import jwt
import pytest
from sqlalchemy import select

from app.db.models import InAppNotification, Patient
from app.services import notifications as notify_svc

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


async def test_in_app_notification_lifecycle(client, session_factory, auth_enabled):
    async with session_factory() as db:
        db.add(
            Patient(
                id="pat_n",
                display_name="N",
                lang_pref="en",
                patient_token="tok_n",
                supabase_user_id="u_notif",
            )
        )
        await db.commit()

    hdr = _bearer(_token("u_notif", "patient"))

    async with session_factory() as db:
        await notify_svc.create_in_app(
            db,
            user_id="u_notif",
            title="Test",
            body="Hello",
            data={"k": "v"},
        )
        await db.commit()

    r = await client.get("/api/v1/notifications", headers=hdr)
    assert r.status_code == 200, r.text
    items = r.json()
    assert len(items) == 1
    assert items[0]["title"] == "Test"
    nid = items[0]["id"]

    r = await client.get("/api/v1/notifications/unread-count", headers=hdr)
    assert r.status_code == 200
    assert r.json()["count"] == 1

    r = await client.patch(f"/api/v1/notifications/{nid}/read", headers=hdr)
    assert r.status_code == 200

    r = await client.get("/api/v1/notifications/unread-count", headers=hdr)
    assert r.json()["count"] == 0

    async with session_factory() as db:
        row = (
            await db.execute(select(InAppNotification).where(InAppNotification.id == nid))
        ).scalar_one()
        assert row.status == "read"


async def test_booking_creates_in_app_notification(client, session_factory, auth_enabled):
    async with session_factory() as db:
        db.add(
            Patient(
                id="pat_bn",
                display_name="B",
                lang_pref="en",
                patient_token="tok_bn",
                supabase_user_id="u_bn",
            )
        )
        await db.commit()

    hdr = _bearer(_token("u_bn", "patient"))
    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": "pat_bn", "specialty": "dermatology"},
        headers=hdr,
    )
    assert r.status_code == 201, r.text

    r = await client.get("/api/v1/notifications", headers=hdr)
    assert r.status_code == 200
    assert any(n["title"] == "Consultation requested" for n in r.json())
