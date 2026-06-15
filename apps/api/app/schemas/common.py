"""Patient, Document, and other shared resource DTOs."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.schemas.claims import ClaimsJSON


class PatientCreateRequest(BaseModel):
    display_name: str | None = None
    lang_pref: str = "mr"


class PatientDTO(BaseModel):
    id: str
    display_name: str | None = None
    lang_pref: str = "mr"
    created_at: datetime
    # patient_token only returned on creation; None otherwise.
    patient_token: str | None = None


class DocumentUploadResponse(BaseModel):
    document_id: str
    job_id: str
    status: str


class DocumentDTO(BaseModel):
    id: str
    patient_id: str
    doc_type: str | None = None
    mime: str | None = None
    source: str = "upload"
    status: str = "pending"
    uploaded_at: datetime
    extraction: ClaimsJSON | None = None


class DocumentListItem(BaseModel):
    id: str
    patient_id: str
    doc_type: str | None = None
    mime: str | None = None
    source: str = "upload"
    status: str = "pending"
    uploaded_at: datetime


class ReferralCreateRequest(BaseModel):
    patient_id: str
    specialty: str
    reason: str | None = None


class ReferralDTO(BaseModel):
    id: str
    patient_id: str
    brief_id: str | None = None
    specialty: str
    reason: str | None = None
    created_at: datetime
