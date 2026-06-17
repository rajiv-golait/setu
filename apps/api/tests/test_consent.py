"""Consent withdrawal blocks further uploads."""
from __future__ import annotations

import io

import jwt
import pytest

from app.db.models import Consent, Patient

pytestmark = pytest.mark.asyncio

_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(sub: str) -> str:
    return jwt.encode({"sub": sub, "aud": "authenticated"}, _SECRET, algorithm="HS256")


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_enabled(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", _SECRET)


async def _make_patient(session_factory, pid: str = "pat_c1", sub: str | None = None) -> str:
    async with session_factory() as db:
        db.add(
            Patient(
                id=pid,
                display_name="Test",
                lang_pref="mr",
                patient_token=f"tok_{pid}",
                supabase_user_id=sub,
            )
        )
        await db.commit()
    return pid


def _file():
    return {"file": ("rx.jpg", io.BytesIO(b"fake-image-bytes"), "image/jpeg")}


async def test_upload_without_consent_is_rejected(client, session_factory):
    pid = await _make_patient(session_factory)
    r = await client.post("/api/v1/documents", files=_file(), data={"patient_id": pid})
    assert r.status_code == 403, r.text
    assert r.json()["error"]["code"] == "CONSENT_REQUIRED"


async def test_consent_then_upload_succeeds(client, session_factory):
    pid = await _make_patient(session_factory, "pat_c2")

    r = await client.post(
        "/api/v1/consent",
        json={"patient_id": pid, "purpose": "document_processing", "lang": "mr", "channel": "web"},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["consent_id"]
    assert body["granted_at"]
    assert body["consent_text"]

    async with session_factory() as db:
        from sqlalchemy import select

        rows = (await db.execute(select(Consent).where(Consent.patient_id == pid))).scalars().all()
        assert len(rows) == 1
        assert rows[0].purpose == "document_processing"

    r = await client.post("/api/v1/documents", files=_file(), data={"patient_id": pid})
    assert r.status_code == 202, r.text
    assert r.json()["status"] == "queued"


async def test_withdraw_consent_blocks_upload(client, session_factory, auth_enabled):
    sub = "u_withdraw"
    pid = await _make_patient(session_factory, "pat_wd", sub=sub)
    headers = _bearer(_token(sub))

    r = await client.post(
        "/api/v1/consent",
        json={"patient_id": pid, "purpose": "document_processing", "lang": "mr", "channel": "web"},
        headers=headers,
    )
    assert r.status_code == 201, r.text

    r = await client.post(
        "/api/v1/consent/withdraw",
        json={"patient_id": pid},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["withdrawn"] is True

    r = await client.post(
        "/api/v1/documents", files=_file(), data={"patient_id": pid}, headers=headers
    )
    assert r.status_code == 403, r.text
