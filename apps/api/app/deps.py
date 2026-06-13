"""Shared FastAPI dependencies. The entire identity surface is X-Patient-Token."""
from __future__ import annotations

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.errors import AppError, NOT_FOUND, VALIDATION_ERROR


async def get_patient_token(x_patient_token: str | None = Header(default=None)) -> str:
    if not x_patient_token:
        raise AppError(VALIDATION_ERROR, "Missing X-Patient-Token header", retryable=False)
    return x_patient_token


async def require_patient(
    token: str = Depends(get_patient_token),
    db: AsyncSession = Depends(get_db),
) -> Patient:
    patient = (
        await db.execute(select(Patient).where(Patient.patient_token == token))
    ).scalar_one_or_none()
    if patient is None:
        raise AppError(NOT_FOUND, "Patient not found for token", retryable=False)
    return patient
