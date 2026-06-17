"""Support tickets and admin dispute handling."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import SupportTicket
from app.db.session import get_db
from app.deps import get_auth_user_id, get_user_role, require_admin
from app.ids import new_id

router = APIRouter(prefix="/support", tags=["support"])


class TicketCreate(BaseModel):
    subject: str
    body: str


class TicketDTO(BaseModel):
    id: str
    subject: str
    body: str
    status: str
    reporter_role: str
    created_at: datetime


@router.post("/tickets", response_model=TicketDTO, status_code=201)
async def create_ticket(
    body: TicketCreate,
    auth_user_id: str | None = Depends(get_auth_user_id),
    role: str = Depends(get_user_role),
    db: AsyncSession = Depends(get_db),
) -> TicketDTO:
    row = SupportTicket(
        id=new_id("tkt"),
        reporter_id=auth_user_id,
        reporter_role=role,
        subject=body.subject,
        body=body.body,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return TicketDTO(
        id=row.id,
        subject=row.subject,
        body=row.body,
        status=row.status,
        reporter_role=row.reporter_role,
        created_at=row.created_at,
    )


@router.get("/tickets", response_model=list[TicketDTO])
async def list_tickets(
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> list[TicketDTO]:
    rows = (
        await db.execute(select(SupportTicket).order_by(SupportTicket.created_at.desc()))
    ).scalars().all()
    return [
        TicketDTO(
            id=r.id,
            subject=r.subject,
            body=r.body,
            status=r.status,
            reporter_role=r.reporter_role,
            created_at=r.created_at,
        )
        for r in rows
    ]


@router.patch("/tickets/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    status: str,
    _admin: str = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    row = (
        await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))
    ).scalar_one_or_none()
    if row is None:
        from app.errors import not_found

        raise not_found("Ticket", ticket_id)
    row.status = status
    await db.commit()
    return {"id": ticket_id, "status": status}
