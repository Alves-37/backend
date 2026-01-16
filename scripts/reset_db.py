import argparse
import asyncio
import sys
import os

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Garantir que o pacote `app` seja importável ao executar via `python scripts/reset_db.py`
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.core.config import settings


async def show_status(conn) -> None:
    schemas = (await conn.execute(
        text(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name NOT IN ('pg_catalog', 'information_schema')
            ORDER BY schema_name
            """
        )
    )).scalars().all()

    pdv_tables = (await conn.execute(
        text(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'pdv' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
    )).scalars().all()

    print("Schemas:", ", ".join(schemas) if schemas else "(none)")
    print("PDV tables:", ", ".join(pdv_tables) if pdv_tables else "(none)")


async def reset_pdv_schema(dry_run: bool) -> None:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            if dry_run:
                print("[DRY-RUN] Status before:")
            else:
                print("Status before:")
            await show_status(conn)

            stmts = [
                "DROP SCHEMA IF EXISTS pdv CASCADE",
                "CREATE SCHEMA IF NOT EXISTS pdv",
            ]
            for s in stmts:
                if dry_run:
                    print("[DRY-RUN]", s)
                else:
                    await conn.execute(text(s))

            if dry_run:
                print("[DRY-RUN] Status after:")
            else:
                print("Status after:")
            await show_status(conn)
    finally:
        await engine.dispose()


async def reset_all(dry_run: bool) -> None:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            if dry_run:
                print("[DRY-RUN] Status before:")
            else:
                print("Status before:")
            await show_status(conn)

            stmts = [
                "DROP SCHEMA IF EXISTS pdv CASCADE",
                "DROP TABLE IF EXISTS tenants CASCADE",
                "CREATE SCHEMA IF NOT EXISTS pdv",
            ]
            for s in stmts:
                if dry_run:
                    print("[DRY-RUN]", s)
                else:
                    await conn.execute(text(s))

            if dry_run:
                print("[DRY-RUN] Status after:")
            else:
                print("Status after:")
            await show_status(conn)
    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Reset database objects used by PDV backend37.")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Also drop the global tenants table (dangerous).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print statements without executing.",
    )
    args = parser.parse_args()

    print("This operation is destructive.")
    print("Tip: pare o backend (uvicorn) antes de resetar, senão as tabelas podem ser recriadas automaticamente no startup.")
    print("Target DB:", settings.DATABASE_URL)
    print("Mode:", "ALL (pdv schema + tenants)" if args.all else "PDV ONLY (pdv schema)")
    confirm = input('Type RESETAR to confirm: ').strip()
    if confirm != "RESETAR":
        print("Cancelled.")
        return 1

    if args.all:
        asyncio.run(reset_all(args.dry_run))
    else:
        asyncio.run(reset_pdv_schema(args.dry_run))

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
