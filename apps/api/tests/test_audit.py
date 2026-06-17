"""Audit trail: share view logging and patient access-log listing."""
from __future__ import annotations

import jwt
import pytest
from sqlalchemy import select

from app.db.models import AccessLog, Patient

pytestmark = pytest.mark.asyncio

_SECRET = "test-jwt-secret-at-least-32-bytes-long"


def _token(sub: str, role: str | None = None) -> str:
    claims: dict = {"sub": sub, "aud": "authenticated"}
    if role is not None:
        claims["app_metadata"] = {"role": role}
    return jwt.encode(claims, _SECRET, algorithm="HS256")


def _bearer(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_enabled(monkeypatch):
    from app import config

    monkeypatch.setattr(config.settings, "SUPABASE_ENABLED", True)
    monkeypatch.setattr(config.settings, "SUPABASE_JWT_SECRET", _SECRET)


async def _seed_patient_with_brief(
    client, session_factory, pid: str = "pat_audit", *, sub: str = "u_pat_audit"
):
    from datetime import date

    from app.db.models import Claim, Document
    from app.schemas.claims import Claim as ClaimSchema
    from app.seed.fixtures import demo_claims
    from app.services.memory.reducer import grouping_key

    async with session_factory() as db:
        db.add(
            Patient(
                id=pid,
                display_name="Audit",
                lang_pref="mr",
                patient_token="tok_audit",
                supabase_user_id=sub,
            )
        )
        for d in ("doc_rx01", "doc_lab1", "doc_disc"):
            db.add(
                Document(
                    id=d,
                    patient_id=pid,
                    doc_type="other",
                    storage_path=f"/x/{d}",
                    mime="image/jpeg",
                    status="extracted",
                )
            )
        for c in demo_claims(pid):
            schema = ClaimSchema(
                claim_id=c["claim_id"],
                type=c["type"],
                fields=c["fields"],
                confidence=c["confidence"],
                observed_at=date.fromisoformat(c["observed_at"]) if c.get("observed_at") else None,
                needs_review=c.get("needs_review", False),
            )
            db.add(
                Claim(
                    id=c["claim_id"],
                    patient_id=pid,
                    document_id=c["document_id"],
                    claim_type=c["type"],
                    normalized_key=grouping_key(schema),
                    fields=c["fields"],
                    confidence=c["confidence"],
                    observed_at=schema.observed_at,
                    needs_review=c.get("needs_review", False),
                )
            )
        await db.commit()

    headers = _bearer(_token(sub, "patient"))
    r = await client.post(f"/api/v1/patients/{pid}/brief", headers=headers)
    assert r.status_code == 201, r.text
    r = await client.post("/api/v1/shares", json={"patient_id": pid}, headers=headers)
    assert r.status_code == 201, r.text
    return r.json()["token"]


async def test_brief_view_creates_access_log(client, session_factory):
    token = await _seed_patient_with_brief(client, session_factory)
    r = await client.get(f"/api/v1/brief/{token}")
    assert r.status_code == 200, r.text

    async with session_factory() as db:
        rows = (await db.execute(select(AccessLog))).scalars().all()
    assert len(rows) == 1
    assert rows[0].actor_role == "public"
    assert rows[0].action == "view"
    assert rows[0].resource == "brief"


async def test_patient_can_list_access_log(client, session_factory, auth_enabled):
    pid = "pat_audit2"
    sub = "u_pat_audit2"
    token = await _seed_patient_with_brief(client, session_factory, pid, sub=sub)
    await client.get(f"/api/v1/brief/{token}")

    r = await client.get(
        f"/api/v1/patients/{pid}/access-log",
        headers=_bearer(_token(sub, "patient")),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert len(body) >= 1
    assert "actor_id" not in body[0]
    assert body[0]["actor_role"] == "public"
