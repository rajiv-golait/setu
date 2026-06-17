"""Phase 6 F2 — appointment lifecycle, role scoping, and side-effect tests.

Auth-enabled tests mint local HS256 tokens carrying app_metadata.role (same
approach as test_providers.py) so provider/patient roles resolve. A patient is
bound to a Supabase user id so ownership scoping works.
"""
from __future__ import annotations

import jwt
import pytest
from sqlalchemy import select

from app.db.models import Appointment, Patient, Provider
from app.db.models import Reminder as ReminderRow

pytestmark = pytest.mark.asyncio

_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(sub: str, role: str | None = None) -> str:
    claims: dict = {"sub": sub, "aud": "authenticated"}
    if role is not None:
        claims["app_metadata"] = {"role": role}
    return jwt.encode(claims, _SECRET, algorithm="HS256")


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_enabled(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", _SECRET)


async def _seed_patient(session_factory, *, patient_id: str, supabase_user_id: str | None = None):
    async with session_factory() as db:
        db.add(
            Patient(
                id=patient_id,
                display_name="Test",
                lang_pref="mr",
                patient_token=f"tok_{patient_id}",
                supabase_user_id=supabase_user_id,
            )
        )
        await db.commit()


async def _seed_provider(session_factory, *, supabase_user_id: str, specialty: str | None = None):
    from app.ids import new_id

    async with session_factory() as db:
        prv = Provider(
            id=new_id("prv"),
            supabase_user_id=supabase_user_id,
            display_name="Dr. Test",
            specialty=specialty,
        )
        db.add(prv)
        await db.commit()
        return prv.id


# --- Booking + DTO joins -------------------------------------------------- #


async def test_patient_books_and_provider_completes_lifecycle(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, patient_id="pat_lc", supabase_user_id="u_pat")
    await _seed_provider(session_factory, supabase_user_id="u_prov", specialty="cardiology")

    pat = _bearer(_token("u_pat", "patient"))
    prov = _bearer(_token("u_prov", "provider"))

    # requested
    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": "pat_lc", "specialty": "cardiology"},
        headers=pat,
    )
    assert r.status_code == 201, r.text
    appt = r.json()
    assert appt["status"] == "requested"
    appt_id = appt["id"]
    assert appt_id.startswith("apt_")

    # accept (provider) → sets consult_room + provider join info + reminder
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "accept"}, headers=prov)
    assert r.status_code == 200, r.text
    accepted = r.json()
    assert accepted["status"] == "accepted"
    assert accepted["consult_room"]
    assert accepted["provider_name"] == "Dr. Test"
    assert accepted["provider_specialty"] == "cardiology"

    # complete (provider)
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "complete"}, headers=prov)
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "completed"


async def test_accept_sets_consult_room_and_creates_reminder(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, patient_id="pat_rm", supabase_user_id="u_pat")
    await _seed_provider(session_factory, supabase_user_id="u_prov", specialty="general")

    pat = _bearer(_token("u_pat", "patient"))
    prov = _bearer(_token("u_prov", "provider"))

    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": "pat_rm", "specialty": "general"},
        headers=pat,
    )
    appt_id = r.json()["id"]
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "accept"}, headers=prov)
    assert r.status_code == 200

    async with session_factory() as db:
        appt = (await db.execute(select(Appointment).where(Appointment.id == appt_id))).scalar_one()
        reminders = (
            await db.execute(select(ReminderRow).where(ReminderRow.patient_id == "pat_rm"))
        ).scalars().all()

    # consult_room reuses services/video.py naming: setu-{patient}-{...}
    assert appt.consult_room == f"setu-pat_rm-{appt_id}"
    appt_reminders = [r for r in reminders if r.reminder_type == "appointment"]
    assert len(appt_reminders) == 1
    assert appt_reminders[0].schedule["appointment_id"] == appt_id


async def test_referral_and_triage_ids_persist_in_dto(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, patient_id="pat_ref", supabase_user_id="u_pat")
    pat = _bearer(_token("u_pat", "patient"))
    r = await client.post(
        "/api/v1/appointments",
        json={
            "patient_id": "pat_ref",
            "specialty": "neurology",
            "referral_id": "ref_x",
            "triage_id": "trg_y",
        },
        headers=pat,
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["referral_id"] == "ref_x"
    assert body["triage_id"] == "trg_y"


# --- Illegal transitions -------------------------------------------------- #


async def test_illegal_transition_rejected(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, patient_id="pat_il", supabase_user_id="u_pat")
    await _seed_provider(session_factory, supabase_user_id="u_prov", specialty="general")
    pat = _bearer(_token("u_pat", "patient"))
    prov = _bearer(_token("u_prov", "provider"))

    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": "pat_il", "specialty": "general"},
        headers=pat,
    )
    appt_id = r.json()["id"]

    # requested → completed directly is not a legal edge.
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "complete"}, headers=prov)
    assert r.status_code == 400, r.text
    assert r.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_unknown_action_rejected(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, patient_id="pat_uk", supabase_user_id="u_pat")
    pat = _bearer(_token("u_pat", "patient"))
    r = await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_uk", "specialty": "x"}, headers=pat
    )
    appt_id = r.json()["id"]
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "teleport"}, headers=pat)
    assert r.status_code == 400


# --- Role gates ----------------------------------------------------------- #


async def test_patient_cannot_accept_own_appointment(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, patient_id="pat_na", supabase_user_id="u_pat")
    pat = _bearer(_token("u_pat", "patient"))
    r = await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_na", "specialty": "general"}, headers=pat
    )
    appt_id = r.json()["id"]
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "accept"}, headers=pat)
    assert r.status_code == 403, r.text
    assert r.json()["error"]["code"] == "FORBIDDEN"


async def test_patient_cannot_cancel_another_patients_appointment(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, patient_id="pat_a", supabase_user_id="u_a")
    await _seed_patient(session_factory, patient_id="pat_b", supabase_user_id="u_b")
    a = _bearer(_token("u_a", "patient"))
    b = _bearer(_token("u_b", "patient"))

    r = await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_a", "specialty": "general"}, headers=a
    )
    appt_id = r.json()["id"]

    # patient B tries to cancel patient A's appointment
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "cancel"}, headers=b)
    assert r.status_code == 403, r.text


async def test_patient_can_cancel_own(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, patient_id="pat_cc", supabase_user_id="u_pat")
    pat = _bearer(_token("u_pat", "patient"))
    r = await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_cc", "specialty": "general"}, headers=pat
    )
    appt_id = r.json()["id"]
    r = await client.patch(f"/api/v1/appointments/{appt_id}", json={"action": "cancel"}, headers=pat)
    assert r.status_code == 200
    assert r.json()["status"] == "cancelled"


# --- GET role scoping ----------------------------------------------------- #


async def test_get_scoping_patient_sees_only_own(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, patient_id="pat_a", supabase_user_id="u_a")
    await _seed_patient(session_factory, patient_id="pat_b", supabase_user_id="u_b")
    a = _bearer(_token("u_a", "patient"))
    b = _bearer(_token("u_b", "patient"))

    await client.post("/api/v1/appointments", json={"patient_id": "pat_a", "specialty": "x"}, headers=a)
    await client.post("/api/v1/appointments", json={"patient_id": "pat_b", "specialty": "x"}, headers=b)

    r = await client.get("/api/v1/appointments", headers=a)
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 1
    assert rows[0]["patient_id"] == "pat_a"


async def test_get_scoping_provider_sees_assigned_and_matching_queue(
    client, session_factory, auth_enabled
):
    await _seed_patient(session_factory, patient_id="pat_q1", supabase_user_id="u1")
    await _seed_patient(session_factory, patient_id="pat_q2", supabase_user_id="u2")
    await _seed_provider(session_factory, supabase_user_id="u_card", specialty="cardiology")

    p1 = _bearer(_token("u1", "patient"))
    p2 = _bearer(_token("u2", "patient"))
    card = _bearer(_token("u_card", "provider"))

    # one cardiology (matches the provider's specialty), one dermatology (does not)
    await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_q1", "specialty": "cardiology"}, headers=p1
    )
    await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_q2", "specialty": "dermatology"}, headers=p2
    )

    r = await client.get("/api/v1/appointments", headers=card)
    assert r.status_code == 200
    rows = r.json()
    specialties = {row["specialty"] for row in rows}
    assert "cardiology" in specialties
    assert "dermatology" not in specialties


async def test_get_status_filter(client, session_factory, auth_enabled):
    await _seed_patient(session_factory, patient_id="pat_sf", supabase_user_id="u_pat")
    await _seed_provider(session_factory, supabase_user_id="u_prov", specialty="general")
    pat = _bearer(_token("u_pat", "patient"))
    prov = _bearer(_token("u_prov", "provider"))

    r1 = await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_sf", "specialty": "general"}, headers=pat
    )
    await client.post(
        "/api/v1/appointments", json={"patient_id": "pat_sf", "specialty": "general"}, headers=pat
    )
    # accept one so it leaves 'requested'
    await client.patch(
        f"/api/v1/appointments/{r1.json()['id']}", json={"action": "accept"}, headers=prov
    )

    r = await client.get("/api/v1/appointments?status=requested", headers=pat)
    rows = r.json()
    assert all(row["status"] == "requested" for row in rows)
    assert len(rows) == 1


async def test_reschedule_releases_and_rebooks_slot(client, session_factory, auth_enabled):
    from datetime import datetime, timedelta, timezone

    from app.db.models import AppointmentSlot

    from app.ids import new_id

    patient_id = "pat_rs"
    await _seed_patient(session_factory, patient_id=patient_id, supabase_user_id="u_pat_rs")
    prv_id = await _seed_provider(session_factory, supabase_user_id="u_prov_rs", specialty="general")

    async with session_factory() as db:
        from app.db.models import Provider

        row = (await db.execute(select(Provider).where(Provider.id == prv_id))).scalar_one()
        row.verification_status = "approved"
        now = datetime.now(timezone.utc)
        slot_a = AppointmentSlot(
            id=new_id("slot"),
            provider_id=prv_id,
            starts_at=now + timedelta(days=2),
            ends_at=now + timedelta(days=2, hours=1),
            status="open",
        )
        slot_b = AppointmentSlot(
            id=new_id("slot"),
            provider_id=prv_id,
            starts_at=now + timedelta(days=3),
            ends_at=now + timedelta(days=3, hours=1),
            status="open",
        )
        db.add(slot_a)
        db.add(slot_b)
        await db.commit()
        slot_a_id, slot_b_id = slot_a.id, slot_b.id

    pat = _bearer(_token("u_pat_rs", "patient"))
    prov = _bearer(_token("u_prov_rs", "provider"))

    r = await client.post(
        "/api/v1/appointments",
        json={"patient_id": patient_id, "specialty": "general", "slot_id": slot_a_id},
        headers=pat,
    )
    assert r.status_code == 201, r.text
    appt_id = r.json()["id"]

    r = await client.patch(
        f"/api/v1/appointments/{appt_id}",
        json={"action": "accept"},
        headers=prov,
    )
    assert r.status_code == 200, r.text

    r = await client.patch(
        f"/api/v1/appointments/{appt_id}",
        json={"action": "reschedule", "new_slot_id": slot_b_id},
        headers=pat,
    )
    assert r.status_code == 200, r.text

    async with session_factory() as db:
        appt = (
            await db.execute(select(Appointment).where(Appointment.id == appt_id))
        ).scalar_one()
        assert appt.slot_id == slot_b_id
        old = (
            await db.execute(select(AppointmentSlot).where(AppointmentSlot.id == slot_a_id))
        ).scalar_one()
        new = (
            await db.execute(select(AppointmentSlot).where(AppointmentSlot.id == slot_b_id))
        ).scalar_one()
        assert old.status == "open"
        assert new.status == "booked"

