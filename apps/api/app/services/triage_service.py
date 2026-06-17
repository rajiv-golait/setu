"""Phase 6 F1 — NON-DIAGNOSTIC AI-assisted triage.

SaMD-safe design, mirroring services/priority.py:

  * `assess()` is PURE and DETERMINISTIC. A fixed rules table maps the inputs
    (symptoms, age, existing conditions) to a priority band (low|medium|high)
    and a routing recommendation (visit_phc | schedule_specialist | emergency).
    No model is involved. The rationale lists the matched rule ids, so every
    decision is explainable and auditable.

  * `message_for()` returns a fixed, localized restatement of the already-decided
    recommendation from a static table. There is intentionally NO model in the
    patient-facing routing text — the recommendation is a closed set of three
    safe strings, so a model would only add risk (diagnosis/drug language)
    without adding value. A banned-phrase guard remains as defence in depth.

The model never decides acuity, names a disease, predicts a condition, or
suggests a medicine. The output is care ROUTING, not medicine.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

logger = logging.getLogger("setu.triage")

RULESET_VERSION = "triage-rules-v1"

# --- Deterministic rule inputs -------------------------------------------- #

# Red-flag symptoms → always HIGH / emergency routing. Normalized to snake_case
# tokens; the router normalizes free text before calling assess().
RED_FLAG_SYMPTOMS = frozenset(
    {
        "chest_pain",
        "breathlessness",
        "shortness_of_breath",
        "unconscious",
        "fainting",
        "severe_bleeding",
        "stroke_signs",
        "slurred_speech",
        "face_drooping",
        "blue_lips",
        "seizure",
        "severe_abdominal_pain",
        "stiff_neck_with_fever",
        "poisoning",
        "severe_burn",
    }
)

# Symptoms that, combined with a chronic condition or extreme age, escalate to
# MEDIUM / specialist routing (but are NOT emergencies on their own).
ELEVATED_SYMPTOMS = frozenset(
    {
        "persistent_fever",
        "high_fever",
        "persistent_cough",
        "blood_in_urine",
        "blood_in_stool",
        "severe_headache",
        "vomiting",
        "dizziness",
        "swelling",
        "blurred_vision",
        "numbness",
    }
)

# Chronic conditions that lower the escalation threshold.
CHRONIC_CONDITIONS = frozenset(
    {
        "diabetes",
        "hypertension",
        "heart_disease",
        "asthma",
        "copd",
        "kidney_disease",
        "ckd",
        "pregnancy",
        "cancer",
        "immunocompromised",
    }
)

ELDERLY_AGE = 65
INFANT_AGE = 1


@dataclass(frozen=True)
class TriageDecision:
    priority: str  # low|medium|high
    recommendation: str  # visit_phc|schedule_specialist|emergency
    matched_rules: list[str] = field(default_factory=list)
    factors: list[str] = field(default_factory=list)

    def rationale(self) -> dict:
        return {
            "engine_version": RULESET_VERSION,
            "matched_rules": list(self.matched_rules),
            "factors": list(self.factors),
        }


def normalize_token(text: str) -> str:
    """Canonicalize a free-text symptom/condition to a snake_case token."""
    return "_".join(text.strip().lower().split())


def assess(
    symptoms: list[str],
    age: int | None = None,
    existing_conditions: list[str] | None = None,
) -> TriageDecision:
    """Deterministic, model-free routing decision.

    Order matters: emergency rules win, then elevation rules, else benign.
    Returns a TriageDecision whose rationale lists every matched rule id.
    """
    sym = {normalize_token(s) for s in symptoms if s and s.strip()}
    cond = {normalize_token(c) for c in (existing_conditions or []) if c and c.strip()}

    matched: list[str] = []
    factors: list[str] = []

    # --- Rule 1: red-flag symptom → HIGH / emergency --------------------- #
    red = sorted(sym & RED_FLAG_SYMPTOMS)
    if red:
        matched.append("red_flag_symptom")
        factors.append(f"red-flag symptom(s): {', '.join(red)}")
        return TriageDecision(
            priority="high",
            recommendation="emergency",
            matched_rules=matched,
            factors=factors,
        )

    # --- Rule 2: elevation → MEDIUM / schedule_specialist ---------------- #
    elevated = sorted(sym & ELEVATED_SYMPTOMS)
    chronic = sorted(cond & CHRONIC_CONDITIONS)

    if elevated and chronic:
        matched.append("elevated_symptom_with_chronic_condition")
        factors.append(f"symptom(s) {', '.join(elevated)} with condition(s) {', '.join(chronic)}")
    elif elevated and age is not None and (age >= ELDERLY_AGE or age <= INFANT_AGE):
        matched.append("elevated_symptom_at_extreme_age")
        factors.append(f"symptom(s) {', '.join(elevated)} at age {age}")
    elif len(elevated) >= 2:
        matched.append("multiple_elevated_symptoms")
        factors.append(f"multiple symptom(s): {', '.join(elevated)}")
    elif chronic and sym:
        matched.append("symptom_with_chronic_condition")
        factors.append(f"symptom present with chronic condition(s) {', '.join(chronic)}")

    if matched:
        return TriageDecision(
            priority="medium",
            recommendation="schedule_specialist",
            matched_rules=matched,
            factors=factors,
        )

    # --- Rule 3: benign → LOW / visit_phc -------------------------------- #
    matched.append("no_escalation_rule_matched")
    factors.append("no red-flag or elevation criteria met")
    return TriageDecision(
        priority="low",
        recommendation="visit_phc",
        matched_rules=matched,
        factors=factors,
    )


# --- Localized phrasing (model rephrases the fixed recommendation only) ---- #

# Static, safe fallback per (recommendation, lang). Used when the reasoner is
# unavailable or returns unsafe text. These never mention a disease or medicine.
RECOMMENDATION_TEXT = {
    "visit_phc": {
        "mr": "जवळच्या प्राथमिक आरोग्य केंद्रात (PHC) तपासणी करा.",
        "hi": "नज़दीकी प्राथमिक स्वास्थ्य केंद्र (PHC) पर जाँच कराएँ।",
        "en": "Please visit your nearest Primary Health Centre (PHC) for a check-up.",
    },
    "schedule_specialist": {
        "mr": "तज्ज्ञ डॉक्टरांचा सल्ला ठरवा.",
        "hi": "विशेषज्ञ डॉक्टर से परामर्श का समय तय करें।",
        "en": "Please schedule a consultation with a specialist.",
    },
    "emergency": {
        "mr": "तातडीने वैद्यकीय मदत घ्या — जवळच्या रुग्णालयात जा किंवा आपत्कालीन सेवेला कॉल करा.",
        "hi": "तुरंत आपातकालीन चिकित्सा सहायता लें — नज़दीकी अस्पताल जाएँ या आपातकालीन सेवा को कॉल करें।",
        "en": "Seek emergency medical care now — go to the nearest hospital or call emergency services.",
    },
}

# Reuse the same banned-phrase posture as services/explanation.py: nothing that
# suggests diagnosis or a medicine change may reach the patient.
BANNED_PHRASES = (
    "you have",
    "diagnos",
    "disease",
    "infection is",
    "take medicine",
    "take this drug",
    "prescrib",
    "dose",
    "tablet",
    "antibiotic",
)


def _contains_banned(text: str) -> bool:
    low = text.lower()
    return any(phrase in low for phrase in BANNED_PHRASES)


def message_for(recommendation: str, lang: str) -> str:
    """Localized restatement of the FIXED recommendation. No model involved.

    The recommendation is one of three closed values, each mapped to a static,
    safe string per language. A banned-phrase assertion guards against future
    edits accidentally introducing diagnosis/drug language.
    """
    table = RECOMMENDATION_TEXT.get(recommendation, RECOMMENDATION_TEXT["visit_phc"])
    text = table.get(lang, table["en"])
    if _contains_banned(text):  # pragma: no cover — defence in depth on the static table
        logger.error("triage recommendation text tripped banned-phrase guard: %r", text)
        return table["en"]
    return text
