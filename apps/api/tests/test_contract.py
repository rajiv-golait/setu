"""Contract test: committed openapi.json must match the live FastAPI schema.

Fails on drift so the frontend's generated client never silently diverges.
If this fails after an intentional API change, run `make gen-client` and commit.
"""
from __future__ import annotations

import json
import os

import pytest

from app.main import app

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_COMMITTED = os.path.join(_REPO_ROOT, "packages", "contracts", "openapi.json")


def _normalize(schema: dict) -> str:
    return json.dumps(schema, indent=2, ensure_ascii=False, sort_keys=True) + "\n"


def test_endpoint_surface_present():
    """All required paths exist in the live schema."""
    paths = app.openapi()["paths"]
    expected = {
        "/api/v1/patients",
        "/api/v1/patients/{patient_id}",
        "/api/v1/documents",
        "/api/v1/documents/{document_id}",
        "/api/v1/jobs/{job_id}",
        "/api/v1/patients/{patient_id}/memory",
        "/api/v1/patients/{patient_id}/brief",
        "/api/v1/patients/{patient_id}/summary",
        "/api/v1/shares",
        "/api/v1/shares/{token}",
        "/api/v1/brief/{token}",
        "/api/v1/referrals",
    }
    missing = expected - set(paths)
    assert not missing, f"missing endpoints: {missing}"


@pytest.mark.skipif(not os.path.exists(_COMMITTED), reason="openapi.json not exported yet (run make gen-client)")
def test_openapi_no_drift():
    with open(_COMMITTED, encoding="utf-8") as f:
        committed = f.read()
    live = _normalize(app.openapi())
    assert committed == live, "openapi.json drift — run `make gen-client` and commit"
