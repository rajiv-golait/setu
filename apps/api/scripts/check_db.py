"""Quick Supabase connectivity check. Run: python scripts/check_db.py"""
from __future__ import annotations

import asyncio
import sys

from sqlalchemy import text

from app.config import get_settings
from app.db.session import engine


async def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    if settings.database_url_unresolved:
        print("FAIL: [password] still in DATABASE_URL — set SUPABASE_DB_PASSWORD in apps/api/.env")
        return 1
    host = settings.DATABASE_URL.split("@", 1)[-1].split("/", 1)[0]
    print(f"Connecting to {host} ...")
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        print("OK: database connection works")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: {type(exc).__name__}: {exc}")
        return 1


if __name__ == "__main__":
    import sys

    if sys.platform == "win32":
        import asyncio

        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    raise SystemExit(asyncio.run(main()))
