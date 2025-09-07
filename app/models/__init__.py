"""
Models package for Task Management Dashboard.

This package contains all SQLAlchemy models for the application:
- User: User authentication and management
- Task: Task management
- Meeting: Meeting management with Google Calendar integration
- MeetingParticipant: Meeting attendees management
- MeetingReminder: Meeting reminder tracking
"""

from .user import User
from .task import Task, TaskStatus, TaskPriority
from .meeting import (
    Meeting, MeetingParticipant, MeetingReminder,
    MeetingType, MeetingStatus, ParticipantRole,
    ResponseStatus, ReminderType, ReminderStatus
)

__all__ = [
    # User models
    "User",
    
    # Task models
    "Task", "TaskStatus", "TaskPriority",
    
    # Meeting models
    "Meeting", "MeetingParticipant", "MeetingReminder",
    "MeetingType", "MeetingStatus", "ParticipantRole",
    "ResponseStatus", "ReminderType", "ReminderStatus"
]