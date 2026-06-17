"""One-off: print alembic version and key tables on Supabase."""
from __future__ import annotations

import asyncio
import selectors
import sys
from urllib.parse import quote_plus

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.config import settings

pwd = settings.SUPABASE_DB_PASSWORD
ref = "sevwzahlsunwqbiowbcx"
url = (
    f"postgresql+psycopg://postgres.{ref}:{quote_plus(pwd)}"
    f"@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres?sslmode=require"
)


async def main() -> None:
    engine = create_async_engine(url)
    async with engine.connect() as conn:
        ver = (await conn.execute(text("SELECT version_num FROM alembic_version"))).scalar()
        tables = (
            await conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema='public' AND table_type='BASE TABLE' "
                    "ORDER BY table_name"
                )
            )
        ).scalars().all()
        col_checks: dict[str, bool] = {}
        for tbl, col in [
            ("appointments", "cancellation_reason"),
            ("appointments", "follow_up_for_appointment_id"),
            ("providers", "phone"),
            ("providers", "verification_status"),
        ]:
            r = await conn.execute(
                text(
                    "SELECT 1 FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=:t AND column_name=:c"
                ),
                {"t": tbl, "c": col},
            )
            col_checks[f"{tbl}.{col}"] = r.scalar() is not None
        rls = (
            await conn.execute(
                text(
                    "SELECT COUNT(*) FROM pg_tables "
                    "WHERE schemaname='public' AND rowsecurity = true"
                )
            )
        ).scalar()
    await engine.dispose()

    print("alembic_version:", ver)
    print("tables_with_rls_enabled:", rls)
    print("table_count:", len(tables))
    for t in tables:
        print(" -", t)
    for k, v in col_checks.items():
        print(f"{k}: {'yes' if v else 'no'}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(main(), loop_factory=lambda: asyncio.SelectorEventLoop(selectors.SelectSelector()))
    else:
        asyncio.run(main())
