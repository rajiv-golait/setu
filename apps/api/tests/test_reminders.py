"""B6 — Reminders engine. Deterministic, restate-only:
  - known notation (OD/BD/TDS/QID/HS, 1-0-1) expands to conventional times
  - food relation (AC/PC) is restated from the instruction
  - ambiguous/unparseable frequency -> needs_confirmation, NO invented times
  - refill_due only when BOTH duration and observed_at are present
"""
from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.reminders import build_reminders, medication_reminders


def _truth(entries) -> CurrentTruthDTO:
    return CurrentTruthDTO(patient_id="p", generated_at=datetime.now(timezone.utc), entries=entries)


def _med(name, freq, instructions=None, duration=None, observed_at=None, claim="clm_1", state="confirmed"):
    value = {"name": name, "dose": 500, "dose_unit": "mg", "frequency": freq}
    if instructions:
        value["instructions"] = instructions
    if duration:
        value["duration"] = duration
    if observed_at:
        value["observed_at"] = observed_at
    return CurrentTruthEntry(
        entry_type="medication", normalized_key=name.lower(), value=value,
        confidence=0.9, state=state, source_claim_ids=[claim],
    )


def test_bd_expands_to_morning_evening():
    [r] = medication_reminders(_truth([_med("Metformin", "BD")]))
    assert r["times_of_day"] == ["morning", "evening"]
    assert r["needs_confirmation"] is False
    assert r["source_claim_id"] == "clm_1"


def test_tds_and_qid_and_hs():
    rs = medication_reminders(_truth([
        _med("A", "TDS", claim="c1"),
        _med("B", "QID", claim="c2"),
        _med("C", "HS", claim="c3"),
    ]))
    by = {r["label"]: r["times_of_day"] for r in rs}
    assert by["A"] == ["morning", "afternoon", "evening"]
    assert by["B"] == ["morning", "afternoon", "evening", "night"]
    assert by["C"] == ["bedtime"]


def test_positional_notation():
    [r] = medication_reminders(_truth([_med("X", "1-0-1")]))
    assert r["times_of_day"] == ["morning", "evening"]
    assert r["needs_confirmation"] is False


def test_food_relation_is_restated():
    [r] = medication_reminders(_truth([_med("Y", "OD", instructions="take after food")]))
    assert r["relative_to_food"] == "after food"


def test_ambiguous_frequency_marks_confirmation_no_invented_times():
    # 'as needed' / SOS is not a fixed schedule -> we must NOT invent times.
    [r] = medication_reminders(_truth([_med("Z", "SOS as needed")]))
    assert r["needs_confirmation"] is True
    assert r["times_of_day"] == []  # nothing invented
    assert r["frequency_text"] == "SOS as needed"  # verbatim restatement


def test_missing_frequency_marks_confirmation():
    [r] = medication_reminders(_truth([_med("W", "")]))
    assert r["needs_confirmation"] is True
    assert r["times_of_day"] == []


def test_discontinued_med_produces_no_reminder():
    rs = medication_reminders(_truth([_med("Old", "BD", state="possibly_discontinued")]))
    assert rs == []


def test_refill_due_only_with_duration_and_observed():
    # Has both -> refill_due present.
    rs = build_reminders(_truth([_med("Metformin", "BD", duration="30 days", observed_at="2026-06-01")]))
    refills = [r for r in rs if r["type"] == "refill_due"]
    assert len(refills) == 1
    assert refills[0]["due_date"] == "2026-07-01"

    # Missing observed_at -> no refill reminder (never invented).
    rs2 = build_reminders(_truth([_med("Metformin", "BD", duration="30 days")]))
    assert [r for r in rs2 if r["type"] == "refill_due"] == []
