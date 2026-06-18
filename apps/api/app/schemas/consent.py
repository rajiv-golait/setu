"""DPDP consent DTOs.

Consent is recorded BEFORE a document enters the pipeline (see
services/ingestion.py). The consent_text shown to the user is stored verbatim
in the requested language for an auditable record.
"""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

ConsentChannel = Literal["web", "telegram"]
ConsentPurpose = Literal["document_processing"]

# Exact consent text rendered to the user, per language. Stored verbatim so the
# record reflects precisely what was agreed to.
CONSENT_TEXT = {
    "document_processing": {
        "mr": (
            "मी SETU ला माझ्या वैद्यकीय कागदपत्रांवर प्रक्रिया करण्यासाठी आणि "
            "त्यांचा सोपा सारांश तयार करण्यासाठी संमती देतो/देते. माझा डेटा "
            "फक्त याच कारणासाठी वापरला जाईल."
        ),
        "hi": (
            "मैं SETU को अपने चिकित्सा दस्तावेज़ों को संसाधित करने और उनका सरल "
            "सारांश बनाने के लिए सहमति देता/देती हूँ। मेरा डेटा केवल इसी उद्देश्य "
            "के लिए उपयोग किया जाएगा।"
        ),
        "en": (
            "I consent to SETU processing my medical documents and creating a "
            "plain-language summary. My data will be used only for this purpose."
        ),
    }
}


def consent_text(purpose: str, lang: str) -> str:
    by_lang = CONSENT_TEXT.get(purpose, CONSENT_TEXT["document_processing"])
    return by_lang.get(lang) or by_lang["en"]


class ConsentCreateRequest(BaseModel):
    patient_id: str
    purpose: ConsentPurpose = "document_processing"
    lang: str = "mr"
    channel: ConsentChannel = "web"


class ConsentDTO(BaseModel):
    consent_id: str
    patient_id: str
    purpose: str
    consent_text: str
    lang: str
    channel: str
    granted_at: datetime


class ConsentWithdrawRequest(BaseModel):
    patient_id: str
    purpose: ConsentPurpose = "document_processing"


class ConsentWithdrawResponse(BaseModel):
    withdrawn: bool
    patient_id: str
    purpose: str


class ConsentStatusDTO(BaseModel):
    patient_id: str
    purpose: str
    granted: bool
