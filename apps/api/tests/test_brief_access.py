"""Access-control tests for the brief and memory endpoints.

Scenarios:
- Provider WITHOUT a grant/appointment → 403 on GET /patients/{id}/brief
- Provider WITH an accepted appointment → 200
- Patient reading their own brief → 200
- Public token route (/brief/{token}) → 200 (no auth required)
"""
from __future__ import annotations

import pytest

from app.db.models import Brief as BriefRow
from app.db.models import Patient, Provider

pytestmark = pytest.mark.asyncio

_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(sub: str, role: str) -> str:
    import jwt

    return jwt.encode(
        {"sub": sub, "aud": "authenticated", "app_metadata": {"role": role}},
        _SECRET,
        algorithm="HS256",
    )


def _bearer(t: str) -> dict:
    return {"Authorization": f"Bearer {t}"}


@pytest.fixture
def auth_enabled(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", _SECRET)


async def _seed_patient(session_factory, patient_id: str, user_id: str) -> None:
    async with session_factory() as db:
        db.add(
            Patient(
                id=patient_id,
                display_name="Alice",
                lang_pref="en",
                patient_token=f"tok_{patient_id}",
                supabase_user_id=user_id,
            )
        )
        await db.commit()


async def _seed_provider(session_factory, provider_id: str, user_id: str) -> None:
    async with session_factory() as db:
        db.add(
            Provider(
                id=provider_id,
                supabase_user_id=user_id,
                display_name="Dr. Test",
                specialty="general",
                verification_status="approved",
            )
        )
        await db.commit()


async def _seed_brief(session_factory, patient_id: str) -> str:
    """Insert a minimal brief row so GET /brief returns 200 not 404."""
    import json
    from datetime import datetime, timezone

    from app.ids import new_id

    brief_id = new_id("brf")
    payload = {
        "brief_id": brief_id,
        "patient_id": patient_id,
        "one_line": "Test patient",
        "chief_concern": "checkup",
        "active_medications": [],
        "recent_labs": [],
        "active_conditions": [],
        "allergies": [],
        "suggested_questions": [],
        "flags": [],
        "model": "mock",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    async with session_factory() as db:
        db.add(
            BriefRow(
                id=brief_id,
                patient_id=patient_id,
                brief_json=payload,
                model="mock",
                generated_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
    return brief_id


async def _accept_appointment(client, session_factory, pat_hdr, prov_hdr, patient_id: str):
    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": patient_id, "specialty": "general"},
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
    return appt_id


# ---------------------------------------------------------------------------


async def test_provider_without_grant_gets_403_on_brief(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, "pat_b1", "u_pat_b1")
    await _seed_provider(session_factory, "prv_b1", "u_prv_b1")
    await _seed_brief(session_factory, "pat_b1")

    r = await client.get(
        "/api/v1/patients/pat_b1/brief",
        headers=_bearer(_token("u_prv_b1", "provider")),
    )
    assert r.status_code == 403, r.text


async def test_provider_with_appointment_gets_200_on_brief(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, "pat_b2", "u_pat_b2")
    await _seed_provider(session_factory, "prv_b2", "u_prv_b2")
    await _seed_brief(session_factory, "pat_b2")

    pat = _bearer(_token("u_pat_b2", "patient"))
    prov = _bearer(_token("u_prv_b2", "provider"))
    await _accept_appointment(client, session_factory, pat, prov, "pat_b2")

    r = await client.get("/api/v1/patients/pat_b2/brief", headers=prov)
    assert r.status_code == 200, r.text
    assert r.json()["patient_id"] == "pat_b2"


async def test_patient_reads_own_brief(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, "pat_b3", "u_pat_b3")
    await _seed_brief(session_factory, "pat_b3")

    r = await client.get(
        "/api/v1/patients/pat_b3/brief",
        headers=_bearer(_token("u_pat_b3", "patient")),
    )
    assert r.status_code == 200, r.text


async def test_patient_cannot_read_another_patients_brief(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, "pat_b4", "u_pat_b4")
    await _seed_patient(session_factory, "pat_b5", "u_pat_b5")
    await _seed_brief(session_factory, "pat_b4")

    r = await client.get(
        "/api/v1/patients/pat_b4/brief",
        headers=_bearer(_token("u_pat_b5", "patient")),
    )
    assert r.status_code == 403, r.text


async def test_public_token_route_needs_no_auth(client, session_factory):
    """GET /brief/{token} is public — no Authorization header required."""
    from datetime import datetime, timezone

    from app.db.models import Share as ShareRow
    from app.ids import new_id, new_token

    await _seed_patient(session_factory, "pat_b6", "u_pat_b6")
    await _seed_brief(session_factory, "pat_b6")

    tok = new_token(10)
    snapshot = {
        "share_id": new_id("shr"),
        "token": tok,
        "patient_ref": "Patient",
        "audience": "patient",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": None,
        "brief": {
            "brief_id": "brf_x",
            "patient_id": "pat_b6",
            "one_line": "",
            "chief_concern": "",
            "active_medications": [],
            "recent_labs": [],
            "active_conditions": [],
            "allergies": [],
            "suggested_questions": [],
            "flags": [],
            "model": "mock",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        },
        "current_truth": {"patient_id": "pat_b6", "entries": [], "generated_at": datetime.now(timezone.utc).isoformat()},
    }
    async with session_factory() as db:
        db.add(
            ShareRow(
                id=new_id("shr"),
                patient_id="pat_b6",
                token=tok,
                snapshot_json=snapshot,
                view_count=0,
                created_at=datetime.now(timezone.utc),
                expires_at=None,
            )
        )
        await db.commit()

    r = await client.get(f"/api/v1/brief/{tok}")  # no Authorization header
    assert r.status_code == 200, r.text
