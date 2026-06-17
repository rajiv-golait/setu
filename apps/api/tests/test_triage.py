"""Phase 6 F1 — triage engine tests.

The guardrail tests are the regulatory gate: the engine is deterministic, the
model never decides acuity, and no patient-facing message contains diagnosis or
drug language.
"""
from __future__ import annotations

import pytest

from app.db.models import Patient
from app.services.triage_service import (
    BANNED_PHRASES,
    RECOMMENDATION_TEXT,
    RULESET_VERSION,
    assess,
    message_for,
)

# --- Pure deterministic rule tests ---------------------------------------- #


def test_red_flag_symptom_is_high_emergency():
    d = assess(["chest pain"], age=40, existing_conditions=[])
    assert d.priority == "high"
    assert d.recommendation == "emergency"
    assert "red_flag_symptom" in d.matched_rules


def test_red_flag_wins_over_everything():
    # Even a young patient with no conditions: a red flag is always emergency.
    d = assess(["Severe Bleeding"], age=22, existing_conditions=[])
    assert (d.priority, d.recommendation) == ("high", "emergency")


def test_elevated_symptom_with_chronic_condition_is_medium():
    d = assess(["persistent fever"], age=45, existing_conditions=["diabetes"])
    assert d.priority == "medium"
    assert d.recommendation == "schedule_specialist"
    assert "elevated_symptom_with_chronic_condition" in d.matched_rules


def test_elevated_symptom_at_extreme_age_is_medium():
    assert assess(["vomiting"], age=80, existing_conditions=[]).priority == "medium"
    assert assess(["high fever"], age=0, existing_conditions=[]).priority == "medium"


def test_multiple_elevated_symptoms_is_medium():
    d = assess(["dizziness", "blurred vision"], age=30, existing_conditions=[])
    assert d.priority == "medium"


def test_benign_is_low_visit_phc():
    d = assess(["mild cold"], age=30, existing_conditions=[])
    assert d.priority == "low"
    assert d.recommendation == "visit_phc"
    assert "no_escalation_rule_matched" in d.matched_rules


def test_no_symptoms_is_low():
    d = assess([], age=None, existing_conditions=[])
    assert d.priority == "low"


def test_rationale_is_explainable_and_versioned():
    d = assess(["chest pain"], age=50, existing_conditions=[])
    r = d.rationale()
    assert r["engine_version"] == RULESET_VERSION
    assert r["matched_rules"] and r["factors"]


def test_assess_is_deterministic():
    a = assess(["persistent fever", "cough"], age=70, existing_conditions=["hypertension"])
    b = assess(["persistent fever", "cough"], age=70, existing_conditions=["hypertension"])
    assert (a.priority, a.recommendation, a.matched_rules) == (
        b.priority,
        b.recommendation,
        b.matched_rules,
    )


# --- Guardrail tests (regulatory) ----------------------------------------- #


def test_messages_never_contain_banned_phrases():
    for rec, table in RECOMMENDATION_TEXT.items():
        for lang in ("mr", "hi", "en"):
            msg = message_for(rec, lang).lower()
            for banned in BANNED_PHRASES:
                assert banned not in msg, f"{rec}/{lang} leaked banned phrase {banned!r}"


def test_message_is_localized_and_falls_back_to_english():
    assert message_for("emergency", "hi") == RECOMMENDATION_TEXT["emergency"]["hi"]
    # Unknown language → English fallback, never an error.
    assert message_for("visit_phc", "ta") == RECOMMENDATION_TEXT["visit_phc"]["en"]


# --- API integration tests ------------------------------------------------ #


async def _seed_patient(session_factory, patient_id: str, lang: str = "mr"):
    async with session_factory() as db:
        db.add(
            Patient(
                id=patient_id,
                display_name="Test",
                lang_pref=lang,
                patient_token=f"tok_{patient_id}",
            )
        )
        await db.commit()


@pytest.mark.asyncio
async def test_post_triage_persists_and_returns_dto(client, session_factory):
    pid = "pat_triage"
    await _seed_patient(session_factory, pid, lang="hi")

    r = await client.post(
        f"/api/v1/patients/{pid}/triage",
        json={"symptoms": ["chest pain"], "age": 55, "existing_conditions": []},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["priority"] == "high"
    assert body["recommendation"] == "emergency"
    assert body["engine_version"] == RULESET_VERSION
    assert body["lang"] == "hi"
    assert body["message"] == RECOMMENDATION_TEXT["emergency"]["hi"]
    assert "not a diagnosis" in body["disclaimer"].lower()
    assert body["rationale"]["matched_rules"]


@pytest.mark.asyncio
async def test_get_triage_history_latest_first(client, session_factory):
    pid = "pat_hist"
    await _seed_patient(session_factory, pid)

    await client.post(
        f"/api/v1/patients/{pid}/triage",
        json={"symptoms": ["mild cold"], "age": 30},
    )
    await client.post(
        f"/api/v1/patients/{pid}/triage",
        json={"symptoms": ["chest pain"], "age": 30},
    )

    r = await client.get(f"/api/v1/patients/{pid}/triage")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 2
    # Most recent (the emergency) is first.
    assert rows[0]["priority"] == "high"


@pytest.mark.asyncio
async def test_low_priority_routes_to_phc(client, session_factory):
    pid = "pat_low"
    await _seed_patient(session_factory, pid, lang="en")
    r = await client.post(
        f"/api/v1/patients/{pid}/triage",
        json={"symptoms": ["runny nose"], "age": 25},
    )
    body = r.json()
    assert body["priority"] == "low"
    assert body["recommendation"] == "visit_phc"
    assert body["message"] == RECOMMENDATION_TEXT["visit_phc"]["en"]
