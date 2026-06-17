"""Access log DTOs — patient-visible audit trail (no actor_id/IP)."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AccessLogDTO(BaseModel):
    id: str
    actor_role: str
    action: str
    resource: str
    created_at: datetime
