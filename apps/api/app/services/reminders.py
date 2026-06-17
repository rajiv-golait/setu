"""Reminders engine — deterministic schedule extraction (B6).

SCOPE (per the master plan, non-negotiable):
  - This builds the reminder SCHEDULE + parsing logic ONLY. It does NOT deliver
    pushes (that is F10 / stretch).
  - A reminder may ONLY restate what the doctor's document already says. It must
    never invent a dosage time the prescription didn't specify and never imply a
    dose change.
  - If the frequency notation is ambiguous or unparseable, the reminder is marked
    needs_confirmation (for the caregiver to confirm) rather than guessed. We do
    NOT emit invented times in that case.

The frequency lookup is a plain table, not an AI call. Times of day are the
conventional reading of the doctor's notation — not a recommendation we author.
"""
from __future__ import annotations

import re
from datetime import date, timedelta

from app.schemas.memory import CurrentTruthDTO, CurrentTruthEntry

# Canonical dosing-notation -> list of times of day. This is the conventional
# expansion of the doctor's notation, nothing more.
_FREQUENCY_TIMES: dict[str, list[str]] = {
    "OD": ["morning"],
    "QD": ["morning"],
    "BD": ["morning", "evening"],
    "BID": ["morning", "evening"],
    "TDS": ["morning", "afternoon", "evening"],
    "TID": ["morning", "afternoon", "evening"],
    "QID": ["morning", "afternoon", "evening", "night"],
    "HS": ["bedtime"],
    "OD-HS": ["bedtime"],
    "STAT": ["now"],
}

# Positional notation like 1-0-1 -> morning/afternoon/evening slots that are "1".
_POSITION_SLOTS = ["morning", "afternoon", "evening"]

# Food relation tokens (restated from the instruction, not authored).
_FOOD_RELATION = {
    "AC": "before food",
    "PC": "after food",
    "before food": "before food",
    "after food": "after food",
    "empty stomach": "before food",
}


def _norm_freq(freq: str) -> str:
    return re.sub(r"\s+", "", str(freq).strip().upper())


def _parse_positional(freq: str) -> list[str] | None:
    """Parse 1-0-1 / 1-1-1 / 0-0-1 style notation. Returns times or None."""
    m = re.fullmatch(r"(\d)\s*-\s*(\d)\s*-\s*(\d)", str(freq).strip())
    if not m:
        return None
    counts = [int(m.group(1)), int(m.group(2)), int(m.group(3))]
    times = [slot for slot, n in zip(_POSITION_SLOTS, counts) if n > 0]
    return times  # may be [] if all zeros (caller treats empty as ambiguous)


def _food_relation(instructions: str | None) -> str | None:
    if not instructions:
        return None
    text = str(instructions).strip().lower()
    for token, rel in _FOOD_RELATION.items():
        if token.lower() in text:
            return rel
    return None


def _times_for_frequency(freq: str) -> list[str] | None:
    """Restate the doctor's frequency as times of day. None = unparseable."""
    if not freq:
        return None
    norm = _norm_freq(freq)
    if norm in _FREQUENCY_TIMES:
        return list(_FREQUENCY_TIMES[norm])
    positional = _parse_positional(freq)
    if positional is not None and positional:
        return positional
    return None


def _med_fields(entry: CurrentTruthEntry) -> dict:
    if entry.value.get("conflict"):
        return entry.value.get("values", [{}])[0]
    return entry.value


def medication_reminders(truth: CurrentTruthDTO) -> list[dict]:
    """One reminder per active medication, restating its prescribed schedule.

    Ambiguous/unreadable frequency -> needs_confirmation, NO invented times.
    """
    reminders: list[dict] = []
    for e in truth.entries:
        if e.entry_type != "medication" or e.state == "possibly_discontinued":
            continue
        f = _med_fields(e)
        name = f.get("name") or e.normalized_key.replace("_", " ").title()
        freq = f.get("frequency")
        instructions = f.get("instructions")
        source = e.source_claim_ids[0] if e.source_claim_ids else None

        times = _times_for_frequency(freq) if freq else None
        relative_to_food = _food_relation(instructions)

        if times is None:
            # Restate-only: we will not guess a timing the prescription didn't give.
            reminders.append(
                {
                    "type": "medication",
                    "label": name,
                    "frequency_text": freq,  # whatever the doc said, verbatim
                    "times_of_day": [],
                    "relative_to_food": relative_to_food,
                    "source_claim_id": source,
                    "needs_confirmation": True,
                    "note": "Dosing schedule unclear — please confirm with the caregiver/doctor.",
                }
            )
            continue

        reminders.append(
            {
                "type": "medication",
                "label": name,
                "frequency_text": freq,
                "times_of_day": times,
                "relative_to_food": relative_to_food,
                "source_claim_id": source,
                "needs_confirmation": False,
                "note": None,
            }
        )
    return reminders


def _parse_iso_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(str(value)[:10])
    except (TypeError, ValueError):
        return None


def non_medication_reminders(truth: CurrentTruthDTO) -> list[dict]:
    """lab_test_due / refill_due derived ONLY from explicit fields in the claims.

    Never invented: if the document didn't state a due/next date or a duration,
    no reminder is produced.
    """
    reminders: list[dict] = []
    for e in truth.entries:
        f = _med_fields(e)
        source = e.source_claim_ids[0] if e.source_claim_ids else None

        # lab_test_due — only if the lab claim carries an explicit next-due date.
        if e.entry_type == "lab_result":
            due = _parse_iso_date(f.get("test_due_date") or f.get("next_due"))
            if due is not None:
                reminders.append(
                    {
                        "type": "lab_test_due",
                        "label": f.get("test_name") or e.normalized_key.replace("_", " ").title(),
                        "due_date": due.isoformat(),
                        "source_claim_id": source,
                        "needs_confirmation": False,
                        "note": None,
                    }
                )

        # refill_due — only if BOTH a duration and an observed_at are present.
        if e.entry_type == "medication" and e.state != "possibly_discontinued":
            duration_days = _duration_days(f.get("duration"))
            observed = _parse_iso_date(f.get("observed_at"))
            if duration_days is not None and observed is not None:
                refill = observed + timedelta(days=duration_days)
                reminders.append(
                    {
                        "type": "refill_due",
                        "label": f.get("name") or e.normalized_key.replace("_", " ").title(),
                        "due_date": refill.isoformat(),
                        "source_claim_id": source,
                        "needs_confirmation": False,
                        "note": "Estimated from the prescribed duration.",
                    }
                )
    return reminders


def _duration_days(duration) -> int | None:
    """Parse '30 days' / '90 days' / '2 weeks' into days. None if unparseable."""
    if not duration:
        return None
    text = str(duration).strip().lower()
    m = re.search(r"(\d+)\s*(day|days|week|weeks|month|months)", text)
    if not m:
        return None
    n = int(m.group(1))
    unit = m.group(2)
    if unit.startswith("day"):
        return n
    if unit.startswith("week"):
        return n * 7
    if unit.startswith("month"):
        return n * 30
    return None


def build_reminders(truth: CurrentTruthDTO) -> list[dict]:
    """Full deterministic reminder schedule for a patient. Restate-only."""
    return medication_reminders(truth) + non_medication_reminders(truth)
