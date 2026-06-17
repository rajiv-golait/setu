"""Try pooler on ports 5432 and 6543 for ap-south-1 with verbose errors."""
from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import psycopg

from app.config import get_settings

REF = "sevwzahlsunwqbiowbcx"
HOST = "aws-0-ap-south-1.pooler.supabase.com"


async def try_conn(port: int, user: str) -> None:
    pwd = get_settings().SUPABASE_DB_PASSWORD
    conninfo = (
        f"host={HOST} port={port} dbname=postgres user={user} "
        f"password={pwd} sslmode=require connect_timeout=12"
    )
    print(f"port={port} user={user} ...", end=" ", flush=True)
    try:
        async with await psycopg.AsyncConnection.connect(conninfo) as conn:
            await conn.execute("SELECT 1")
        print("OK")
    except Exception as exc:
        print(type(exc).__name__, str(exc)[:200])


async def main() -> None:
    get_settings.cache_clear()
    for port in (5432, 6543):
        await try_conn(port, f"postgres.{REF}")
        await try_conn(port, "postgres")


if __name__ == "__main__":
    asyncio.run(main())
