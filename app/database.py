"""
Database configuration and session management.
This module handles SQLAlchemy engine, session factory, and database dependencies.
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Generator

from app.config import settings

# Create SQLAlchemy engine with optimized settings
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=settings.debug
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for all models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency to get database session.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        ```python
        @app.get("/users/")
        async def get_users(db: Session = Depends(get_db)):
            return db.query(User).all()
        ```
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """
    Create all database tables.
    This should be called during application startup.
    """
    # Import models here to avoid circular imports
    from app.models.user import User
    from app.models.task import Task
    from app.models.meeting import Meeting, MeetingParticipant, MeetingReminder
    
    Base.metadata.create_all(bind=engine)
