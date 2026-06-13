"""Name normalization — maps drug/test/condition variants to a canonical key.

Pure, dependency-free string logic. Deterministic. Used by the reducer to group
claims, and by ingestion to set claims.normalized_key.

The map is intentionally small + curated for the demo profile (T2DM/HTN). The
fall-through behaviour (lowercase + strip non-alphanumerics) is what makes
'Metformin', 'METFORMIN', 'metformin' all collapse to 'metformin' without an
explicit entry.
"""
from __future__ import annotations

import re

# Curated aliases. Keys are the *normalized form of the alias*, values the canonical key.
_ALIASES: dict[str, str] = {
    # Medications
    "metformin": "metformin",
    "glucophage": "metformin",
    "amlodipine": "amlodipine",
    "amlong": "amlodipine",
    "telmisartan": "telmisartan",
    "atorvastatin": "atorvastatin",
    "atorva": "atorvastatin",
    "glimepiride": "glimepiride",
    # Lab tests
    "hba1c": "hba1c",
    "hb a1c": "hba1c",
    "glycatedhemoglobin": "hba1c",
    "glycosylatedhemoglobin": "hba1c",
    "fbs": "fasting_blood_sugar",
    "fastingbloodsugar": "fasting_blood_sugar",
    "ppbs": "postprandial_blood_sugar",
    "creatinine": "creatinine",
    "serumcreatinine": "creatinine",
    "ldl": "ldl_cholesterol",
    "ldlcholesterol": "ldl_cholesterol",
    "egfr": "egfr",
    # Conditions
    "type2diabetesmellitus": "type_2_diabetes_mellitus",
    "t2dm": "type_2_diabetes_mellitus",
    "diabetesmellitustype2": "type_2_diabetes_mellitus",
    "diabetes": "type_2_diabetes_mellitus",
    "hypertension": "hypertension",
    "htn": "hypertension",
    "highbloodpressure": "hypertension",
    # Allergies
    "sulfadrugs": "sulfa_drugs",
    "sulfa": "sulfa_drugs",
    "sulphonamides": "sulfa_drugs",
    "penicillin": "penicillin",
}


def _slug(text: str) -> str:
    """Lowercase and strip everything that isn't a letter or digit."""
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _snake(text: str) -> str:
    """Lowercase, collapse runs of non-alphanumerics to single underscores."""
    s = re.sub(r"[^a-z0-9]+", "_", text.lower())
    return s.strip("_")


def normalize_key(name: str | None) -> str:
    """Return the canonical grouping key for a drug/test/condition/substance name.

    Resolution order:
      1. exact alias hit on the de-punctuated slug
      2. exact alias hit on the snake form
      3. snake-cased fallback (stable + readable)
    """
    if not name:
        return "unknown"
    slug = _slug(name)
    if slug in _ALIASES:
        return _ALIASES[slug]
    snake = _snake(name)
    if snake in _ALIASES:
        return _ALIASES[snake]
    return snake or "unknown"
