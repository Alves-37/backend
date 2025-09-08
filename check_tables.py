import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check_tables():
    """Verifica quais tabelas existem no PostgreSQL."""
    engine = create_async_engine(settings.DATABASE_URL, pool_pre_ping=True)
    
    try:
        async with engine.begin() as conn:
            # Listar todas as tabelas
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = result.fetchall()
            
            print("Tabelas encontradas no PostgreSQL:")
            if tables:
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("  Nenhuma tabela encontrada!")
            
            # Verificar estrutura da tabela produtos se existir
            if any('produtos' in str(table[0]) for table in tables):
                print("\nEstrutura da tabela 'produtos':")
                result = await conn.execute(text("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'produtos'
                    ORDER BY ordinal_position;
                """))
                
                columns = result.fetchall()
                for col in columns:
                    print(f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}")
                    
    except Exception as e:
        print(f"Erro ao verificar tabelas: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_tables())
