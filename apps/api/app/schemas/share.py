"""Share + Snapshot DTOs."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.brief import DoctorBriefDTO
from app.schemas.memory import CurrentTruthDTO


class ShareCreateRequest(BaseModel):
    patient_id: str
    expires_in: int | None = None  # seconds; default applied server-side


class ShareDTO(BaseModel):
    """Returned when a share is created — carries the link + QR for the patient."""

    share_id: str
    token: str
    url: str
    qr_svg: str  # inline SVG string (scannable)
    created_at: datetime
    expires_at: datetime | None = None


class ShareSnapshotDTO(BaseModel):
    """Public, frozen, read-only snapshot fetched by the doctor."""

    share_id: str
    token: str
    created_at: datetime
    expires_at: datetime | None = None
    read_only: bool = True
    patient_ref: str
    brief: DoctorBriefDTO
    current_truth: CurrentTruthDTO
    audience: Literal["patient", "specialist"] = "patient"
