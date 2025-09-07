"""
Task model definition.
This module contains the SQLAlchemy model for task management.
"""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Integer
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class TaskStatus(str, enum.Enum):
    """Task status enumeration."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class TaskPriority(str, enum.Enum):
    """Task priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Task(Base):
    """
    Task model for task management.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to users table
        title: Task title
        description: Task description
        status: Task status (pending, in_progress, completed)
        priority: Task priority (low, medium, high)
        created_at: Task creation timestamp
        updated_at: Last update timestamp
        
    Relationships:
        user: Many-to-one relationship with users
    """
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tasks")
