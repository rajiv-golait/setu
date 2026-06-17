"""DEMO_MODE short-circuits GET /memory and GET /brief to the seeded patient,
so any request returns the cached demo data instantly with no pipeline.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.config import settings
from app.db.models import Brief, CurrentTruth, Patient

pytestmark = pytest.mark.asyncio

SEED = settings.SEED_PATIENT_ID


async def _seed_demo(session_factory):
    async with session_factory() as db:
        db.add(Patient(id=SEED, display_name="Ramesh Shinde", lang_pref="mr", patient_token="tok_demo"))
        db.add(
            CurrentTruth(
                id="ct_demo1", patient_id=SEED, entry_type="lab_result",
                normalized_key="hba1c",
                value={"test_name": "HbA1c", "value": 9.1, "unit": "%", "trend": "up", "previous": 8.4},
                confidence=0.95, state="confirmed", source_claim_ids=[],
            )
        )
        db.add(
            Brief(
                id="brf_demo1", patient_id=SEED,
                brief_json={
                    "brief_id": "brf_demo1", "patient_id": SEED,
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "model": "mock", "one_line": "58M · T2DM + HTN", "chief_concern": "Review",
                    "active_medications": [], "recent_labs": [], "active_conditions": [],
                    "allergies": [], "timeline": [], "flags": [], "suggested_questions": [],
                    "source_documents": [], "confidence_notes": None,
                },
                model="mock", generated_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()


async def test_demo_mode_memory_serves_seed(client, session_factory, monkeypatch):
    await _seed_demo(session_factory)
    monkeypatch.setattr(settings, "DEMO_MODE", True)

    # Request a DIFFERENT (nonexistent) patient id — DEMO_MODE serves the seed.
    r = await client.get("/api/v1/patients/pat_anything/memory")
    assert r.status_code == 200, r.text
    assert r.json()["patient_id"] == SEED


async def test_demo_mode_brief_serves_seed(client, session_factory, monkeypatch):
    await _seed_demo(session_factory)
    monkeypatch.setattr(settings, "DEMO_MODE", True)

    r = await client.get("/api/v1/patients/pat_anything/brief")
    assert r.status_code == 200, r.text
    assert r.json()["patient_id"] == SEED
