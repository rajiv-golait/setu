"""Deterministic priority flag — logistics only, not clinical triage."""
from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.priority import PRIORITY_DISCLAIMER, compute_priority


def _truth(entries: list[CurrentTruthEntry]) -> CurrentTruthDTO:
    return CurrentTruthDTO(
        patient_id="pat_x", entries=entries, generated_at=datetime.now(timezone.utc)
    )


def test_ramesh_profile_review_soon():
    entries = [
        CurrentTruthEntry(
            entry_type="lab_result",
            normalized_key="hba1c",
            value={
                "test_name": "HbA1c",
                "value": 9.1,
                "unit": "%",
                "flag": "high",
                "trend": "up",
                "previous": 8.4,
                "history": [],
            },
            confidence=0.95,
            state="confirmed",
            source_claim_ids=["l1"],
        ),
        CurrentTruthEntry(
            entry_type="vital",
            normalized_key="blood_pressure",
            value={"name": "Blood Pressure", "value": "142/88", "unit": "mmHg"},
            confidence=0.85,
            state="confirmed",
            source_claim_ids=["v1"],
        ),
    ]
    result = compute_priority(_truth(entries))
    assert result["level"] == "review_soon"
    assert any("HbA1c 9.1%" in r for r in result["reasons"])
    assert any("BP 142/88 (high)" in r for r in result["reasons"])


def test_single_abnormal_routine():
    entries = [
        CurrentTruthEntry(
            entry_type="lab_result",
            normalized_key="hba1c",
            value={
                "test_name": "HbA1c",
                "value": 6.0,
                "unit": "%",
                "flag": "high",
                "trend": "stable",
                "previous": 5.8,
                "history": [],
            },
            confidence=0.95,
            state="confirmed",
            source_claim_ids=["l1"],
        ),
    ]
    result = compute_priority(_truth(entries))
    assert result["level"] == "routine"
    assert len(result["reasons"]) == 1


def test_worsening_trend_alone_review_soon():
    entries = [
        CurrentTruthEntry(
            entry_type="lab_result",
            normalized_key="fbs",
            value={
                "test_name": "FBS",
                "value": 5.5,
                "unit": "mmol/L",
                "flag": "normal",
                "trend": "up",
                "previous": 5.0,
                "history": [],
            },
            confidence=0.95,
            state="confirmed",
            source_claim_ids=["l1"],
        ),
    ]
    result = compute_priority(_truth(entries))
    assert result["level"] == "review_soon"


def test_priority_disclaimer_is_non_clinical():
    assert "not a clinical assessment" in PRIORITY_DISCLAIMER.lower()
