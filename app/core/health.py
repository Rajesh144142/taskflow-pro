"""
Health check endpoints.
"""

from fastapi import APIRouter
from app.core.startup import check_database_health
from app.config import settings

router = APIRouter()


@router.get("/health")
async def health_check():
    """General application health check."""
    return {"status": "healthy", "message": "API is running"}


@router.get("/health/db")
async def database_health_check():
    """Database connection health check."""
    is_healthy = await check_database_health()
    
    if is_healthy:
        return {
            "status": "healthy",
            "message": "Database connection successful",
            "database_url": _get_database_info()
        }
    else:
        return {
            "status": "unhealthy",
            "message": "Database connection failed",
            "database_url": _get_database_info()
        }


def _get_database_info():
    """Extract database connection info for display."""
    if '@' in settings.database_url:
        return settings.database_url.split('@')[1]
    return "configured"
