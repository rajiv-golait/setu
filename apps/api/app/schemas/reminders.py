"""Reminder DTOs (B6). Restate-only schedule; delivery is out of scope."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ReminderType = Literal["medication", "lab_test_due", "refill_due", "appointment"]


class ReminderItem(BaseModel):
    type: ReminderType
    label: str
    # medication fields
    frequency_text: str | None = None
    times_of_day: list[str] = []
    relative_to_food: str | None = None
    # date-based fields (lab_test_due / refill_due)
    due_date: str | None = None
    # provenance + safety
    source_claim_id: str | None = None
    needs_confirmation: bool = False
    note: str | None = None


class ReminderScheduleDTO(BaseModel):
    patient_id: str
    reminders: list[ReminderItem] = []
    # A plain restatement, not advice. Surfaced in the UI alongside the schedule.
    disclaimer: str = (
        "Reminders restate your doctor's prescribed schedule only. They are not "
        "medical advice and do not change any dose. Confirm anything marked unclear."
    )
