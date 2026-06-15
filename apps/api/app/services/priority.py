"""Deterministic priority flag for brief logistics — NOT clinical triage.

Flags OBJECTIVE out-of-range values for logistics/prioritization. This is NOT a
diagnosis, NOT an acuity score, NOT medical advice. The doctor decides clinical
urgency. Language is deliberately "flagged for earlier review", never
"critical"/"urgent"/"emergency".
"""
from __future__ import annotations

from typing import Literal

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry

PRIORITY_DISCLAIMER = (
    "Flagged on objective out-of-range values for prioritization only — "
    "not a clinical assessment."
)

PriorityLevel = Literal["routine", "review_soon"]

_WORSE_WHEN_UP = frozenset(
    {"hba1c", "fbs", "fasting_blood_sugar", "blood_pressure", "blood pressure", "bp"}
)


def _raw_label(entry: CurrentTruthEntry) -> str:
    v = entry.value
    return (
        v.get("test_name")
        or v.get("name")
        or entry.normalized_key.replace("_", " ").title()
    )


def _entry_label(entry: CurrentTruthEntry) -> str:
    raw = _raw_label(entry)
    if _is_blood_pressure(raw, entry.normalized_key):
        return "BP"
    return raw


def _is_blood_pressure(label: str, key: str) -> bool:
    text = f"{label} {key}".lower()
    return "blood pressure" in text or text.strip() in {"bp", "blood_pressure"}


def _parse_bp(value) -> tuple[int, int] | None:
    if not isinstance(value, str) or "/" not in value:
        return None
    parts = value.split("/", 1)
    try:
        return int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        return None


def _bp_is_high(value) -> bool:
    parsed = _parse_bp(value)
    if parsed is None:
        return False
    systolic, diastolic = parsed
    return systolic >= 140 or diastolic >= 90


def _effective_flag(entry: CurrentTruthEntry) -> str | None:
    v = entry.value
    flag = v.get("flag")
    if flag in ("high", "low"):
        return flag
    if entry.entry_type == "vital" and _is_blood_pressure(_raw_label(entry), entry.normalized_key):
        if _bp_is_high(v.get("value")):
            return "high"
    return None


def _worsening_trend(entry: CurrentTruthEntry) -> bool:
    v = entry.value
    if v.get("trend") != "up" or v.get("previous") is None:
        return False
    label = _entry_label(entry).lower()
    key = entry.normalized_key.lower()
    if key in _WORSE_WHEN_UP or any(w in label for w in ("hba1c", "fbs", "blood pressure", "bp")):
        return True
    return entry.entry_type in ("lab_result", "vital")


def _format_value(entry: CurrentTruthEntry) -> str:
    v = entry.value
    val = v.get("value")
    if _is_blood_pressure(_raw_label(entry), entry.normalized_key):
        return str(val)
    unit = v.get("unit") or ""
    if unit and not str(val).endswith(unit):
        return f"{val}{unit}"
    return str(val)


def _reason_for_entry(entry: CurrentTruthEntry) -> str | None:
    flag = _effective_flag(entry)
    v = entry.value
    worsening = _worsening_trend(entry)
    if flag not in ("high", "low") and not worsening:
        return None

    label = _entry_label(entry)
    value_str = _format_value(entry)
    parts: list[str] = []
    if flag in ("high", "low"):
        parts.append(f"{label} {value_str} ({flag}")
        if worsening and v.get("previous") is not None:
            prev = v.get("previous")
            prev_unit = v.get("unit") or ""
            prev_str = f"{prev}{prev_unit}" if prev_unit else str(prev)
            parts[-1] += f", ↑ from {prev_str})"
        else:
            parts[-1] += ")"
    elif worsening:
        prev = v.get("previous")
        prev_unit = v.get("unit") or ""
        prev_str = f"{prev}{prev_unit}" if prev_unit else str(prev)
        parts.append(f"{label} {value_str} (trending worse, ↑ from {prev_str})")
    return parts[0] if parts else None


def compute_priority(current_truth: CurrentTruthDTO) -> dict:
    """Deterministic. No AI. Flags a brief for earlier specialist review based ONLY
    on objective, already-extracted lab flags + trends.

    Returns {"level": "routine"|"review_soon", "reasons": [..]}.
    NEVER returns a clinical acuity judgment (no "critical"/"emergency").
    """
    reasons: list[str] = []
    out_of_range_count = 0
    has_worsening = False

    for entry in current_truth.entries:
        if entry.entry_type not in ("lab_result", "vital"):
            continue
        flag = _effective_flag(entry)
        worsening = _worsening_trend(entry)
        if flag in ("high", "low"):
            out_of_range_count += 1
        if worsening:
            has_worsening = True
        reason = _reason_for_entry(entry)
        if reason:
            reasons.append(reason)

    level: PriorityLevel = (
        "review_soon" if out_of_range_count >= 2 or has_worsening else "routine"
    )
    return {"level": level, "reasons": reasons}
