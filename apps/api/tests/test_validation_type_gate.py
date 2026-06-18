"""Type-gate tests: non-memory claim types (procedure, advice) are hard-rejected
before persist_claims(); valid-typed low-confidence claims are stored with
needs_review=True but never surfaced as confirmed in current_truth.
"""
from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from app.schemas.claims import Claim, ClaimsJSON
from app.services.memory.reducer import reduce
from app.services.validation import KNOWN_MEDICAL_TYPES, validate_claims

THRESHOLD = 0.7

_NOW = datetime(2026, 6, 18, tzinfo=timezone.utc)


def _make_claims_json(*claims: Claim) -> ClaimsJSON:
    return ClaimsJSON(
        document_id="doc_test",
        patient_id="pat_test",
        extracted_at=_NOW,
        provider="test",
        document_type="other",
        overall_confidence=0.9,
        claims=list(claims),
    )


# --- helpers ----------------------------------------------------------------

def _med(claim_id: str, name: str, confidence: float) -> Claim:
    return Claim(
        claim_id=claim_id,
        type="medication",
        fields={"name": name, "dose": 500, "dose_unit": "mg", "frequency": "BD"},
        confidence=confidence,
        observed_at=date(2026, 6, 1),
    )


def _procedure(claim_id: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        type="procedure",
        fields={"name": "config.toml injection"},
        confidence=0.95,
        observed_at=date(2026, 6, 1),
    )


def _advice(claim_id: str) -> Claim:
    return Claim(
        claim_id=claim_id,
        type="advice",
        fields={"text": "mcp.servers random extracted string"},
        confidence=0.95,
        observed_at=date(2026, 6, 1),
    )


# --- tests ------------------------------------------------------------------

def test_known_medical_types_set():
    """Sanity: KNOWN_MEDICAL_TYPES contains exactly the memory-meaningful types."""
    assert KNOWN_MEDICAL_TYPES == {"medication", "diagnosis", "allergy", "lab_result", "vital"}


def test_junk_types_are_rejected():
    """procedure and advice claims are hard-rejected — never appear in result.claims."""
    payload = _make_claims_json(
        _med("c1", "Metformin", 0.95),
        _procedure("c2"),
        _advice("c3"),
    )
    result = validate_claims(payload, THRESHOLD)

    claim_ids = {c.claim_id for c in result.claims}
    assert "c2" not in claim_ids, "procedure claim must not reach persist_claims()"
    assert "c3" not in claim_ids, "advice claim must not reach persist_claims()"

    rejected_ids = {r["claim_id"] for r in result.rejected}
    assert "c2" in rejected_ids
    assert "c3" in rejected_ids
    assert all(r["code"] == "UNKNOWN_TYPE" for r in result.rejected)


def test_valid_medical_claim_passes_through():
    """A high-confidence medical claim is not rejected and has needs_review=False."""
    payload = _make_claims_json(_med("c1", "Metformin", 0.95))
    result = validate_claims(payload, THRESHOLD)

    assert len(result.claims) == 1
    assert result.claims[0].claim_id == "c1"
    assert result.claims[0].needs_review is False
    assert result.rejected == []


def test_low_confidence_valid_type_stored_as_needs_review():
    """A real medical type below threshold lands in result.claims with needs_review=True
    (goes to review queue, not silently into current_truth as confirmed)."""
    payload = _make_claims_json(_med("c1", "Metformin", 0.4))
    result = validate_claims(payload, THRESHOLD)

    assert len(result.claims) == 1
    assert result.claims[0].needs_review is True
    assert any(i["code"] == "LOW_CONFIDENCE" for i in result.issues)


def test_junk_never_appears_in_current_truth():
    """End-to-end gate: junk types, even if they somehow slipped into result.claims,
    would be skipped by the reducer — but they never reach result.claims at all."""
    payload = _make_claims_json(
        _med("c1", "Metformin", 0.95),
        _procedure("c2"),
        _advice("c3"),
    )
    result = validate_claims(payload, THRESHOLD)

    # Only the medication survives; pass it to the reducer.
    truth_entries = reduce(result.claims, confidence_threshold=THRESHOLD)

    entry_types = {e.entry_type for e in truth_entries}
    assert "procedure" not in entry_types
    assert "advice" not in entry_types
    assert "medication" in entry_types


def test_low_confidence_claim_not_confirmed_in_current_truth():
    """A low-confidence (needs_review) medication is stored but the reducer
    marks it needs_review — never surfaced as 'confirmed'."""
    payload = _make_claims_json(_med("c1", "Metformin", 0.4))
    result = validate_claims(payload, THRESHOLD)

    truth_entries = reduce(result.claims, confidence_threshold=THRESHOLD)

    assert len(truth_entries) == 1
    assert truth_entries[0].state == "needs_review"
    assert truth_entries[0].state != "confirmed"
