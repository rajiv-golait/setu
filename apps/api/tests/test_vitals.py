"""Phase 6 F5 — vitals thresholds and RBAC."""
from __future__ import annotations

import jwt
import pytest

from app.db.models import Patient, PatientLink
from app.ids import new_id
from app.services.vitals import flag_vital

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


def test_blood_pressure_thresholds():
    assert flag_vital("blood_pressure", {"systolic": 139, "diastolic": 85}) is None
    assert flag_vital("blood_pressure", {"systolic": 140, "diastolic": 85}) == "out_of_range"
    assert flag_vital("blood_pressure", {"systolic": 120, "diastolic": 90}) == "out_of_range"


def test_blood_sugar_thresholds():
    assert flag_vital("blood_sugar", {"fasting": 100}) is None
    assert flag_vital("blood_sugar", {"fasting": 127}) == "out_of_range"
    assert flag_vital("blood_sugar", {"fasting": 69}) == "out_of_range"


def test_spo2_and_heart_rate_thresholds():
    assert flag_vital("spo2", {"percent": 94}) is None
    assert flag_vital("spo2", {"percent": 93}) == "out_of_range"
    assert flag_vital("heart_rate", {"bpm": 50}) is None
    assert flag_vital("heart_rate", {"bpm": 49}) == "out_of_range"
    assert flag_vital("heart_rate", {"bpm": 101}) == "out_of_range"


async def _seed_linked_patient(session_factory, *, patient_sub: str, worker_sub: str) -> tuple[str, str]:
    from app.db.models import HealthWorker

    async with session_factory() as db:
        worker = HealthWorker(id=new_id("hw"), supabase_user_id=worker_sub, display_name="HW")
        patient = Patient(
            id=new_id("pat"),
            display_name="Vitals",
            lang_pref="mr",
            patient_token="tok_v",
            supabase_user_id=patient_sub,
        )
        db.add(worker)
        db.add(patient)
        await db.flush()
        db.add(
            PatientLink(
                id=new_id("lnk"),
                health_worker_id=worker.id,
                patient_id=patient.id,
            )
        )
        await db.commit()
        return patient.id, worker.id


@pytest.mark.asyncio
async def test_patient_posts_vital(client, session_factory, auth_enabled):
    async with session_factory() as db:
        db.add(
            Patient(
                id="pat_v1",
                display_name="V",
                lang_pref="mr",
                patient_token="tok_v1",
                supabase_user_id="u_v1",
            )
        )
        await db.commit()

    r = await client.post(
        "/api/v1/patients/pat_v1/vitals",
        headers=_bearer(_token("u_v1", "patient")),
        json={
            "vital_type": "heart_rate",
            "value": {"bpm": 72},
            "unit": "bpm",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["flag"] is None
    assert body.get("flag_message") is None


@pytest.mark.asyncio
async def test_out_of_range_has_informational_message_only(client, session_factory, auth_enabled):
    async with session_factory() as db:
        db.add(
            Patient(
                id="pat_v2",
                display_name="V",
                lang_pref="mr",
                patient_token="tok_v2",
                supabase_user_id="u_v2",
            )
        )
        await db.commit()

    r = await client.post(
        "/api/v1/patients/pat_v2/vitals",
        headers=_bearer(_token("u_v2", "patient")),
        json={
            "vital_type": "spo2",
            "value": {"percent": 90},
            "unit": "%",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["flag"] == "out_of_range"
    assert "doctor" in (body.get("flag_message") or "").lower()
    assert "diagnos" not in (body.get("flag_message") or "").lower()


@pytest.mark.asyncio
async def test_worker_with_link_can_post(client, session_factory, auth_enabled):
    pid, _wid = await _seed_linked_patient(session_factory, patient_sub="u_vp", worker_sub="u_hw_v")
    r = await client.post(
        f"/api/v1/patients/{pid}/vitals",
        headers=_bearer(_token("u_hw_v", "health_worker")),
        json={
            "vital_type": "blood_pressure",
            "value": {"systolic": 120, "diastolic": 80},
            "unit": "mmHg",
        },
    )
    assert r.status_code == 201, r.text


@pytest.mark.asyncio
async def test_unlinked_worker_gets_403(client, session_factory, auth_enabled):
    async with session_factory() as db:
        db.add(
            Patient(
                id="pat_v3",
                display_name="V",
                lang_pref="mr",
                patient_token="tok_v3",
            )
        )
        await db.commit()

    r = await client.post(
        "/api/v1/patients/pat_v3/vitals",
        headers=_bearer(_token("u_hw_x", "health_worker")),
        json={
            "vital_type": "heart_rate",
            "value": {"bpm": 80},
            "unit": "bpm",
        },
    )
    assert r.status_code == 403, r.text
