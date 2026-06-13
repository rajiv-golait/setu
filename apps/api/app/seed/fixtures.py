"""Canonical seeded claim data for the demo patient (T2DM/HTN profile).

Single source of truth, reused by:
  - the mock extractor (so a mock upload yields a realistic Claims JSON)
  - the seed script (so `make seed` produces the same demo patient)

The shape mirrors Claims JSON. observed_at uses ISO date strings; two HbA1c
readings on different dates give the reducer a real trend; the diagnosis claim
is deliberately low-confidence to exercise the needs_review path.
"""
from __future__ import annotations

DEMO_PATIENT_ID = "pat_demo"
DEMO_PATIENT_TOKEN = "tok_demo"
DEMO_SHARE_TOKEN = "shr_demo_token"

# Three documents.
DEMO_DOCUMENTS = [
    {"id": "doc_rx01", "doc_type": "prescription", "mime": "image/jpeg"},
    {"id": "doc_lab1", "doc_type": "lab_report", "mime": "application/pdf"},
    {"id": "doc_disc", "doc_type": "discharge_summary", "mime": "application/pdf"},
]


def demo_claims(patient_id: str = DEMO_PATIENT_ID) -> list[dict]:
    """~8 claims: 2 meds, 3 labs (HbA1c x2 for trend + creatinine), 1 dx, 1 allergy, 1 vital."""
    return [
        # --- medications (from prescription) ---
        {
            "claim_id": "clm_med1",
            "document_id": "doc_rx01",
            "type": "medication",
            "fields": {
                "name": "Metformin", "generic": "metformin",
                "dose": 500, "dose_unit": "mg",
                "frequency": "BD", "route": "oral",
                "duration": "30 days", "instructions": "after food",
            },
            "confidence": 0.91,
            "observed_at": "2026-06-18",
            "needs_review": False,
        },
        {
            "claim_id": "clm_med2",
            "document_id": "doc_rx01",
            "type": "medication",
            "fields": {
                "name": "Amlodipine", "generic": "amlodipine",
                "dose": 5, "dose_unit": "mg",
                "frequency": "OD", "route": "oral",
                "duration": "30 days", "instructions": "morning",
            },
            "confidence": 0.88,
            "observed_at": "2026-06-18",
            "needs_review": False,
        },
        # --- lab results (HbA1c x2 across dates for trend) ---
        {
            "claim_id": "clm_lab1",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "HbA1c", "value": 6.9, "unit": "%",
                "reference_range": "4.0-5.6", "flag": "high",
            },
            "confidence": 0.96,
            "observed_at": "2026-03-12",
            "needs_review": False,
        },
        {
            "claim_id": "clm_lab2",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "HbA1c", "value": 7.8, "unit": "%",
                "reference_range": "4.0-5.6", "flag": "high",
            },
            "confidence": 0.95,
            "observed_at": "2026-06-15",
            "needs_review": False,
        },
        {
            "claim_id": "clm_lab3",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "Creatinine", "value": 0.9, "unit": "mg/dL",
                "reference_range": "0.6-1.2", "flag": "normal",
            },
            "confidence": 0.93,
            "observed_at": "2026-06-15",
            "needs_review": False,
        },
        # --- diagnosis (deliberately low-confidence -> needs_review) ---
        {
            "claim_id": "clm_dx01",
            "document_id": "doc_disc",
            "type": "diagnosis",
            "fields": {"condition": "Type 2 Diabetes Mellitus", "status": "active"},
            "confidence": 0.6,
            "observed_at": "2026-06-18",
            "needs_review": True,
        },
        # --- allergy ---
        {
            "claim_id": "clm_alg1",
            "document_id": "doc_disc",
            "type": "allergy",
            "fields": {"substance": "Sulfa drugs", "reaction": "rash", "severity": "moderate"},
            "confidence": 0.9,
            "observed_at": "2024-01-10",
            "needs_review": False,
        },
        # --- vital ---
        {
            "claim_id": "clm_vit1",
            "document_id": "doc_disc",
            "type": "vital",
            "fields": {"name": "Blood Pressure", "value": "148/92", "unit": "mmHg"},
            "confidence": 0.85,
            "observed_at": "2026-06-18",
            "needs_review": False,
        },
    ]
