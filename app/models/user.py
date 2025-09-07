"""
User model definition.
This module contains the SQLAlchemy model for user management.
"""

from sqlalchemy import Column, String, DateTime, Boolean, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    """
    User model for authentication and user management.
    
    Attributes:
        id: Primary key
        username: Unique username
        email: Unique email address
        hashed_password: Bcrypt hashed password
        is_active: Account status
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        
    Relationships:
        tasks: One-to-many relationship with tasks
        meetings_created: One-to-many relationship with meetings created
        meeting_participations: Many-to-many relationship with meetings
    """
    
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")
    meetings_created = relationship("Meeting", back_populates="organizer", cascade="all, delete-orphan")
    meeting_participations = relationship("MeetingParticipant", back_populates="user", cascade="all, delete-orphan")
