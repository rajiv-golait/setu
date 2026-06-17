"""Appointment DTOs + the authoritative status state machine (Phase 6 F2).

`ALLOWED_TRANSITIONS` is the single source of truth for what status changes are
legal and which role may perform them. The PATCH endpoint never writes a raw
status — it submits an `action`, and services/appointments.transition() validates
it against this map. Arbitrary status writes are not possible.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class AppointmentStatus(str, Enum):
    requested = "requested"
    accepted = "accepted"
    confirmed = "confirmed"
    completed = "completed"
    declined = "declined"
    cancelled = "cancelled"


# Actions a client may request via PATCH. Each maps to a (from_status -> to_status)
# edge plus the role allowed to perform it.
#   action -> {"to": AppointmentStatus, "from": {allowed source statuses},
#              "roles": {roles permitted}}
# "self" in roles means the patient who owns the appointment (booked it).
ALLOWED_TRANSITIONS: dict[str, dict] = {
    "accept": {
        "to": AppointmentStatus.accepted,
        "from": {AppointmentStatus.requested},
        "roles": {"provider"},
    },
    "decline": {
        "to": AppointmentStatus.declined,
        "from": {AppointmentStatus.requested},
        "roles": {"provider"},
    },
    "confirm": {
        "to": AppointmentStatus.confirmed,
        "from": {AppointmentStatus.accepted},
        "roles": {"patient", "provider"},
    },
    "complete": {
        "to": AppointmentStatus.completed,
        "from": {AppointmentStatus.accepted, AppointmentStatus.confirmed},
        "roles": {"provider"},
    },
    "cancel": {
        "to": AppointmentStatus.cancelled,
        "from": {AppointmentStatus.requested, AppointmentStatus.accepted, AppointmentStatus.confirmed},
        "roles": {"patient", "provider"},
    },
}


class AppointmentCreate(BaseModel):
    patient_id: str
    specialty: str
    scheduled_for: datetime | None = None
    referral_id: str | None = None
    triage_id: str | None = None
    notes: str | None = None


class AppointmentPatch(BaseModel):
    action: str  # one of ALLOWED_TRANSITIONS keys


class AppointmentDTO(BaseModel):
    id: str
    patient_id: str
    provider_id: str | None = None
    specialty: str
    status: AppointmentStatus
    scheduled_for: datetime | None = None
    consult_room: str | None = None
    referral_id: str | None = None
    triage_id: str | None = None
    notes: str | None = None
    requested_at: datetime
    created_at: datetime
    updated_at: datetime
    # Joined provider info (populated when a provider is assigned) so the
    # frontend doesn't need a second call — mirrors how brief/referral DTOs
    # inline their derived/joined fields.
    provider_name: str | None = None
    provider_specialty: str | None = None
