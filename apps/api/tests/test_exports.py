"""Tests for FHIR and eSanjeevani export serializers (B8/B9)."""
from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.brief import (
    BriefLab,
    BriefMedication,
    BriefPriority,
    DoctorBriefDTO,
)
from app.services.esanjeewani_export import brief_to_esanjeewani_text
from app.services.fhir_export import brief_to_fhir_bundle


def _sample_brief() -> DoctorBriefDTO:
    return DoctorBriefDTO(
        brief_id="brf_test",
        patient_id="pat_test",
        generated_at=datetime.now(timezone.utc),
        model="test",
        one_line="Type 2 diabetes follow-up",
        chief_concern="Elevated HbA1c",
        active_medications=[
            BriefMedication(name="Metformin", dose="500mg", frequency="twice daily"),
        ],
        recent_labs=[
            BriefLab(test="HbA1c", value=8.2, unit="%", flag="high"),
        ],
        referral_reason="Uncontrolled sugars",
        specialist_type="Endocrinology",
        priority=BriefPriority(level="review_soon", reasons=["HbA1c above target"]),
        consult_room="setu-pat_test-brf_test",
    )


def test_fhir_bundle_shape():
    bundle = brief_to_fhir_bundle(_sample_brief(), patient_display="Ramesh")
    assert bundle["resourceType"] == "Bundle"
    types = {e["resource"]["resourceType"] for e in bundle["entry"]}
    assert "Patient" in types
    assert "Composition" in types
    assert "MedicationStatement" in types
    assert "Observation" in types


def test_esanjeewani_text_includes_referral():
    text = brief_to_esanjeewani_text(_sample_brief(), patient_label="Ramesh")
    assert "eSanjeevani" in text
    assert "Metformin" in text
    assert "Endocrinology" in text
    assert "not a diagnosis" in text.lower() or "Not a diagnosis" in text
