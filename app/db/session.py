from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings

# Create engine with error handling
try:
    engine = create_async_engine(
        settings.DATABASE_URL, 
        pool_pre_ping=True,
        echo=False  # Set to True for SQL debugging
    )
    AsyncSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Database connection error: {e}")
    print(f"DATABASE_URL: {settings.DATABASE_URL}")
    raise

# Alias para compatibilidade
async_session = AsyncSessionLocal
