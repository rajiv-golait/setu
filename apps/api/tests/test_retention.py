"""B7 — Document retention + purge. Transient raw storage, claims + hash kept.

  - upload stores a sha256 original_hash
  - DELETE /documents/{id} removes the raw FILE but keeps the row + claims + hash
  - purge_expired_documents purges only files older than the retention window
  - DELETE /patients/{id}/data cascades the purge across the patient's documents
"""
from __future__ import annotations

import io
import os
from datetime import datetime, timedelta, timezone

import pytest

from app.config import settings
from app.db.models import Claim, Document, Patient
from app.services import retention

pytestmark = pytest.mark.asyncio


async def _patient_with_consent(client, session_factory, pid):
    async with session_factory() as db:
        db.add(Patient(id=pid, display_name="T", lang_pref="mr", patient_token=f"tok_{pid}"))
        await db.commit()
    r = await client.post(
        "/api/v1/consent",
        json={"patient_id": pid, "purpose": "document_processing", "lang": "mr", "channel": "web"},
    )
    assert r.status_code == 201, r.text


def _file():
    return {"file": ("rx.jpg", io.BytesIO(b"raw-bytes-here"), "image/jpeg")}


async def test_upload_stores_hash_and_real_file(client, session_factory, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path))
    pid = "pat_r1"
    await _patient_with_consent(client, session_factory, pid)

    r = await client.post("/api/v1/documents", files=_file(), data={"patient_id": pid})
    assert r.status_code == 202, r.text
    doc_id = r.json()["document_id"]

    async with session_factory() as db:
        from sqlalchemy import select

        doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
        assert doc.original_hash and len(doc.original_hash) == 64  # sha256 hex
        assert os.path.isfile(doc.storage_path)  # raw file is on disk during care window


async def test_delete_document_purges_raw_keeps_claims(client, session_factory, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path))
    pid = "pat_r2"
    await _patient_with_consent(client, session_factory, pid)
    r = await client.post("/api/v1/documents", files=_file(), data={"patient_id": pid})
    doc_id = r.json()["document_id"]

    # Attach a claim so we can prove claims survive the purge.
    async with session_factory() as db:
        db.add(Claim(
            id="clm_keep", patient_id=pid, document_id=doc_id, claim_type="lab_result",
            normalized_key="hba1c", fields={"test_name": "HbA1c", "value": 9.1, "unit": "%"},
            confidence=0.9,
        ))
        await db.commit()
        from sqlalchemy import select

        path = (await db.execute(select(Document.storage_path).where(Document.id == doc_id))).scalar_one()
    assert os.path.isfile(path)

    # Purge.
    r = await client.delete(f"/api/v1/documents/{doc_id}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["raw_file_removed"] is True
    assert body["claims_retained"] is True
    assert body["original_hash"]

    async with session_factory() as db:
        from sqlalchemy import select

        doc = (await db.execute(select(Document).where(Document.id == doc_id))).scalar_one()
        assert doc.status == "purged"
        assert doc.purged_at is not None
        assert doc.original_hash  # hash kept
        claims = (await db.execute(select(Claim).where(Claim.document_id == doc_id))).scalars().all()
        assert len(claims) >= 1  # claims kept (our explicit one + any from the pipeline)
        assert any(c.id == "clm_keep" for c in claims)
    assert not os.path.isfile(path)  # raw file gone


async def test_purge_expired_only_old_documents(session_factory, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path))
    monkeypatch.setattr(settings, "RAW_RETENTION_DAYS", 30)
    old_path = os.path.join(tmp_path, "old.jpg")
    new_path = os.path.join(tmp_path, "new.jpg")
    open(old_path, "wb").write(b"old")
    open(new_path, "wb").write(b"new")

    async with session_factory() as db:
        db.add(Patient(id="pat_r3", display_name="T", lang_pref="mr", patient_token="tok_r3"))
        db.add(Document(
            id="doc_old", patient_id="pat_r3", storage_path=old_path, mime="image/jpeg",
            status="extracted", uploaded_at=datetime.now(timezone.utc) - timedelta(days=90),
        ))
        db.add(Document(
            id="doc_new", patient_id="pat_r3", storage_path=new_path, mime="image/jpeg",
            status="extracted", uploaded_at=datetime.now(timezone.utc),
        ))
        await db.commit()

    async with session_factory() as db:
        n = await retention.purge_expired_documents(db)
    assert n == 1
    assert not os.path.isfile(old_path)  # old purged
    assert os.path.isfile(new_path)      # new kept (still in window)


async def test_delete_my_data_cascade(client, session_factory, tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "STORAGE_PATH", str(tmp_path))
    pid = "pat_r4"
    await _patient_with_consent(client, session_factory, pid)
    await client.post("/api/v1/documents", files=_file(), data={"patient_id": pid})
    await client.post("/api/v1/documents", files={"file": ("a.png", io.BytesIO(b"x"), "image/png")}, data={"patient_id": pid})

    r = await client.delete(f"/api/v1/patients/{pid}/data")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["documents"] == 2
    assert body["raw_files_purged"] == 2

    async with session_factory() as db:
        from sqlalchemy import select

        docs = (await db.execute(select(Document).where(Document.patient_id == pid))).scalars().all()
        assert all(d.status == "purged" for d in docs)
        assert all(not os.path.isfile(d.storage_path) for d in docs)
