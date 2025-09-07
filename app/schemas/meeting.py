from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from app.models.meeting import MeetingType, MeetingStatus, ParticipantRole, ResponseStatus


class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    meeting_date: datetime = Field(..., description="Meeting date and time")
    duration_minutes: int = Field(60, ge=1, le=1440, description="Meeting duration in minutes (1-1440)")
    location: Optional[str] = Field(None, max_length=255, description="Meeting location")
    meeting_url: Optional[str] = Field(None, max_length=500, description="Virtual meeting URL")
    reminder_minutes: int = Field(15, ge=0, le=10080, description="Reminder time in minutes before meeting (0-10080)")
    meeting_type: MeetingType = Field(MeetingType.IN_PERSON, description="Type of meeting")
    participant_emails: Optional[List[str]] = Field(None, description="List of participant email addresses")

    @validator('meeting_date')
    def validate_meeting_date(cls, v):
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if v.tzinfo is None:
            # If the input datetime is naive, assume it's UTC
            v = v.replace(tzinfo=timezone.utc)
        if v <= now:
            raise ValueError('Meeting date must be in the future')
        return v

    @validator('participant_emails')
    def validate_participant_emails(cls, v):
        if v:
            for email in v:
                if '@' not in email:
                    raise ValueError(f'Invalid email format: {email}')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Project Planning Meeting",
                "description": "Discuss project timeline and deliverables",
                "meeting_date": "2024-01-15T10:00:00Z",
                "duration_minutes": 60,
                "location": "Conference Room A",
                "meeting_url": "https://meet.google.com/abc-defg-hij",
                "reminder_minutes": 15,
                "meeting_type": "in_person",
                "participant_emails": ["john@example.com", "jane@example.com"]
            }
        }


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    meeting_date: Optional[datetime] = None
    duration_minutes: Optional[int] = Field(None, ge=1, le=1440)
    location: Optional[str] = Field(None, max_length=255)
    meeting_url: Optional[str] = Field(None, max_length=500)
    reminder_minutes: Optional[int] = Field(None, ge=0, le=10080)
    meeting_type: Optional[MeetingType] = None
    status: Optional[MeetingStatus] = None
    participant_emails: Optional[List[str]] = None

    @validator('meeting_date')
    def validate_meeting_date(cls, v):
        if v:
            from datetime import datetime, timezone
            now = datetime.now(timezone.utc)
            if v.tzinfo is None:
                # If the input datetime is naive, assume it's UTC
                v = v.replace(tzinfo=timezone.utc)
            if v <= now:
                raise ValueError('Meeting date must be in the future')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Updated Project Planning Meeting",
                "description": "Updated discussion topics",
                "meeting_date": "2024-01-15T11:00:00Z",
                "duration_minutes": 90,
                "location": "Conference Room B",
                "reminder_minutes": 30
            }
        }


class MeetingParticipantResponse(BaseModel):
    user_id: int
    username: Optional[str] = None
    email: Optional[str] = None
    role: ParticipantRole
    response_status: ResponseStatus

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "role": "attendee",
                "response_status": "accepted"
            }
        }


class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    meeting_date: datetime
    duration_minutes: int
    location: Optional[str]
    meeting_url: Optional[str]
    reminder_minutes: int
    created_by: int
    created_at: datetime
    updated_at: datetime
    is_active: bool
    meeting_type: MeetingType
    status: MeetingStatus

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "title": "Project Planning Meeting",
                "description": "Discuss project timeline and deliverables",
                "meeting_date": "2024-01-15T10:00:00Z",
                "duration_minutes": 60,
                "location": "Conference Room A",
                "meeting_url": "https://meet.google.com/abc-defg-hij",
                "reminder_minutes": 15,
                "created_by": 1,
                "created_at": "2024-01-10T09:00:00Z",
                "updated_at": "2024-01-10T09:00:00Z",
                "is_active": True,
                "meeting_type": "in_person",
                "status": "scheduled",
                "participants": [
                    {
                        "user_id": 1,
                        "username": "john_doe",
                        "email": "john@example.com",
                        "role": "organizer",
                        "response_status": "accepted"
                    }
                ]
            }
        }


class MeetingListResponse(BaseModel):
    meetings: List[MeetingResponse]
    total: int
    page: int
    size: int

    class Config:
        json_schema_extra = {
            "example": {
                "meetings": [
                    {
                        "id": 1,
                        "title": "Project Planning Meeting",
                        "meeting_date": "2024-01-15T10:00:00Z",
                        "status": "scheduled"
                    }
                ],
                "total": 1,
                "page": 1,
                "size": 10
            }
        }


class MeetingReminderRequest(BaseModel):
    meeting_id: int
    reminder_minutes: int = Field(15, ge=0, le=10080, description="Minutes before meeting to send reminder")

    class Config:
        json_schema_extra = {
            "example": {
                "meeting_id": 1,
                "reminder_minutes": 30
            }
        }


