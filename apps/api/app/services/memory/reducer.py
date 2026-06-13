"""Memory reducer — PURE, DETERMINISTIC, patient-safety critical.

    reduce(claims, *, confidence_threshold) -> list[CurrentTruthEntry]

NO database calls. NO I/O. NO randomness. Recomputed in full every run
(idempotent, replayable). Tested in isolation in tests/test_reducer.py.

Rules (from spec PART "REDUCER RULES"):
  1. NORMALIZE name variants to a canonical key (via normalize_key).
  2. GROUP by (claim_type, normalized_key).
  3. STATE-LIKE (medication, diagnosis, allergy): latest observed_at wins;
     ties -> higher confidence; a previously-active medication absent from a
     newer document -> possibly_discontinued (never deleted).
  4. TIME-SERIES (lab_result): keep ALL history; current = latest; trend vs
     previous (>5% delta is directional, else stable).
  5. CONFLICT: same key, same observed_at, materially different value, both above
     threshold -> conflict, surface BOTH, never auto-pick.
  6. CONFIDENCE GATE: resolved entry below threshold -> needs_review.
  7. PROVENANCE: every entry records source_claim_ids.
"""
from __future__ import annotations

from datetime import date

from app.schemas.claims import Claim
from app.schemas.memory import CurrentTruthEntry
from app.services.memory.normalize import normalize_key

# vital is treated as a time-series like labs; advice/procedure are not memory entries.
STATE_LIKE = {"medication", "diagnosis", "allergy"}
TIME_SERIES = {"lab_result", "vital"}

# entry_type -> the field within claim.fields that names the thing.
_NAME_FIELD = {
    "medication": "name",
    "diagnosis": "condition",
    "allergy": "substance",
    "lab_result": "test_name",
    "vital": "name",
}

# Below this fraction, two time-series values are "stable" rather than up/down.
_TREND_DELTA = 0.05
# Two values differing by more than this fraction are "materially different" (conflict).
_CONFLICT_DELTA = 0.05


def grouping_key(claim: Claim) -> str:
    """Canonical normalized_key for a claim (also used at ingestion time)."""
    name = claim.fields.get(_NAME_FIELD.get(claim.type, ""))
    return normalize_key(name if isinstance(name, str) else None)


def _observed(claim: Claim) -> date:
    """observed_at, with a stable floor so missing dates sort oldest."""
    return claim.observed_at or date.min


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _trend(current, previous) -> str | None:
    """Directional trend of current vs previous numeric value."""
    cur, prev = _num(current), _num(previous)
    if cur is None or prev is None or prev == 0:
        return None
    delta = (cur - prev) / abs(prev)
    if delta > _TREND_DELTA:
        return "up"
    if delta < -_TREND_DELTA:
        return "down"
    return "stable"


# Fields that identify *which thing* an entry is about (not what it asserts).
# Two claims about the same thing conflict when their *assertion* fields differ.
_IDENTITY_FIELDS = {"name", "generic", "condition", "substance", "test_name", "unit", "dose_unit"}


def _materially_different(a: Claim, b: Claim, name_field: str) -> bool:
    """True if two same-key/same-date claims assert genuinely different values.

    The grouping already guarantees they're about the same thing (same
    normalized_key). So we compare the *assertion* fields — dose/frequency for a
    medication, status for a diagnosis, severity for an allergy, numeric value for
    a lab/vital — ignoring the identity fields that merely name the thing.
    """
    fa, fb = a.fields, b.fields

    # Numeric assertion (labs/vitals): compare value with tolerance.
    na, nb = _num(fa.get("value")), _num(fb.get("value"))
    if na is not None and nb is not None:
        if nb == 0:
            return na != nb
        return abs(na - nb) / abs(nb) > _CONFLICT_DELTA

    # Non-numeric: any assertion field present in either claim that differs.
    assertion_keys = (set(fa) | set(fb)) - _IDENTITY_FIELDS
    for k in assertion_keys:
        if str(fa.get(k)).strip().lower() != str(fb.get(k)).strip().lower():
            return True
    return False


def _gate_state(state: str, confidence: float, threshold: float) -> str:
    """Apply the confidence gate without overriding conflict/discontinued states."""
    if state in ("conflict", "possibly_discontinued"):
        return state
    return "needs_review" if confidence < threshold else state


# --------------------------------------------------------------------------- #
# Per-family resolvers
# --------------------------------------------------------------------------- #
def _resolve_state_like(
    entry_type: str, key: str, claims: list[Claim], threshold: float
) -> CurrentTruthEntry:
    """latest-wins + confidence tie-break + conflict detection."""
    name_field = _NAME_FIELD[entry_type]
    ordered = sorted(claims, key=lambda c: (_observed(c), c.confidence), reverse=True)
    winner = ordered[0]

    # Conflict: same latest date, materially different, both above threshold.
    state = "confirmed"
    latest_date = _observed(winner)
    same_date = [c for c in claims if _observed(c) == latest_date]
    conflicting = [
        c
        for c in same_date
        if c is not winner
        and c.confidence >= threshold
        and winner.confidence >= threshold
        and _materially_different(winner, c, name_field)
    ]
    value: dict = {**winner.fields}
    if conflicting:
        state = "conflict"
        value = {
            "conflict": True,
            "values": [{**winner.fields}] + [{**c.fields} for c in conflicting],
        }

    state = _gate_state(state, float(winner.confidence), threshold)
    source_ids = [winner.claim_id] + [c.claim_id for c in conflicting]
    return CurrentTruthEntry(
        entry_type=entry_type,
        normalized_key=key,
        value=value,
        confidence=float(winner.confidence),
        state=state,
        source_claim_ids=source_ids,
    )


def _resolve_time_series(
    entry_type: str, key: str, claims: list[Claim], threshold: float
) -> CurrentTruthEntry:
    """Keep all history; current = latest; trend vs previous. Never collapse."""
    ordered = sorted(claims, key=lambda c: (_observed(c), c.confidence))
    history = [
        {
            "value": c.fields.get("value"),
            "unit": c.fields.get("unit"),
            "date": c.observed_at.isoformat() if c.observed_at else None,
            "flag": c.fields.get("flag"),
            "claim_id": c.claim_id,
        }
        for c in ordered
    ]
    current = ordered[-1]
    previous = ordered[-2] if len(ordered) >= 2 else None
    trend = _trend(current.fields.get("value"), previous.fields.get("value")) if previous else None

    value = {
        **current.fields,
        "trend": trend,
        "previous": previous.fields.get("value") if previous else None,
        "history": history,
    }
    state = _gate_state("confirmed", float(current.confidence), threshold)
    return CurrentTruthEntry(
        entry_type=entry_type,
        normalized_key=key,
        value=value,
        confidence=float(current.confidence),
        state=state,
        source_claim_ids=[c.claim_id for c in ordered],
    )


def _apply_discontinuation(
    medications: list[CurrentTruthEntry], claims: list[Claim]
) -> None:
    """A previously-active medication absent from the newest document => possibly_discontinued.

    Conservative: we flag, never delete. "Newest document" is approximated by the
    most recent observed_at across all medication claims; meds not seen on that
    date that were active before it are flagged.
    """
    med_claims = [c for c in claims if c.type == "medication"]
    if not med_claims:
        return
    latest = max(_observed(c) for c in med_claims)
    keys_on_latest = {grouping_key(c) for c in med_claims if _observed(c) == latest}
    keys_before_latest = {grouping_key(c) for c in med_claims if _observed(c) < latest}

    for entry in medications:
        if (
            entry.normalized_key in keys_before_latest
            and entry.normalized_key not in keys_on_latest
            and entry.state not in ("conflict",)
        ):
            entry.state = "possibly_discontinued"


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def reduce(claims: list[Claim], *, confidence_threshold: float) -> list[CurrentTruthEntry]:
    """Pure reduction of a patient's full claim set into Current Truth entries."""
    # Group by (claim_type, normalized_key). advice/procedure are not memory facts.
    groups: dict[tuple[str, str], list[Claim]] = {}
    for claim in claims:
        if claim.type not in STATE_LIKE and claim.type not in TIME_SERIES:
            continue
        key = grouping_key(claim)
        groups.setdefault((claim.type, key), []).append(claim)

    entries: list[CurrentTruthEntry] = []
    for (entry_type, key), group in groups.items():
        if entry_type in STATE_LIKE:
            entries.append(_resolve_state_like(entry_type, key, group, confidence_threshold))
        else:
            entries.append(_resolve_time_series(entry_type, key, group, confidence_threshold))

    # Post-pass: medication discontinuation.
    medications = [e for e in entries if e.entry_type == "medication"]
    _apply_discontinuation(medications, claims)

    # Stable, deterministic ordering for reproducible output/snapshots.
    entries.sort(key=lambda e: (e.entry_type, e.normalized_key))
    return entries
