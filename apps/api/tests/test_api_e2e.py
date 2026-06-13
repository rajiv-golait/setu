"""E2E happy path through the HTTP surface: create patient -> regen brief from
seeded claims -> create share -> fetch public snapshot. This is the demo centerpiece.
"""
from __future__ import annotations

from datetime import date

import pytest

from app.db.models import Claim, Document, Patient
from app.schemas.claims import Claim as ClaimSchema
from app.seed.fixtures import demo_claims
from app.services.memory.reducer import grouping_key

pytestmark = pytest.mark.asyncio


async def _seed_claims(session_factory, patient_id: str):
    async with session_factory() as db:
        db.add(Patient(id=patient_id, display_name="62F", lang_pref="mr", patient_token="tok_e2e"))
        for d in ("doc_rx01", "doc_lab1", "doc_disc"):
            db.add(Document(id=d, patient_id=patient_id, doc_type="other", storage_path=f"/x/{d}", mime="image/jpeg", status="extracted"))
        for c in demo_claims(patient_id):
            schema = ClaimSchema(
                claim_id=c["claim_id"], type=c["type"], fields=c["fields"],
                confidence=c["confidence"],
                observed_at=date.fromisoformat(c["observed_at"]) if c.get("observed_at") else None,
                needs_review=c.get("needs_review", False),
            )
            db.add(Claim(
                id=c["claim_id"], patient_id=patient_id, document_id=c["document_id"],
                claim_type=c["type"], normalized_key=grouping_key(schema), fields=c["fields"],
                confidence=c["confidence"], observed_at=schema.observed_at, needs_review=c.get("needs_review", False),
            ))
        await db.commit()


async def test_brief_share_public_snapshot(client, session_factory):
    pid = "pat_e2e"
    await _seed_claims(session_factory, pid)

    # Regenerate brief from claims.
    r = await client.post(f"/api/v1/patients/{pid}/brief")
    assert r.status_code == 201, r.text
    brief = r.json()
    assert brief["one_line"]
    assert any(f["type"] == "needs_review" for f in brief["flags"])

    # Memory is populated + schema-valid.
    r = await client.get(f"/api/v1/patients/{pid}/memory")
    assert r.status_code == 200
    assert len(r.json()["entries"]) > 0

    # Create a share — returns QR + url.
    r = await client.post("/api/v1/shares", json={"patient_id": pid})
    assert r.status_code == 201, r.text
    share = r.json()
    assert share["qr_svg"].lstrip().startswith("<svg")
    token = share["token"]

    # Public fetch — no token header.
    r = await client.get(f"/api/v1/shares/{token}")
    assert r.status_code == 200
    snap = r.json()
    assert snap["read_only"] is True
    assert snap["brief"]["brief_id"] == brief["brief_id"]


async def test_missing_patient_token_returns_error_envelope(client):
    r = await client.get("/api/v1/jobs/job_nope")
    assert r.status_code == 404
    body = r.json()
    assert body["error"]["code"] == "NOT_FOUND"
    assert "retryable" in body["error"]


async def test_unknown_patient_is_not_found(client):
    r = await client.get("/api/v1/patients/pat_missing")
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "NOT_FOUND"
