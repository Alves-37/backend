from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.db.session import AsyncSessionLocal

router = APIRouter()

async def get_db_session():
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/healthz", tags=["Health"])
async def health_check(db: AsyncSession = Depends(get_db_session)):
    """Check if the API is running and can connect to the database."""
    try:
        await db.execute(text("SELECT 1"))
        
        # Listar tabelas existentes
        result = await db.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        
        return {
            "status": "ok", 
            "database_connection": "ok",
            "tables": tables,
            "table_count": len(tables)
        }
    except Exception as e:
        return {"status": "error", "database_connection": "failed", "details": str(e)}
