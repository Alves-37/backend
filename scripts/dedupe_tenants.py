import argparse
import asyncio
import os
import sys
import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# Garantir que o pacote `app` seja importável ao executar via `python scripts/...`
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from app.core.config import settings


PDV_TABLES = [
    "pdv.usuarios",
    "pdv.produtos",
    "pdv.clientes",
    "pdv.vendas",
    "pdv.empresa_config",
    "pdv.dividas",
    "pdv.itens_venda",
    "pdv.itens_divida",
    "pdv.pagamentos_divida",
]


async def _list_tenants(conn, name: str | None):
    if name:
        rows = (await conn.execute(
            text(
                """
                SELECT id::text, nome, ativo, created_at
                FROM tenants
                WHERE nome = :nome
                ORDER BY created_at
                """
            ),
            {"nome": name},
        )).all()
    else:
        rows = (await conn.execute(
            text(
                """
                SELECT id::text, nome, ativo, created_at
                FROM tenants
                ORDER BY created_at
                """
            )
        )).all()

    return rows


async def dedupe(name: str, dry_run: bool) -> None:
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    try:
        async with engine.begin() as conn:
            tenants = await _list_tenants(conn, name)
            print(f"Tenants com nome='{name}':")
            for t in tenants:
                print("-", t)

            if len(tenants) <= 1:
                print("Nada para deduplicar.")
                return

            keep_id = uuid.UUID(tenants[0][0])
            dup_ids = [uuid.UUID(t[0]) for t in tenants[1:]]

            print("\nManter:", keep_id)
            print("Duplicados:", ", ".join(str(x) for x in dup_ids))

            # 1) Atualizar dados do schema pdv para apontar para o tenant mantido
            for table in PDV_TABLES:
                stmt = text(
                    f"UPDATE {table} SET tenant_id = :keep WHERE tenant_id = ANY(CAST(:dups AS uuid[]))"
                )
                params = {"keep": keep_id, "dups": dup_ids}

                if dry_run:
                    print("[DRY-RUN]", stmt.text, params)
                else:
                    await conn.execute(stmt, params)

            # 2) Remover tenants duplicados
            del_stmt = text(
                """
                DELETE FROM tenants
                WHERE id = ANY(CAST(:dups AS uuid[]))
                """
            )
            if dry_run:
                print("[DRY-RUN]", del_stmt.text, {"dups": dup_ids})
            else:
                await conn.execute(del_stmt, {"dups": dup_ids})

            if dry_run:
                print("[DRY-RUN] Final tenants:")
            else:
                print("Final tenants:")
            final = await _list_tenants(conn, name)
            for t in final:
                print("-", t)

    finally:
        await engine.dispose()


def main() -> int:
    parser = argparse.ArgumentParser(description="Deduplica tenants por nome e migra tenant_id nas tabelas pdv.*")
    parser.add_argument(
        "--name",
        default="Default",
        help="Nome do tenant para deduplicar (default: Default)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Mostra SQL sem executar.",
    )
    args = parser.parse_args()

    print("This operation is destructive.")
    print("Tip: pare o backend (uvicorn) antes de rodar.")
    print("Target DB:", settings.DATABASE_URL)
    print("Target tenant name:", args.name)

    confirm = input('Type DEDUPE to confirm: ').strip()
    if confirm != "DEDUPE":
        print("Cancelled.")
        return 1

    asyncio.run(dedupe(args.name, args.dry_run))
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
