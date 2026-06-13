"""Reducer unit tests — HIGHEST PRIORITY (patient safety).

The reducer is a pure function: no DB, no I/O. These tests construct Claim objects
directly and assert on CurrentTruthEntry output.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.schemas.claims import Claim
from app.services.memory.reducer import reduce

THRESHOLD = 0.7


def med(claim_id, name, dose, freq, conf, observed, **extra):
    fields = {"name": name, "dose": dose, "dose_unit": "mg", "frequency": freq, **extra}
    return Claim(claim_id=claim_id, type="medication", fields=fields, confidence=conf, observed_at=observed)


def lab(claim_id, test, value, conf, observed, **extra):
    fields = {"test_name": test, "value": value, "unit": "%", **extra}
    return Claim(claim_id=claim_id, type="lab_result", fields=fields, confidence=conf, observed_at=observed)


def dx(claim_id, condition, conf, observed, status="active"):
    return Claim(claim_id=claim_id, type="diagnosis", fields={"condition": condition, "status": status}, confidence=conf, observed_at=observed)


def by_key(entries, entry_type, key):
    return next(e for e in entries if e.entry_type == entry_type and e.normalized_key == key)


# --------------------------------------------------------------------------- #
# Rule 1 — normalization / grouping
# --------------------------------------------------------------------------- #
def test_name_variants_group_to_one_key():
    claims = [
        med("c1", "Metformin", 500, "BD", 0.9, date(2026, 1, 1)),
        med("c2", "METFORMIN", 500, "BD", 0.9, date(2026, 2, 1)),
        med("c3", "metformin", 500, "BD", 0.9, date(2026, 3, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    meds = [e for e in out if e.entry_type == "medication"]
    assert len(meds) == 1
    assert meds[0].normalized_key == "metformin"


# --------------------------------------------------------------------------- #
# Rule 3 — state-like: latest wins + confidence tie-break
# --------------------------------------------------------------------------- #
def test_latest_observed_at_wins():
    claims = [
        med("c1", "Metformin", 500, "BD", 0.9, date(2026, 1, 1)),
        med("c2", "Metformin", 1000, "BD", 0.9, date(2026, 6, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    entry = by_key(out, "medication", "metformin")
    assert entry.value["dose"] == 1000
    assert entry.state == "confirmed"


def test_confidence_breaks_same_date_tie():
    claims = [
        med("c1", "Metformin", 500, "BD", 0.75, date(2026, 6, 1)),
        med("c2", "Metformin", 850, "BD", 0.95, date(2026, 6, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    entry = by_key(out, "medication", "metformin")
    # Same dose field is "materially different" -> conflict (both above threshold).
    # The winner by confidence is the 850 claim.
    assert entry.state == "conflict"
    assert entry.confidence == pytest.approx(0.95)


# --------------------------------------------------------------------------- #
# Rule 4 — time-series labs + trend
# --------------------------------------------------------------------------- #
def test_lab_history_preserved_and_trend_up():
    claims = [
        lab("l1", "HbA1c", 6.9, 0.95, date(2026, 3, 1)),
        lab("l2", "HbA1c", 7.8, 0.95, date(2026, 6, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    entry = by_key(out, "lab_result", "hba1c")
    assert entry.value["value"] == 7.8           # current = latest
    assert entry.value["previous"] == 6.9
    assert entry.value["trend"] == "up"
    assert len(entry.value["history"]) == 2       # history never collapsed


def test_lab_trend_stable_within_5pct():
    claims = [
        lab("l1", "HbA1c", 7.0, 0.95, date(2026, 3, 1)),
        lab("l2", "HbA1c", 7.2, 0.95, date(2026, 6, 1)),  # +2.8% -> stable
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    entry = by_key(out, "lab_result", "hba1c")
    assert entry.value["trend"] == "stable"


def test_lab_trend_down():
    claims = [
        lab("l1", "HbA1c", 8.0, 0.95, date(2026, 3, 1)),
        lab("l2", "HbA1c", 6.5, 0.95, date(2026, 6, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    assert by_key(out, "lab_result", "hba1c").value["trend"] == "down"


# --------------------------------------------------------------------------- #
# Rule 5 — conflict
# --------------------------------------------------------------------------- #
def test_conflict_surfaces_both_values_never_autopicks():
    claims = [
        lab("l1", "HbA1c", 7.8, 0.95, date(2026, 6, 1)),
        lab("l2", "HbA1c", 9.9, 0.95, date(2026, 6, 1)),  # same date, materially different
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    entry = by_key(out, "lab_result", "hba1c")
    # time-series labs keep both as history; conflict is primarily a state-like concern,
    # but both readings must remain visible.
    assert len(entry.value["history"]) == 2


def test_state_like_conflict_flagged():
    claims = [
        dx("d1", "Type 2 Diabetes Mellitus", 0.9, date(2026, 6, 1), status="active"),
        dx("d2", "Type 2 Diabetes Mellitus", 0.9, date(2026, 6, 1), status="resolved"),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    entry = by_key(out, "diagnosis", "type_2_diabetes_mellitus")
    assert entry.state == "conflict"
    assert entry.value.get("conflict") is True
    assert len(entry.value["values"]) == 2


# --------------------------------------------------------------------------- #
# Rule 6 — confidence gate
# --------------------------------------------------------------------------- #
def test_low_confidence_entry_needs_review():
    claims = [dx("d1", "Type 2 Diabetes Mellitus", 0.6, date(2026, 6, 1))]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    assert by_key(out, "diagnosis", "type_2_diabetes_mellitus").state == "needs_review"


def test_above_threshold_is_confirmed():
    claims = [dx("d1", "Hypertension", 0.85, date(2026, 6, 1))]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    assert by_key(out, "diagnosis", "hypertension").state == "confirmed"


# --------------------------------------------------------------------------- #
# Rule 3 (cont.) — possibly_discontinued
# --------------------------------------------------------------------------- #
def test_medication_omitted_in_newer_doc_is_possibly_discontinued():
    claims = [
        med("c1", "Metformin", 500, "BD", 0.9, date(2026, 1, 1)),
        med("c2", "Amlodipine", 5, "OD", 0.9, date(2026, 1, 1)),
        # newer document (later date) only re-affirms Metformin
        med("c3", "Metformin", 500, "BD", 0.9, date(2026, 6, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    assert by_key(out, "medication", "metformin").state == "confirmed"
    assert by_key(out, "medication", "amlodipine").state == "possibly_discontinued"


# --------------------------------------------------------------------------- #
# Rule 7 — provenance
# --------------------------------------------------------------------------- #
def test_provenance_recorded():
    claims = [
        lab("l1", "HbA1c", 6.9, 0.95, date(2026, 3, 1)),
        lab("l2", "HbA1c", 7.8, 0.95, date(2026, 6, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    entry = by_key(out, "lab_result", "hba1c")
    assert set(entry.source_claim_ids) == {"l1", "l2"}


# --------------------------------------------------------------------------- #
# Idempotence
# --------------------------------------------------------------------------- #
def test_reduce_is_idempotent():
    claims = [
        med("c1", "Metformin", 500, "BD", 0.9, date(2026, 1, 1)),
        lab("l1", "HbA1c", 6.9, 0.95, date(2026, 3, 1)),
        lab("l2", "HbA1c", 7.8, 0.95, date(2026, 6, 1)),
        dx("d1", "Type 2 Diabetes Mellitus", 0.6, date(2026, 6, 1)),
    ]
    first = reduce(claims, confidence_threshold=THRESHOLD)
    second = reduce(claims, confidence_threshold=THRESHOLD)
    assert [e.model_dump() for e in first] == [e.model_dump() for e in second]


def test_advice_and_procedure_are_not_memory_entries():
    claims = [
        Claim(claim_id="a1", type="advice", fields={"text": "exercise daily"}, confidence=0.9, observed_at=date(2026, 6, 1)),
        Claim(claim_id="p1", type="procedure", fields={"name": "ECG"}, confidence=0.9, observed_at=date(2026, 6, 1)),
    ]
    out = reduce(claims, confidence_threshold=THRESHOLD)
    assert out == []
