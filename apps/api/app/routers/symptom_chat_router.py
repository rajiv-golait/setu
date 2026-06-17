"""Structured symptom assistant — routes to deterministic triage (non-diagnostic)."""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services import triage_service as triage

router = APIRouter(prefix="/chat", tags=["symptom-chat"])


class SymptomChatRequest(BaseModel):
    symptoms: list[str] = Field(default_factory=list)
    age: int | None = None
    existing_conditions: list[str] = Field(default_factory=list)
    lang: str = "en"


class SymptomChatResponse(BaseModel):
    priority: str
    recommendation: str
    message: str
    matched_rules: list[str]
    disclaimer: str = (
        "This is care routing guidance only — not a diagnosis. "
        "Please consult a qualified healthcare provider."
    )


@router.post("/triage", response_model=SymptomChatResponse)
async def symptom_chat(body: SymptomChatRequest) -> SymptomChatResponse:
    decision = triage.assess(
        body.symptoms,
        age=body.age,
        existing_conditions=body.existing_conditions,
    )
    msg = triage.message_for(decision.recommendation, body.lang)
    return SymptomChatResponse(
        priority=decision.priority,
        recommendation=decision.recommendation,
        message=msg,
        matched_rules=decision.matched_rules,
    )
