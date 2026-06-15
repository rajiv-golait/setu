"""Canonical seeded claim data for the demo patient (T2DM + HTN profile).

Single source of truth, reused by:
  - the mock extractor (so a mock upload yields a realistic Claims JSON)
  - the seed script (so `make seed` produces the same demo patient)
  - the DEMO_MODE cached paths (telegram + webchat) via SEEDED_EXPLANATION

The patient is Ramesh Shinde (58M, T2D + HTN, Ahmednagar); the bot operator is
his son Akash (the caregiver). The shape mirrors Claims JSON. observed_at uses
ISO date strings; two HbA1c readings on different dates (8.4% -> 9.1%) give the
reducer a real upward trend — the demo moment. The diagnosis claim is
deliberately low-confidence to exercise the needs_review path.

IDs are intentionally NOT renamed (pat_demo / tok_demo / shr_demo_token): they
are referenced by config defaults, e2e tests, and the contract test.
"""
from __future__ import annotations

DEMO_PATIENT_ID = "pat_demo"
DEMO_PATIENT_TOKEN = "tok_demo"
DEMO_SHARE_TOKEN = "shr_demo_token"
DEMO_CHAT_ID = "demo_chat_id"
DEMO_DISPLAY_NAME = "Ramesh Shinde"

# Cached Marathi explanation returned by the DEMO_MODE paths (Path A / Path B).
SEEDED_EXPLANATION = (
    "तुमची साखर (HbA1c) ९.१% आहे — मागच्या वेळेपेक्षा (८.४%) वाढली आहे. "
    "रक्तदाब देखील थोडा जास्त आहे. Metformin आणि Amlodipine सुरू आहेत. "
    "कृपया लवकरात लवकर डॉक्टरांशी बोला. "
    "हे तुमच्या कागदाचे स्पष्टीकरण आहे, वैद्यकीय सल्ला नाही."
)

# Forced one_line for the seeded brief (the brief engine's prose is overridden
# in the seed script so the demo headline is exact and stable).
SEEDED_ONE_LINE = "58M · T2DM + HTN · HbA1c 9.1% ↑ (was 8.4%) · Ahmednagar"

# Bridge demo: local GP → specialist referral context (seed overrides).
SEEDED_REFERRED_BY = "Dr. Kulkarni (GP, Ahmednagar)"
SEEDED_REFERRAL_REASON = "Worsening glycaemic control — specialist review"
SEEDED_SPECIALIST_TYPE = "Endocrinologist"
SEEDED_PRIORITY = {
    "level": "review_soon",
    "reasons": [
        "HbA1c 9.1% (high, ↑ from 8.4%)",
        "BP 142/88 (high)",
    ],
}

# Telegram brief-link handoff message (caregiver → specialist).
BRIEF_HANDOFF_MSG = "तुमचा रिपोर्ट तयार आहे. हा specialist डॉक्टरांना पाठवा: {url}"

# Two lab dates: 3 months ago (baseline) and today (the new report).
DATE_OLD = "2026-03-15"
DATE_NEW = "2026-06-15"

# Three documents.
DEMO_DOCUMENTS = [
    {"id": "doc_rx01", "doc_type": "prescription", "mime": "image/jpeg"},
    {"id": "doc_lab1", "doc_type": "lab_report", "mime": "application/pdf"},
    {"id": "doc_disc", "doc_type": "discharge_summary", "mime": "application/pdf"},
]


def demo_claims(patient_id: str = DEMO_PATIENT_ID) -> list[dict]:
    """Richer T2DM/HTN profile.

    Medications: Metformin 500 BD, Amlodipine 5 OD, Atorvastatin 10 OD.
    Labs across two dates: HbA1c 8.4 -> 9.1 (trend), FBS 7.2 -> 7.8 (trend),
    BP 142/88 (baseline), eGFR 72 (today, normal — kidney safety context).
    Diagnoses: T2DM (low-conf -> needs_review), Hypertension.
    Allergy: Sulfa drugs.
    """
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
                "duration": "90 days", "instructions": "after food",
            },
            "confidence": 0.91,
            "observed_at": DATE_NEW,
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
                "duration": "90 days", "instructions": "morning",
            },
            "confidence": 0.88,
            "observed_at": DATE_NEW,
            "needs_review": False,
        },
        {
            "claim_id": "clm_med3",
            "document_id": "doc_rx01",
            "type": "medication",
            "fields": {
                "name": "Atorvastatin", "generic": "atorvastatin",
                "dose": 10, "dose_unit": "mg",
                "frequency": "OD", "route": "oral",
                "duration": "90 days", "instructions": "at night",
            },
            "confidence": 0.87,
            "observed_at": DATE_NEW,
            "needs_review": False,
        },
        # --- lab results: HbA1c x2 (8.4 -> 9.1, the demo trend) ---
        {
            "claim_id": "clm_lab1",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "HbA1c", "value": 8.4, "unit": "%",
                "reference_range": "4.0-5.6", "flag": "high",
            },
            "confidence": 0.96,
            "observed_at": DATE_OLD,
            "needs_review": False,
        },
        {
            "claim_id": "clm_lab2",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "HbA1c", "value": 9.1, "unit": "%",
                "reference_range": "4.0-5.6", "flag": "high",
            },
            "confidence": 0.95,
            "observed_at": DATE_NEW,
            "needs_review": False,
        },
        # --- FBS x2 (7.2 -> 7.8) ---
        {
            "claim_id": "clm_lab3",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "FBS", "value": 7.2, "unit": "mmol/L",
                "reference_range": "3.9-5.6", "flag": "high",
            },
            "confidence": 0.93,
            "observed_at": DATE_OLD,
            "needs_review": False,
        },
        {
            "claim_id": "clm_lab4",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "FBS", "value": 7.8, "unit": "mmol/L",
                "reference_range": "3.9-5.6", "flag": "high",
            },
            "confidence": 0.92,
            "observed_at": DATE_NEW,
            "needs_review": False,
        },
        # --- eGFR (today, normal — kidney safety context) ---
        {
            "claim_id": "clm_lab5",
            "document_id": "doc_lab1",
            "type": "lab_result",
            "fields": {
                "test_name": "eGFR", "value": 72, "unit": "mL/min",
                "reference_range": ">60", "flag": "normal",
            },
            "confidence": 0.94,
            "observed_at": DATE_NEW,
            "needs_review": False,
        },
        # --- diagnoses ---
        {
            "claim_id": "clm_dx01",
            "document_id": "doc_disc",
            "type": "diagnosis",
            "fields": {"condition": "Type 2 Diabetes Mellitus", "status": "active"},
            "confidence": 0.6,  # deliberately low -> needs_review path
            "observed_at": DATE_OLD,
            "needs_review": True,
        },
        {
            "claim_id": "clm_dx02",
            "document_id": "doc_disc",
            "type": "diagnosis",
            "fields": {"condition": "Hypertension", "status": "active"},
            "confidence": 0.85,
            "observed_at": DATE_OLD,
            "needs_review": False,
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
        # --- vital (BP, baseline) ---
        {
            "claim_id": "clm_vit1",
            "document_id": "doc_disc",
            "type": "vital",
            "fields": {"name": "Blood Pressure", "value": "142/88", "unit": "mmHg"},
            "confidence": 0.85,
            "observed_at": DATE_OLD,
            "needs_review": False,
        },
    ]
