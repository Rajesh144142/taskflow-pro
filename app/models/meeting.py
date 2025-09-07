"""
Meeting model definitions.
This module contains SQLAlchemy models for meeting management and email reminders.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from enum import Enum


class MeetingType(str, Enum):
    """Meeting type enumeration."""
    IN_PERSON = "in_person"
    VIRTUAL = "virtual"
    HYBRID = "hybrid"


class MeetingStatus(str, Enum):
    """Meeting status enumeration."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ParticipantRole(str, Enum):
    """Participant role enumeration."""
    ORGANIZER = "organizer"
    ATTENDEE = "attendee"
    OPTIONAL = "optional"


class ResponseStatus(str, Enum):
    """Response status enumeration."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    TENTATIVE = "tentative"


class ReminderType(str, Enum):
    """Reminder type enumeration."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"


class ReminderStatus(str, Enum):
    """Reminder status enumeration."""
    SENT = "sent"
    FAILED = "failed"
    PENDING = "pending"


class Meeting(Base):
    """
    Meeting model for meeting management and email reminders.
    
    Attributes:
        id: Primary key
        title: Meeting title
        description: Meeting description
        meeting_date: Meeting date and time
        duration_minutes: Meeting duration in minutes
        location: Meeting location
        meeting_url: Virtual meeting URL
        reminder_minutes: Minutes before meeting to send reminder
        created_by: Foreign key to users table (organizer)
        created_at: Meeting creation timestamp
        updated_at: Last update timestamp
        is_active: Meeting status flag
        meeting_type: Type of meeting (in_person, virtual, hybrid)
        status: Meeting status (scheduled, in_progress, completed, cancelled)
        
    Relationships:
        organizer: Many-to-one relationship with users
        participants: One-to-many relationship with meeting participants
        reminders: One-to-many relationship with meeting reminders
    """
    
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    meeting_date = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, default=60)
    location = Column(String(255))
    meeting_url = Column(String(500))  # For virtual meetings
    reminder_minutes = Column(Integer, default=15)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)
    meeting_type = Column(String(50), default=MeetingType.IN_PERSON)
    status = Column(String(50), default=MeetingStatus.SCHEDULED)

    # Relationships
    organizer = relationship("User", foreign_keys=[created_by])
    participants = relationship("MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan")
    reminders = relationship("MeetingReminder", back_populates="meeting", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="meetings_duration_check"),
        CheckConstraint("reminder_minutes >= 0", name="meetings_reminder_check"),
        CheckConstraint("meeting_type IN ('in_person', 'virtual', 'hybrid')", name="meetings_type_check"),
        CheckConstraint("status IN ('scheduled', 'in_progress', 'completed', 'cancelled')", name="meetings_status_check"),
    )


class MeetingParticipant(Base):
    """
    Meeting participant model for managing meeting attendees.
    
    Attributes:
        id: Primary key
        meeting_id: Foreign key to meetings table
        user_id: Foreign key to users table
        role: Participant role (organizer, attendee, optional)
        response_status: Response status (pending, accepted, declined, tentative)
        created_at: Participation creation timestamp
        
    Relationships:
        meeting: Many-to-one relationship with meetings
        user: Many-to-one relationship with users
    """
    
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(50), default=ParticipantRole.ATTENDEE)
    response_status = Column(String(50), default=ResponseStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", back_populates="meeting_participations")

    # Constraints
    __table_args__ = (
        CheckConstraint("role IN ('organizer', 'attendee', 'optional')", name="participants_role_check"),
        CheckConstraint("response_status IN ('pending', 'accepted', 'declined', 'tentative')", name="participants_response_check"),
    )


class MeetingReminder(Base):
    """
    Meeting reminder model for tracking sent reminders.
    
    Attributes:
        id: Primary key
        meeting_id: Foreign key to meetings table
        user_id: Foreign key to users table
        reminder_sent_at: Timestamp when reminder was sent
        reminder_type: Type of reminder (email, sms, push)
        status: Reminder status (sent, failed, pending)
        
    Relationships:
        meeting: Many-to-one relationship with meetings
        user: Many-to-one relationship with users
    """
    
    __tablename__ = "meeting_reminders"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    reminder_sent_at = Column(DateTime(timezone=True), server_default=func.now())
    reminder_type = Column(String(50), default=ReminderType.EMAIL)
    status = Column(String(50), default=ReminderStatus.SENT)

    # Relationships
    meeting = relationship("Meeting", back_populates="reminders")
    user = relationship("User")

    # Constraints
    __table_args__ = (
        CheckConstraint("reminder_type IN ('email', 'sms', 'push')", name="reminders_type_check"),
        CheckConstraint("status IN ('sent', 'failed', 'pending')", name="reminders_status_check"),
    )
