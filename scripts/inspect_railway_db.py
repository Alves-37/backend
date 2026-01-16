import os
import asyncio
import asyncpg


async def main():
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url:
        raise SystemExit(
            "DATABASE_URL não encontrado.\n"
            "Defina a variável de ambiente DATABASE_URL com o valor do Railway (Postgres.DATABASE_URL).\n"
            "Exemplo (PowerShell):\n"
            "  $env:DATABASE_URL=\"postgresql://user:pass@host:port/db\"\n"
            "  python scripts/inspect_railway_db.py\n"
        )

    conn = await asyncpg.connect(database_url)
    try:
        print("=== Connected ===")

        print("\n=== Schemas ===")
        schemas = await conn.fetch(
            """
            SELECT schema_name
            FROM information_schema.schemata
            ORDER BY schema_name
            """
        )
        for r in schemas:
            print("-", r["schema_name"])

        print("\n=== Tables (public + pdv) ===")
        tables = await conn.fetch(
            """
            SELECT table_schema, table_name
            FROM information_schema.tables
            WHERE table_type = 'BASE TABLE'
              AND table_schema IN ('public', 'pdv')
            ORDER BY table_schema, table_name
            """
        )
        for r in tables:
            print(f"- {r['table_schema']}.{r['table_name']}")

        print("\n=== Tenants (public.tenants) ===")
        try:
            tenants = await conn.fetch(
                """
                SELECT id::text AS id, nome, ativo, created_at
                FROM public.tenants
                ORDER BY created_at
                """
            )
            for t in tenants:
                print(f"- {t['id']} | {t['nome']} | ativo={t['ativo']} | created_at={t['created_at']}")
        except Exception as e:
            print("Falha ao ler public.tenants:", str(e))

        print("\n=== Counts by tenant_id ===")
        for table in ["pdv.produtos", "pdv.usuarios", "pdv.clientes", "pdv.vendas"]:
            try:
                rows = await conn.fetch(
                    f"""
                    SELECT tenant_id::text AS tenant_id, COUNT(*)::int AS count
                    FROM {table}
                    GROUP BY tenant_id
                    ORDER BY count DESC
                    """
                )
                print(f"\n-- {table} --")
                if not rows:
                    print("(sem registros)")
                for r in rows:
                    print(f"tenant_id={r['tenant_id']} | count={r['count']}")
            except Exception as e:
                print(f"\n-- {table} --")
                print("Falha:", str(e))

        print("\n=== Sample rows (pdv.produtos) ===")
        try:
            rows = await conn.fetch(
                """
                SELECT id::text AS id, tenant_id::text AS tenant_id, codigo, nome, preco_venda, ativo, created_at
                FROM pdv.produtos
                ORDER BY created_at DESC
                LIMIT 20
                """
            )
            for r in rows:
                print(
                    f"- id={r['id']} | tenant_id={r['tenant_id']} | codigo={r['codigo']} | nome={r['nome']} | preco_venda={r['preco_venda']} | ativo={r['ativo']} | created_at={r['created_at']}"
                )
        except Exception as e:
            print("Falha ao ler pdv.produtos:", str(e))

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
