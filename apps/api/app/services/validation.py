"""Claim validation: schema + plausibility + confidence gating.

Pure-ish and unit-testable. Does NOT mutate claims destructively beyond setting
needs_review (claims are append-only at the DB layer; here we operate on in-memory
Claim objects before persistence). Abstain-friendly: a missing field flags
needs_review rather than fabricating a value.
"""
from __future__ import annotations

from app.config import settings
from app.schemas.claims import REQUIRED_FIELDS, Claim, ClaimsJSON

# Plausibility ranges per lab test (normalized_key -> (min, max, unit hint)).
# Generous bounds — the goal is to catch garbage (OCR slips), not to second-guess clinicians.
_LAB_RANGES: dict[str, tuple[float, float]] = {
    "hba1c": (2.0, 20.0),
    "fasting_blood_sugar": (20.0, 600.0),
    "postprandial_blood_sugar": (20.0, 800.0),
    "creatinine": (0.1, 20.0),
    "ldl_cholesterol": (10.0, 400.0),
    "egfr": (1.0, 200.0),
}

# Sanity bounds for medication dose (mg-equivalent, very loose).
_DOSE_RANGE = (0.001, 10000.0)

_VALID_DIAGNOSIS_STATUS = {"active", "resolved", "suspected"}


class ValidationResult:
    def __init__(self) -> None:
        self.claims: list[Claim] = []
        self.issues: list[dict] = []

    def add_issue(self, claim_id: str, code: str, message: str) -> None:
        self.issues.append({"claim_id": claim_id, "code": code, "message": message})


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def validate_claim(claim: Claim, threshold: float) -> tuple[Claim, list[dict]]:
    """Validate a single claim. Returns the (possibly needs_review-flagged) claim + issues."""
    issues: list[dict] = []
    fields = dict(claim.fields)
    needs_review = claim.needs_review

    # 1. Required fields present?
    required = REQUIRED_FIELDS.get(claim.type, [])
    missing = [f for f in required if fields.get(f) in (None, "")]
    if missing:
        needs_review = True
        issues.append({"claim_id": claim.claim_id, "code": "MISSING_FIELDS", "message": f"missing {missing}"})

    # 2. Type-specific plausibility.
    if claim.type == "lab_result":
        val = _num(fields.get("value"))
        if val is not None:
            from app.services.memory.normalize import normalize_key

            key = normalize_key(fields.get("test_name"))
            rng = _LAB_RANGES.get(key)
            if rng and not (rng[0] <= val <= rng[1]):
                needs_review = True
                issues.append({"claim_id": claim.claim_id, "code": "IMPLAUSIBLE_VALUE", "message": f"{key}={val} outside {rng}"})

    elif claim.type == "medication":
        dose = _num(fields.get("dose"))
        if dose is not None and not (_DOSE_RANGE[0] <= dose <= _DOSE_RANGE[1]):
            needs_review = True
            issues.append({"claim_id": claim.claim_id, "code": "IMPLAUSIBLE_DOSE", "message": f"dose={dose} implausible"})

    elif claim.type == "diagnosis":
        status = fields.get("status")
        if status and status not in _VALID_DIAGNOSIS_STATUS:
            needs_review = True
            issues.append({"claim_id": claim.claim_id, "code": "BAD_STATUS", "message": f"status={status} invalid"})

    # 3. Confidence gate.
    if claim.confidence < threshold:
        needs_review = True
        issues.append({"claim_id": claim.claim_id, "code": "LOW_CONFIDENCE", "message": f"confidence {claim.confidence} < {threshold}"})

    validated = claim.model_copy(update={"needs_review": needs_review})
    return validated, issues


def validate_claims(claims_json: ClaimsJSON, threshold: float | None = None) -> ValidationResult:
    """Validate every claim in a Claims JSON payload."""
    threshold = settings.CONFIDENCE_THRESHOLD if threshold is None else threshold
    result = ValidationResult()
    for claim in claims_json.claims:
        validated, issues = validate_claim(claim, threshold)
        result.claims.append(validated)
        result.issues.extend(issues)
    return result
