"""Phase 6 F6 — admin analytics aggregates (no PII)."""
from __future__ import annotations

import jwt
import pytest

from app.db.models import Appointment, Patient, TriageResult
from app.ids import new_id

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


async def _seed_analytics_data(session_factory):
    async with session_factory() as db:
        db.add(
            Patient(
                id="pat_rural",
                display_name="Rural",
                lang_pref="mr",
                patient_token="tok_r",
                is_rural=True,
            )
        )
        db.add(
            Patient(
                id="pat_urban",
                display_name="Urban",
                lang_pref="en",
                patient_token="tok_u",
                is_rural=False,
            )
        )
        db.add(
            Appointment(
                id=new_id("apt"),
                patient_id="pat_rural",
                specialty="general",
                status="completed",
            )
        )
        db.add(
            TriageResult(
                id=new_id("trg"),
                patient_id="pat_urban",
                inputs={},
                priority="high",
                recommendation="urgent_care",
                rationale="test",
                message="msg",
                lang="en",
                engine_version="1",
                created_by="patient",
            )
        )
        await db.commit()


async def test_admin_analytics_overview(client, session_factory, auth_enabled):
    await _seed_analytics_data(session_factory)
    r = await client.get(
        "/api/v1/admin/analytics/overview",
        headers=_bearer(_token("u_admin", "admin")),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_patients"] == 2
    assert body["rural_patients"] == 1
    assert body["consultations_completed"] == 1
    assert body["high_priority_triage"] == 1
    assert "display_name" not in str(body)
    langs = {x["lang_pref"]: x["count"] for x in body["languages"]}
    assert langs.get("mr") == 1
    assert langs.get("en") == 1


async def test_non_admin_rejected(client, auth_enabled):
    r = await client.get(
        "/api/v1/admin/analytics/overview",
        headers=_bearer(_token("u_pat", "patient")),
    )
    assert r.status_code == 403, r.text
