"""Brief engine.

The reasoner writes PROSE. This module decides SAFETY FLAGS deterministically
from Current Truth — flags are never left to the model:

  abnormal_lab  -> lab value outside its reference_range (or flagged high/low)
  needs_review  -> entry confidence < threshold or entry.state == needs_review
  missing_data  -> a required field for a memory entry is absent
  conflict      -> entry.state == conflict (same key/date, different values)
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.config import settings
from app.ids import new_id
from app.schemas.brief import BriefFlag, BriefPriority, DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.priority import compute_priority
from app.services.reasoning.base import ReasonerProvider

# Default specialist when the model does not infer one (plain dict — not AI).
_SPECIALIST_BY_DOMINANT = {
    "diabetes": "Endocrinologist",
    "hypertension": "Cardiologist",
    "cardiac": "Cardiologist",
    "renal": "Nephrologist",
}
_DEFAULT_SPECIALIST = "General Physician"

# Required fields whose absence yields a missing_data flag, per entry type.
_REQUIRED_FOR_BRIEF = {
    "medication": ["name", "dose", "frequency"],
    "lab_result": ["value", "unit"],
    "diagnosis": ["condition"],
    "allergy": ["substance"],
}


def _parse_range(rng: str) -> tuple[float, float] | None:
    """Parse a reference range like '4.0-5.6' or '4.0 - 5.6' into (low, high)."""
    if not rng:
        return None
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*[-–]\s*(-?\d+(?:\.\d+)?)", str(rng))
    if not m:
        return None
    low, high = float(m.group(1)), float(m.group(2))
    return (low, high) if low <= high else (high, low)


def _num(v) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _entry_fields(entry: CurrentTruthEntry) -> dict:
    """The salient field dict for an entry (handle conflict-wrapped values)."""
    if entry.value.get("conflict"):
        return entry.value.get("values", [{}])[0]
    return entry.value


def compute_flags(truth: CurrentTruthDTO, threshold: float) -> list[BriefFlag]:
    """Deterministic safety flags. Order: conflict, abnormal_lab, needs_review, missing_data."""
    flags: list[BriefFlag] = []

    for e in truth.entries:
        fields = _entry_fields(e)
        label = fields.get("name") or fields.get("test_name") or fields.get("condition") or fields.get("substance") or e.normalized_key.replace("_", " ")

        # conflict
        if e.state == "conflict":
            flags.append(BriefFlag(severity="warning", text=f"Conflicting values recorded for {label} — confirm", type="conflict"))

        # abnormal_lab
        if e.entry_type == "lab_result":
            flag = fields.get("flag")
            val = _num(fields.get("value"))
            rng = _parse_range(fields.get("reference_range", ""))
            abnormal = flag in ("high", "low")
            if not abnormal and val is not None and rng is not None:
                abnormal = val < rng[0] or val > rng[1]
            if abnormal:
                trend = e.value.get("trend")
                trend_str = f" (trending {trend})" if trend in ("up", "down") else ""
                flags.append(BriefFlag(severity="warning", text=f"{label} {fields.get('value')}{fields.get('unit', '')} outside reference range{trend_str}", type="abnormal_lab"))

        # needs_review (confidence gate or reducer-flagged)
        if e.state == "needs_review" or (e.confidence is not None and e.confidence < threshold):
            flags.append(BriefFlag(severity="info", text=f"{label} is low-confidence — confirm", type="needs_review"))

        # possibly_discontinued -> surfaced as an info needs_review-style note
        if e.state == "possibly_discontinued":
            flags.append(BriefFlag(severity="info", text=f"{label} may have been discontinued — confirm", type="needs_review"))

        # missing_data
        required = _REQUIRED_FOR_BRIEF.get(e.entry_type, [])
        missing = [f for f in required if fields.get(f) in (None, "")]
        if missing:
            flags.append(BriefFlag(severity="info", text=f"{label} missing: {', '.join(missing)}", type="missing_data"))

    return flags


def _confidence_notes(truth: CurrentTruthDTO, flags: list[BriefFlag]) -> str:
    flagged = sum(1 for f in flags if f.type in ("needs_review", "conflict"))
    total = len(truth.entries)
    if flagged == 0:
        return "All memory entries above confidence threshold."
    return f"{flagged} of {total} memory entries flagged for review."


def _has_renal_flag(truth: CurrentTruthDTO) -> bool:
    for e in truth.entries:
        if e.entry_type != "lab_result":
            continue
        key = e.normalized_key.lower()
        flag = e.value.get("flag")
        if key in ("egfr", "creatinine", "gfr") and flag in ("low", "high"):
            return True
    return False


def _dominant_condition_key(truth: CurrentTruthDTO) -> str | None:
    for e in truth.entries:
        if e.entry_type != "diagnosis":
            continue
        fields = _entry_fields(e)
        cond = (fields.get("condition") or e.normalized_key).lower()
        if any(w in cond for w in ("diabetes", "diabetic", "t2dm", "t1dm", "glyc")):
            return "diabetes"
        if any(w in cond for w in ("hypertension", "htn", "cardiac", "heart", "cad")):
            return "hypertension"
    return None


def default_specialist_type(truth: CurrentTruthDTO) -> str:
    """Deterministic specialty suggestion from dominant condition / renal lab flags."""
    if _has_renal_flag(truth):
        return _SPECIALIST_BY_DOMINANT["renal"]
    dominant = _dominant_condition_key(truth)
    if dominant:
        return _SPECIALIST_BY_DOMINANT[dominant]
    return _DEFAULT_SPECIALIST


def _coerce_named_item(item: object, name_key: str, aliases: tuple[str, ...] = ()) -> dict:
    """Normalize a list item that may be a plain string from LLM output."""
    if isinstance(item, str):
        return {name_key: item}
    if isinstance(item, dict):
        if name_key not in item:
            for alt in aliases:
                if alt in item:
                    return {**item, name_key: item[alt]}
        return item
    return {name_key: str(item)}


def _coerce_timeline_item(item: object) -> dict:
    if isinstance(item, str):
        return {"date": "", "event": item}
    if isinstance(item, dict):
        event = item.get("event") or item.get("description") or ""
        return {"date": item.get("date", ""), "event": event}
    return {"date": "", "event": str(item)}


def _as_list(value: object) -> list:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_brief_content(content: dict) -> dict:
    """Coerce provider brief JSON into shapes DoctorBriefDTO expects.

    Cloud models often return medications/conditions as plain strings instead of
    structured objects — normalize before Pydantic validation.
    """
    out = dict(content)
    out["active_medications"] = [
        _coerce_named_item(m, "name", ("medication", "drug"))
        for m in _as_list(content.get("active_medications"))
    ]
    out["recent_labs"] = [
        _coerce_named_item(l, "test", ("test_name",))
        for l in _as_list(content.get("recent_labs"))
    ]
    out["active_conditions"] = [
        _coerce_named_item(c, "condition", ("diagnosis", "name"))
        for c in _as_list(content.get("active_conditions"))
    ]
    out["allergies"] = [
        _coerce_named_item(a, "substance", ("allergen", "name"))
        for a in _as_list(content.get("allergies"))
    ]
    out["timeline"] = [_coerce_timeline_item(t) for t in _as_list(content.get("timeline"))]
    out["suggested_questions"] = [
        q if isinstance(q, str) else str(q) for q in content.get("suggested_questions", [])
    ]
    return out


async def build_brief(
    patient_id: str,
    truth: CurrentTruthDTO,
    reasoner: ReasonerProvider,
    source_documents: list[str],
) -> DoctorBriefDTO:
    """Generate the full Doctor Brief: model prose + code-computed flags."""
    content = normalize_brief_content(await reasoner.generate_brief(truth))
    flags = compute_flags(truth, settings.CONFIDENCE_THRESHOLD)
    priority_data = compute_priority(truth)
    specialist_type = content.get("specialist_type") or default_specialist_type(truth)

    brief = DoctorBriefDTO(
        brief_id=new_id("brf", 3),
        patient_id=patient_id,
        generated_at=datetime.now(timezone.utc),
        model=getattr(reasoner, "name", "mock"),
        one_line=content.get("one_line", ""),
        chief_concern=content.get("chief_concern", ""),
        active_medications=content.get("active_medications", []),
        recent_labs=content.get("recent_labs", []),
        active_conditions=content.get("active_conditions", []),
        allergies=content.get("allergies", []),
        timeline=content.get("timeline", []),
        flags=flags,
        suggested_questions=content.get("suggested_questions", []),
        source_documents=source_documents,
        confidence_notes=_confidence_notes(truth, flags),
        referred_by=content.get("referred_by"),
        referral_reason=content.get("referral_reason"),
        specialist_type=specialist_type,
        priority=BriefPriority.model_validate(priority_data),
    )
    return brief
