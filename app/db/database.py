"""
Database session management for dependency injection.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_session

async def get_db_session() -> AsyncSession:
    """
    Dependency to get database session for FastAPI endpoints.
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
