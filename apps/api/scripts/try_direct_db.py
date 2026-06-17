"""Try direct db.*.supabase.co connection (IPv6)."""
from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import psycopg

from app.config import get_settings


async def main() -> int:
    get_settings.cache_clear()
    pwd = get_settings().SUPABASE_DB_PASSWORD
    if not pwd:
        print("No SUPABASE_DB_PASSWORD")
        return 1
    hosts = [
        ("direct hostname", "db.sevwzahlsunwqbiowbcx.supabase.co", "postgres"),
        ("IPv6 literal", "2406:da14:311:1501:21de:dc64:3ece:215d", "postgres"),
    ]
    for label, host, user in hosts:
        print(f"Trying {label} ({host}) ...", end=" ", flush=True)
        conninfo = (
            f"host={host} port=5432 dbname=postgres user={user} "
            f"password={pwd} sslmode=require connect_timeout=15"
        )
        try:
            async with await psycopg.AsyncConnection.connect(conninfo) as conn:
                await conn.execute("SELECT 1")
            print("OK")
            return 0
        except Exception as exc:
            print(type(exc).__name__, str(exc)[:120])
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
