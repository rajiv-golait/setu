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
from app.schemas.brief import BriefFlag, DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry
from app.services.reasoning.base import ReasonerProvider

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


async def build_brief(
    patient_id: str,
    truth: CurrentTruthDTO,
    reasoner: ReasonerProvider,
    source_documents: list[str],
) -> DoctorBriefDTO:
    """Generate the full Doctor Brief: model prose + code-computed flags."""
    content = await reasoner.generate_brief(truth)
    flags = compute_flags(truth, settings.CONFIDENCE_THRESHOLD)

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
    )
    return brief
