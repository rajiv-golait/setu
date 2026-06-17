"""Find working Supabase pooler region. Run from apps/api: python scripts/find_pooler.py"""
from __future__ import annotations

import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from urllib.parse import quote_plus

import psycopg

from app.config import get_settings

REGIONS = [
    "ap-south-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "ap-northeast-2",
    "eu-central-1",
    "eu-west-1",
    "eu-west-2",
    "eu-west-3",
    "eu-north-1",
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "ca-central-1",
    "sa-east-1",
]
POOLER_PREFIXES = ("aws-0", "aws-1")


async def try_region(ref: str, password: str, prefix: str, region: str) -> bool:
    host = f"{prefix}-{region}.pooler.supabase.com"
    user = f"postgres.{ref}"
    conninfo = (
        f"host={host} port=5432 dbname=postgres user={user} "
        f"password={password} sslmode=require"
    )
    try:
        async with await psycopg.AsyncConnection.connect(conninfo, connect_timeout=8) as conn:
            await conn.execute("SELECT 1")
        return True
    except Exception as exc:
        print(f"({type(exc).__name__}: {str(exc)[:80]})")
        return False


async def main() -> int:
    get_settings.cache_clear()
    settings = get_settings()
    pwd = settings.SUPABASE_DB_PASSWORD
    ref = "sevwzahlsunwqbiowbcx"
    if not pwd:
        print("Set SUPABASE_DB_PASSWORD in apps/api/.env first")
        return 1
    for prefix in POOLER_PREFIXES:
        for region in REGIONS:
            label = f"{prefix}-{region}"
            print(f"Trying {label} ...", end=" ", flush=True)
            if await try_region(ref, pwd, prefix, region):
                print("OK")
                encoded = quote_plus(pwd)
            print(
                f"\nUse this in apps/api/.env (set SUPABASE_DB_PASSWORD separately):\n"
                f"DATABASE_URL=postgresql+psycopg://postgres.{ref}:[password]"
                f"@{prefix}-{region}.pooler.supabase.com:5432/postgres?sslmode=require"
            )
                return 0
            print("no")
    print("No pooler region matched - copy URI from Supabase Dashboard -> Database")
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
