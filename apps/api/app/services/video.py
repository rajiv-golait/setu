"""Video consult room naming — deterministic helper ONLY.

The video consult is a client-side Jitsi Meet iframe embed (frontend, Tier 2).
Jitsi's free tier needs no server-side signaling for this use case, so the
backend's entire role is to provide a stable, unique room name per
patient+brief. NO WebRTC, NO TURN/STUN, NO signaling server.

Room name is deterministic so the caregiver and specialist independently derive
the same room from the shared brief.
"""
from __future__ import annotations


def consult_room_name(patient_id: str, brief_id: str) -> str:
    """Stable Jitsi room name for a given patient + brief."""
    return f"setu-{patient_id}-{brief_id}"
