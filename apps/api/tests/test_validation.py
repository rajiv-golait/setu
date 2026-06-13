"""Validation unit tests: plausibility ranges, required fields, abstain handling."""
from __future__ import annotations

from datetime import date

from app.schemas.claims import Claim
from app.services.validation import validate_claim

THRESHOLD = 0.7


def test_missing_required_field_flags_needs_review():
    # medication requires name, dose, dose_unit, frequency — omit frequency.
    claim = Claim(
        claim_id="c1", type="medication",
        fields={"name": "Metformin", "dose": 500, "dose_unit": "mg"},
        confidence=0.95, observed_at=date(2026, 6, 1),
    )
    validated, issues = validate_claim(claim, THRESHOLD)
    assert validated.needs_review is True
    assert any(i["code"] == "MISSING_FIELDS" for i in issues)


def test_implausible_lab_value_flagged():
    claim = Claim(
        claim_id="c1", type="lab_result",
        fields={"test_name": "HbA1c", "value": 99.0, "unit": "%"},  # way out of range
        confidence=0.95, observed_at=date(2026, 6, 1),
    )
    validated, issues = validate_claim(claim, THRESHOLD)
    assert validated.needs_review is True
    assert any(i["code"] == "IMPLAUSIBLE_VALUE" for i in issues)


def test_plausible_lab_value_not_flagged():
    claim = Claim(
        claim_id="c1", type="lab_result",
        fields={"test_name": "HbA1c", "value": 7.8, "unit": "%"},
        confidence=0.95, observed_at=date(2026, 6, 1),
    )
    validated, issues = validate_claim(claim, THRESHOLD)
    assert validated.needs_review is False
    assert issues == []


def test_low_confidence_gated():
    claim = Claim(
        claim_id="c1", type="diagnosis",
        fields={"condition": "T2DM", "status": "active"},
        confidence=0.5, observed_at=date(2026, 6, 1),
    )
    validated, issues = validate_claim(claim, THRESHOLD)
    assert validated.needs_review is True
    assert any(i["code"] == "LOW_CONFIDENCE" for i in issues)


def test_bad_diagnosis_status_flagged():
    claim = Claim(
        claim_id="c1", type="diagnosis",
        fields={"condition": "T2DM", "status": "maybe"},
        confidence=0.95, observed_at=date(2026, 6, 1),
    )
    validated, issues = validate_claim(claim, THRESHOLD)
    assert validated.needs_review is True
    assert any(i["code"] == "BAD_STATUS" for i in issues)


def test_implausible_dose_flagged():
    claim = Claim(
        claim_id="c1", type="medication",
        fields={"name": "Metformin", "dose": 999999, "dose_unit": "mg", "frequency": "BD"},
        confidence=0.95, observed_at=date(2026, 6, 1),
    )
    validated, issues = validate_claim(claim, THRESHOLD)
    assert validated.needs_review is True
    assert any(i["code"] == "IMPLAUSIBLE_DOSE" for i in issues)
