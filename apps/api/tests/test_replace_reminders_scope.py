"""D-C4: replace_reminders must NOT delete appointment-type reminders."""
from __future__ import annotations

import pytest

pytestmark = pytest.mark.asyncio


async def test_replace_reminders_preserves_appointment_type(client, session_factory):
    """Calling GET /patients/{id}/reminders must not wipe appointment reminders."""
    from app.db.models import Patient, Reminder
    from app.ids import new_id

    pat_id = "pat_dc4"
    async with session_factory() as db:
        db.add(Patient(id=pat_id, display_name="Test", lang_pref="en",
                       patient_token="tok_dc4"))
        # Seed one appointment reminder (managed by appointments service, not replace_reminders).
        db.add(Reminder(
            id=new_id("rem", 5),
            patient_id=pat_id,
            reminder_type="appointment",
            label="Appointment with Dr. Smith",
            schedule={"at": "2026-07-01T10:00:00Z"},
            needs_confirmation=False,
        ))
        await db.commit()

    # Call the reminders endpoint — this triggers replace_reminders internally.
    r = await client.get(f"/api/v1/patients/{pat_id}/reminders")
    assert r.status_code == 200

    # Appointment reminder must still exist in the DB.
    from sqlalchemy import select
    async with session_factory() as db:
        rows = (await db.execute(
            select(Reminder).where(
                Reminder.patient_id == pat_id,
                Reminder.reminder_type == "appointment",
            )
        )).scalars().all()
    assert len(rows) == 1, "appointment reminder was deleted by replace_reminders"
