"""Export the live FastAPI OpenAPI schema to packages/contracts/openapi.json.

Run via `make gen-client`. CI compares the committed file to this output to
detect contract drift.
"""
from __future__ import annotations

import json
import os

from app.main import app

# apps/api/scripts/ -> repo root is three levels up.
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.abspath(os.path.join(_HERE, "..", "..", ".."))
_OUT = os.path.join(_REPO_ROOT, "packages", "contracts", "openapi.json")


def export() -> str:
    schema = app.openapi()
    os.makedirs(os.path.dirname(_OUT), exist_ok=True)
    with open(_OUT, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False, sort_keys=True)
        f.write("\n")
    return _OUT


if __name__ == "__main__":
    path = export()
    print(f"Wrote {path}")
