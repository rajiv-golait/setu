"""Encounter prescriptions and patient-scoped summary access."""
from __future__ import annotations

import jwt
import pytest
from sqlalchemy import select

from app.db.models import Encounter, Patient, Provider

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


async def _seed_patient(session_factory, *, patient_id: str, supabase_user_id: str):
    async with session_factory() as db:
        db.add(
            Patient(
                id=patient_id,
                display_name="Pat",
                lang_pref="en",
                patient_token=f"tok_{patient_id}",
                supabase_user_id=supabase_user_id,
            )
        )
        await db.commit()


async def _seed_provider(session_factory, *, supabase_user_id: str, provider_id: str | None = None):
    from app.ids import new_id

    pid = provider_id or new_id("prv")
    async with session_factory() as db:
        db.add(
            Provider(
                id=pid,
                supabase_user_id=supabase_user_id,
                display_name="Dr. Rx",
                specialty="general",
                verification_status="approved",
            )
        )
        await db.commit()
    return pid


async def _book_and_accept(client, session_factory, pat_hdr, prov_hdr):
    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": "pat_rx", "specialty": "general"},
        headers=pat_hdr,
    )
    assert r.status_code == 201, r.text
    appt_id = r.json()["id"]
    r = await client.patch(
        f"/api/v1/appointments/{appt_id}",
        json={"action": "accept"},
        headers=prov_hdr,
    )
    assert r.status_code == 200, r.text
    async with session_factory() as db:
        enc = (
            await db.execute(select(Encounter).where(Encounter.appointment_id == appt_id))
        ).scalar_one()
    return appt_id, enc.id


async def test_provider_adds_prescription_and_patient_reads_summary(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, patient_id="pat_rx", supabase_user_id="u_pat_rx")
    await _seed_provider(session_factory, supabase_user_id="u_prov_rx")

    pat = _bearer(_token("u_pat_rx", "patient"))
    prov = _bearer(_token("u_prov_rx", "provider"))

    _appt_id, enc_id = await _book_and_accept(client, session_factory, pat, prov)

    r = await client.post(
        f"/api/v1/encounters/{enc_id}/prescriptions",
        json={
            "items": [
                {"name": "Paracetamol", "dose": "500mg", "frequency": "BD", "duration": "3d"}
            ]
        },
        headers=prov,
    )
    assert r.status_code == 200, r.text
    assert r.json()["id"]

    r = await client.get(f"/api/v1/encounters/{enc_id}/summary", headers=pat)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["encounter_id"] == enc_id
    assert len(body["prescriptions"]) == 1

    r = await client.get(f"/api/v1/appointments/{_appt_id}/visit-summary", headers=pat)
    assert r.status_code == 200, r.text
    assert r.json()["prescriptions"]


async def test_patient_cannot_read_other_patients_encounter_summary(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, patient_id="pat_a", supabase_user_id="u_a")
    await _seed_patient(session_factory, patient_id="pat_b", supabase_user_id="u_b")
    await _seed_provider(session_factory, supabase_user_id="u_prov2")

    pat_a = _bearer(_token("u_a", "patient"))
    pat_b = _bearer(_token("u_b", "patient"))
    prov = _bearer(_token("u_prov2", "provider"))

    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": "pat_a", "specialty": "general"},
        headers=pat_a,
    )
    appt_id = r.json()["id"]
    await client.patch(
        f"/api/v1/appointments/{appt_id}",
        json={"action": "accept"},
        headers=prov,
    )
    async with session_factory() as db:
        enc_id = (
            await db.execute(select(Encounter).where(Encounter.appointment_id == appt_id))
        ).scalar_one().id

    r = await client.get(f"/api/v1/encounters/{enc_id}/summary", headers=pat_b)
    assert r.status_code == 403, r.text
