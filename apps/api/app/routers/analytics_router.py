"""Admin analytics routes (Phase 6 F6)."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.deps import require_admin
from app.schemas.analytics import AnalyticsOverviewDTO
from app.services import analytics as svc

router = APIRouter(prefix="/admin/analytics", tags=["analytics"])


@router.get("/overview", response_model=AnalyticsOverviewDTO)
async def analytics_overview(
    from_dt: datetime | None = Query(default=None, alias="from"),
    to_dt: datetime | None = Query(default=None, alias="to"),
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> AnalyticsOverviewDTO:
    return await svc.overview(db, from_dt=from_dt, to_dt=to_dt)
