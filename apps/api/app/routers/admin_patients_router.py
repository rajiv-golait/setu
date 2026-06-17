"""Admin patient listing."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Patient
from app.db.session import get_db
from app.deps import require_admin
from app.schemas.common import PatientDTO

router = APIRouter(prefix="/admin/patients", tags=["admin"])


@router.get("", response_model=list[PatientDTO])
async def list_patients(
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(default=50, le=200),
) -> list[PatientDTO]:
    rows = (
        await db.execute(select(Patient).order_by(Patient.created_at.desc()).limit(limit))
    ).scalars().all()
    return [
        PatientDTO(
            id=r.id,
            display_name=r.display_name,
            lang_pref=r.lang_pref,
            created_at=r.created_at,
        )
        for r in rows
    ]
