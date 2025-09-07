from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func, text
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models.meeting import Meeting, MeetingParticipant, MeetingReminder, MeetingType, MeetingStatus, ParticipantRole, ResponseStatus
from app.models.user import User
import logging

logger = logging.getLogger(__name__)


class MeetingService:
    """Service for managing meetings and email reminders"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_meeting(self, meeting_data: dict, created_by: int, participant_emails: Optional[List[str]] = None) -> Optional[Meeting]:
        """Create a new meeting with email reminders"""
        try:
            # Create meeting
            meeting = Meeting(
                title=meeting_data['title'],
                description=meeting_data.get('description'),
                meeting_date=meeting_data['meeting_date'],
                duration_minutes=meeting_data.get('duration_minutes', 60),
                location=meeting_data.get('location'),
                meeting_url=meeting_data.get('meeting_url'),
                reminder_minutes=meeting_data.get('reminder_minutes', 15),
                meeting_type=meeting_data.get('meeting_type', MeetingType.IN_PERSON),
                created_by=created_by
            )
            
            self.db.add(meeting)
            self.db.flush()  # Get the meeting ID
            
            # Add organizer as participant
            organizer_participant = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=created_by,
                role=ParticipantRole.ORGANIZER,
                response_status=ResponseStatus.ACCEPTED
            )
            self.db.add(organizer_participant)
            
            # Add other participants if provided
            if participant_emails:
                await self._add_participants_by_email(meeting.id, participant_emails)
            
            self.db.commit()
            logger.info(f"Meeting created successfully: {meeting.id}")
            return meeting
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create meeting: {e}")
            return None
    
    async def get_meeting(self, meeting_id: int, user_id: int) -> Optional[Meeting]:
        """Get a meeting by ID (user must be participant or organizer)"""
        try:
            # First check if user is organizer
            meeting = self.db.execute(
                select(Meeting).where(
                    and_(
                        Meeting.id == meeting_id,
                        Meeting.created_by == user_id
                    )
                )
            ).scalar_one_or_none()
            
            if meeting:
                return meeting
            
            # If not organizer, check if user is participant
            meeting = self.db.execute(
                select(Meeting)
                .join(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)
                .where(
                    and_(
                        Meeting.id == meeting_id,
                        MeetingParticipant.user_id == user_id
                    )
                )
            ).scalar_one_or_none()
            
            return meeting
            
        except Exception as e:
            logger.error(f"Failed to get meeting {meeting_id}: {e}")
            return None
    
    async def get_user_meetings(self, user_id: int, page: int = 1, size: int = 10, status: Optional[MeetingStatus] = None) -> Dict[str, Any]:
        """Get meetings for a user with pagination"""
        try:
            offset = (page - 1) * size
            
            # Simplified query - just get meetings where user is organizer
            query = select(Meeting).where(Meeting.created_by == user_id)
            
            if status:
                query = query.where(Meeting.status == status)
            
            # Get total count
            total_query = select(func.count(Meeting.id)).where(Meeting.created_by == user_id)
            if status:
                total_query = total_query.where(Meeting.status == status)
            
            total = self.db.execute(total_query).scalar()
            
            # Get meetings with pagination
            meetings = self.db.execute(
                query.order_by(Meeting.meeting_date.desc())
                .offset(offset)
                .limit(size)
            ).scalars().all()
            
            return {
                'meetings': meetings,
                'total': total,
                'page': page,
                'size': size
            }
            
        except Exception as e:
            logger.error(f"Failed to get user meetings: {e}")
            return {'meetings': [], 'total': 0, 'page': page, 'size': size}
    
    async def update_meeting(self, meeting_id: int, user_id: int, update_data: dict) -> Optional[Meeting]:
        """Update a meeting (only organizer can update)"""
        try:
            meeting = self.db.execute(
                select(Meeting).where(
                    and_(
                        Meeting.id == meeting_id,
                        Meeting.created_by == user_id
                    )
                )
            ).scalar_one_or_none()
            
            if not meeting:
                return None
            
            # Update meeting fields
            for field, value in update_data.items():
                if hasattr(meeting, field) and value is not None:
                    setattr(meeting, field, value)
            
            
            self.db.commit()
            logger.info(f"Meeting updated successfully: {meeting_id}")
            return meeting
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to update meeting {meeting_id}: {e}")
            return None
    
    async def delete_meeting(self, meeting_id: int, user_id: int) -> bool:
        """Delete a meeting (only organizer can delete)"""
        try:
            meeting = self.db.execute(
                select(Meeting).where(
                    and_(
                        Meeting.id == meeting_id,
                        Meeting.created_by == user_id
                    )
                )
            ).scalar_one_or_none()
            
            if not meeting:
                return False
            
            
            # Delete meeting (cascade will handle participants and reminders)
            self.db.delete(meeting)
            self.db.commit()
            
            logger.info(f"Meeting deleted successfully: {meeting_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to delete meeting {meeting_id}: {e}")
            return False
    
    async def get_upcoming_meetings(self, user_id: int, hours_ahead: int = 24) -> List[Meeting]:
        """Get upcoming meetings for a user within specified hours"""
        try:
            now = datetime.utcnow()
            future_time = now + timedelta(hours=hours_ahead)
            
            meetings = self.db.execute(
                select(Meeting)
                .join(MeetingParticipant, Meeting.id == MeetingParticipant.meeting_id)
                .where(
                    and_(
                        MeetingParticipant.user_id == user_id,
                        Meeting.meeting_date >= now,
                        Meeting.meeting_date <= future_time,
                        Meeting.status == MeetingStatus.SCHEDULED
                    )
                )
                .order_by(Meeting.meeting_date.asc())
            ).scalars().all()
            
            return meetings
            
        except Exception as e:
            logger.error(f"Failed to get upcoming meetings: {e}")
            return []
    
    async def get_meetings_needing_reminders(self, reminder_minutes: int = 15) -> List[Dict[str, Any]]:
        """Get meetings that need reminders sent (for cron job)"""
        try:
            now = datetime.utcnow()
            
            # Get meetings that need reminders based on their individual reminder_minutes setting
            meetings_query = text("""
                SELECT m.id, m.title, m.meeting_date, m.duration_minutes, m.location, m.meeting_url,
                       m.reminder_minutes, m.meeting_type,
                       u.username, u.email as organizer_email
                FROM meetings m
                JOIN users u ON m.created_by = u.id
                WHERE m.meeting_date BETWEEN :now AND :future_time
                AND m.status = 'scheduled'
                AND m.is_active = true
                AND NOT EXISTS (
                    SELECT 1 FROM meeting_reminders mr 
                    WHERE mr.meeting_id = m.id 
                    AND mr.sent_at >= :now - INTERVAL '1 hour'
                )
            """)
            
            # Look for meetings in the next 30 minutes (covers all possible reminder times)
            meetings = self.db.execute(meetings_query, {
                'now': now,
                'future_time': now + timedelta(minutes=30)
            }).fetchall()
            
            # Filter meetings that need reminders based on their individual reminder_minutes
            result = []
            for meeting in meetings:
                meeting_datetime = meeting.meeting_date
                reminder_time = meeting_datetime - timedelta(minutes=meeting.reminder_minutes)
                
                # Check if current time is within 1 minute of the reminder time
                time_diff = abs((now - reminder_time).total_seconds())
                if time_diff <= 60:  # Within 1 minute of reminder time
                    # Get participants for this meeting
                    participants_query = text("""
                        SELECT u.id, u.username, u.email, mp.role, mp.response_status
                        FROM meeting_participants mp
                        JOIN users u ON mp.user_id = u.id
                        WHERE mp.meeting_id = :meeting_id
                    """)
                    
                    participants = self.db.execute(participants_query, {
                        'meeting_id': meeting.id
                    }).fetchall()
                    
                    result.append({
                        'meeting': meeting,
                        'participants': participants
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get meetings needing reminders: {e}")
            return []
    
    async def _add_participants_by_email(self, meeting_id: int, participant_emails: List[str]) -> None:
        """Add participants to a meeting by email addresses"""
        try:
            for email in participant_emails:
                # Find user by email
                user = self.db.execute(
                    select(User).where(User.email == email)
                ).scalar_one_or_none()
                
                if user:
                    # Check if already a participant
                    existing_participant = self.db.execute(
                        select(MeetingParticipant).where(
                            and_(
                                MeetingParticipant.meeting_id == meeting_id,
                                MeetingParticipant.user_id == user.id
                            )
                        )
                    ).scalar_one_or_none()
                    
                    if not existing_participant:
                        participant = MeetingParticipant(
                            meeting_id=meeting_id,
                            user_id=user.id,
                            role=ParticipantRole.ATTENDEE,
                            response_status=ResponseStatus.PENDING
                        )
                        self.db.add(participant)
                        logger.info(f"Added participant {email} to meeting {meeting_id}")
                else:
                    logger.warning(f"User not found for email: {email} - skipping participant addition")
                    
        except Exception as e:
            logger.error(f"Failed to add participants by email: {e}")
    
    async def record_reminder_sent(self, meeting_id: int, user_id: int, reminder_type: str = 'email') -> None:
        """Record that a reminder was sent to a user"""
        try:
            reminder = MeetingReminder(
                meeting_id=meeting_id,
                user_id=user_id,
                reminder_type=reminder_type,
                status='sent'
            )
            self.db.add(reminder)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to record reminder: {e}")
            self.db.rollback()
