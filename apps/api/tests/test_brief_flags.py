"""Brief engine: safety flags are computed by CODE, not the model."""
from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.brief import compute_flags, normalize_brief_content

THRESHOLD = 0.7


def truth(entries):
    return CurrentTruthDTO(patient_id="pat_x", entries=entries, generated_at=datetime.now(timezone.utc))


def test_abnormal_lab_flag_from_reference_range():
    e = CurrentTruthEntry(
        entry_type="lab_result", normalized_key="hba1c",
        value={"test_name": "HbA1c", "value": 7.8, "unit": "%", "reference_range": "4.0-5.6", "trend": "up", "history": []},
        confidence=0.95, state="confirmed", source_claim_ids=["l1"],
    )
    flags = compute_flags(truth([e]), THRESHOLD)
    assert any(f.type == "abnormal_lab" for f in flags)


def test_needs_review_flag_from_low_confidence():
    e = CurrentTruthEntry(
        entry_type="diagnosis", normalized_key="type_2_diabetes_mellitus",
        value={"condition": "Type 2 Diabetes Mellitus", "status": "active"},
        confidence=0.6, state="needs_review", source_claim_ids=["d1"],
    )
    flags = compute_flags(truth([e]), THRESHOLD)
    assert any(f.type == "needs_review" for f in flags)


def test_conflict_flag():
    e = CurrentTruthEntry(
        entry_type="diagnosis", normalized_key="hypertension",
        value={"conflict": True, "values": [{"condition": "HTN", "status": "active"}, {"condition": "HTN", "status": "resolved"}]},
        confidence=0.9, state="conflict", source_claim_ids=["d1", "d2"],
    )
    flags = compute_flags(truth([e]), THRESHOLD)
    assert any(f.type == "conflict" for f in flags)


def test_missing_data_flag():
    e = CurrentTruthEntry(
        entry_type="medication", normalized_key="metformin",
        value={"name": "Metformin"},  # missing dose + frequency
        confidence=0.95, state="confirmed", source_claim_ids=["c1"],
    )
    flags = compute_flags(truth([e]), THRESHOLD)
    assert any(f.type == "missing_data" for f in flags)


def test_clean_entry_no_flags():
    e = CurrentTruthEntry(
        entry_type="medication", normalized_key="metformin",
        value={"name": "Metformin", "dose": 500, "dose_unit": "mg", "frequency": "BD"},
        confidence=0.95, state="confirmed", source_claim_ids=["c1"],
    )
    flags = compute_flags(truth([e]), THRESHOLD)
    assert flags == []


def test_normalize_brief_content_coerces_string_medications():
    raw = {
        "one_line": "Dermatology follow-up",
        "chief_concern": "Acne management",
        "active_medications": [
            "Biodript Facewash",
            {"name": "Metformin", "dose": "500mg", "frequency": "BD"},
        ],
        "recent_labs": ["HbA1c 8.1%"],
        "active_conditions": "Type 2 diabetes",
        "allergies": "Sulfa drugs",
        "timeline": "2026-06-15: Lab draw",
        "suggested_questions": ["Adherence to topical regimen?"],
    }
    normalized = normalize_brief_content(raw)
    assert normalized["active_medications"][0] == {"name": "Biodript Facewash"}
    assert normalized["active_medications"][1]["name"] == "Metformin"
    assert normalized["recent_labs"][0] == {"test": "HbA1c 8.1%"}
    assert normalized["active_conditions"][0] == {"condition": "Type 2 diabetes"}
    assert normalized["allergies"][0] == {"substance": "Sulfa drugs"}
    assert normalized["timeline"][0] == {"date": "", "event": "2026-06-15: Lab draw"}
