"""Phase 6 F4 — health worker proxy flows."""
from __future__ import annotations

import io

import jwt
import pytest
from sqlalchemy import select

from app.db.models import AccessLog, Consent, PatientLink

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


async def test_worker_registers_patient_with_link_and_consent(
    client, session_factory, auth_enabled
):
    headers = _bearer(_token("u_hw1", "health_worker"))
    r = await client.get("/api/v1/workers/me", headers=headers)
    assert r.status_code == 200, r.text
    worker_id = r.json()["id"]

    r = await client.post(
        "/api/v1/workers/patients",
        headers=headers,
        json={"display_name": "Rural Patient", "lang_pref": "mr", "is_rural": True},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    async with session_factory() as db:
        links = (await db.execute(select(PatientLink))).scalars().all()
        assert len(links) == 1
        assert links[0].health_worker_id == worker_id
        consents = (await db.execute(select(Consent).where(Consent.patient_id == pid))).scalars().all()
        assert len(consents) == 1
        logs = (await db.execute(select(AccessLog).where(AccessLog.action == "register_patient"))).scalars().all()
        assert len(logs) == 1


async def test_unlinked_worker_cannot_upload(client, session_factory, auth_enabled):
    headers = _bearer(_token("u_hw2", "health_worker"))
    async with session_factory() as db:
        from app.db.models import Patient

        db.add(
            Patient(
                id="pat_orphan",
                display_name="Orphan",
                lang_pref="mr",
                patient_token="tok_orphan",
            )
        )
        await db.commit()

    files = {"file": ("rx.jpg", io.BytesIO(b"bytes"), "image/jpeg")}
    r = await client.post(
        "/api/v1/workers/patients/pat_orphan/documents",
        headers=headers,
        files=files,
    )
    assert r.status_code == 403, r.text


async def test_patient_role_rejected_from_worker_routes(client, auth_enabled):
    r = await client.get("/api/v1/workers/me", headers=_bearer(_token("u_p", "patient")))
    assert r.status_code == 403, r.text


async def test_worker_books_appointment_for_linked_patient(client, session_factory, auth_enabled):
    headers = _bearer(_token("u_hw3", "health_worker"))
    r = await client.post(
        "/api/v1/workers/patients",
        headers=headers,
        json={"display_name": "Appt Patient", "lang_pref": "en"},
    )
    assert r.status_code == 201, r.text
    pid = r.json()["id"]

    r = await client.post(
        "/api/v1/appointments",
        headers=headers,
        json={"patient_id": pid, "specialty": "general"},
    )
    assert r.status_code == 201, r.text
    assert r.json()["patient_id"] == pid

    r = await client.get("/api/v1/appointments", headers=headers)
    assert r.status_code == 200, r.text
    assert len(r.json()) == 1
