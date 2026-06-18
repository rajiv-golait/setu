"""Sharing service. Builds an immutable snapshot (frozen copies of brief +
current truth) and a scannable QR pointing at the public share URL.

The snapshot embeds copies, so later document uploads never change an
already-shared link.
"""
from __future__ import annotations

import io

import segno

from app.config import settings
from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO
from app.schemas.share import ShareSnapshotDTO


def share_url(token: str) -> str:
    """Public doctor-facing brief URL (encoded in QR codes)."""
    return f"{settings.BRIEF_BASE_URL.rstrip('/')}/brief/{token}"


def make_qr_svg(data: str, scale: int = 6) -> str:
    """Return an inline SVG string for the given data (scannable on a phone)."""
    qr = segno.make(data, error="m")
    buf = io.BytesIO()  # segno's svg writer emits bytes
    qr.save(buf, kind="svg", scale=scale, border=2, xmldecl=False)
    return buf.getvalue().decode("utf-8")


def build_snapshot(
    share_id: str,
    token: str,
    created_at,
    expires_at,
    patient_ref: str,
    brief: DoctorBriefDTO,
    current_truth: CurrentTruthDTO,
) -> ShareSnapshotDTO:
    """Assemble the frozen, public, read-only snapshot."""
    return ShareSnapshotDTO(
        share_id=share_id,
        token=token,
        created_at=created_at,
        expires_at=expires_at,
        read_only=True,
        patient_ref=patient_ref,
        brief=brief,
        current_truth=current_truth,
    )
