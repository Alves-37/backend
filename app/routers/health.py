from fastapi import APIRouter
import os

router = APIRouter()

@router.get("/healthz")
async def health_check():
    """Simple health check that doesn't depend on database connection."""
    return {
        "status": "ok",
        "message": "PDV3 Backend is healthy",
        "environment": os.getenv("RAILWAY_ENVIRONMENT", "development"),
        "port": os.getenv("PORT", "8000")
    }
