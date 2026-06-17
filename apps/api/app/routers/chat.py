"""Saathi chatbot endpoint — grounded on the patient's CurrentTruth."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.deps import get_db, require_patient_access
from app.errors import not_found
from app.services.memory.persistence import load_current_truth
from app.services.saathi import SaathiResponse, chat

router = APIRouter(prefix="/patients/{patient_id}/saathi", tags=["saathi"])


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    lang: str = "mr"


@router.post("", response_model=SaathiResponse)
async def saathi_chat(
    patient_id: str,
    body: ChatRequest,
    patient=Depends(require_patient_access),
    db: AsyncSession = Depends(get_db),
) -> SaathiResponse:
    current_truth = await load_current_truth(db, patient_id)
    if current_truth is None:
        raise not_found("CurrentTruth", patient_id)
    return await chat(
        patient_id=patient_id,
        message=body.message,
        history=body.history,
        current_truth=current_truth,
        lang=body.lang,
    )
