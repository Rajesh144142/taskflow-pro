"""
Application startup and shutdown handlers.
"""

import logging
from sqlalchemy import text

from app.config import settings
from app.database import engine, Base
from app.utils.scheduler import setup_scheduler, shutdown_scheduler

logger = logging.getLogger(__name__)


async def startup_handler():
    """Initialize application services."""
    logger.info("Starting Task Management Dashboard...")
    logger.info(f"Version: {settings.version}")
    logger.info(f"Server: http://{settings.host}:{settings.port}")
    
    await _setup_database()
    await _setup_scheduler()
    
    logger.info("Application startup completed")
    logger.info("Available endpoints:")
    logger.info("  - API Docs: /docs")
    logger.info("  - Next.js Frontend: Coming soon")
    logger.info("  - Health: /health")
    logger.info("  - DB Health: /health/db")


async def shutdown_handler():
    """Cleanup application services."""
    logger.info("Shutting down Task Management Dashboard...")
    
    try:
        shutdown_scheduler()
        logger.info("Scheduler stopped")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
    
    logger.info("Shutdown completed")


async def _setup_database():
    """Initialize database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


async def _setup_scheduler():
    """Initialize background scheduler."""
    try:
        setup_scheduler()
        logger.info("Background scheduler started")
    except Exception as e:
        logger.error(f"Scheduler setup failed: {e}")
        raise


async def check_database_health():
    """Check database connection health."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
