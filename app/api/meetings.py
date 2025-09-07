from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.api.auth import get_current_user
from app.models.user import User
from app.schemas.meeting import (
    MeetingCreate, MeetingUpdate, MeetingResponse, MeetingListResponse,
    MeetingReminderRequest
)
from app.services.meeting_service import MeetingService
from app.services.email_service import email_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/meetings", tags=["meetings"])


@router.post("/create", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new meeting with email reminders.
    
    - **title**: Meeting title (required)
    - **description**: Meeting description (optional)
    - **meeting_date**: Meeting date and time (required, must be in future)
    - **duration_minutes**: Meeting duration in minutes (default: 60)
    - **location**: Meeting location (optional)
    - **meeting_url**: Virtual meeting URL (optional)
    - **reminder_minutes**: Minutes before meeting to send reminder (default: 15)
    - **meeting_type**: Type of meeting (in_person, virtual, hybrid)
    - **participant_emails**: List of participant email addresses (optional)
    """
    try:
        meeting_service = MeetingService(db)
        
        meeting_data = meeting.dict()
        participant_emails = meeting_data.pop('participant_emails', None)
        
        created_meeting = await meeting_service.create_meeting(
            meeting_data=meeting_data,
            created_by=current_user.id,
            participant_emails=participant_emails
        )
        
        if not created_meeting:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create meeting"
            )
        
        # Get the full meeting with participants
        full_meeting = await meeting_service.get_meeting(created_meeting.id, current_user.id)
        
        if full_meeting:
            return full_meeting
        else:
            # If we can't retrieve the full meeting, return the created meeting
            return created_meeting
        
    except Exception as e:
        logger.error(f"Error creating meeting: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create meeting: {str(e)}"
        )


@router.get("/debug-test")
async def debug_meetings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Debug endpoint to test meeting service"""
    try:
        meeting_service = MeetingService(db)
        
        # Test basic database connection
        from app.models.meeting import Meeting
        from sqlalchemy import select
        
        # Try to query meetings table
        meetings_count = db.execute(select(Meeting)).fetchall()
        
        # Check if user is organizer of any meetings
        user_meetings = db.execute(select(Meeting).where(Meeting.created_by == current_user.id)).fetchall()
        
        return {
            "user_id": current_user.id,
            "user_email": current_user.email,
            "total_meetings": len(meetings_count),
            "user_organized_meetings": len(user_meetings),
            "status": "debug_success"
        }
        
    except Exception as e:
        logger.error(f"Debug error: {e}")
        return {
            "error": str(e),
            "status": "debug_failed"
        }


@router.get("/simple-list")
async def get_meetings_simple(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Simple endpoint to test meeting retrieval without complex schema"""
    try:
        logger.info(f"Getting meetings for user {current_user.id}")
        meeting_service = MeetingService(db)
        
        result = await meeting_service.get_user_meetings(
            user_id=current_user.id,
            page=1,
            size=10
        )
        
        # Return simple data structure
        return {
            "success": True,
            "total": result['total'],
            "meetings_count": len(result['meetings']),
            "user_id": current_user.id,
            "meetings": [
                {
                    "id": meeting.id,
                    "title": meeting.title,
                    "meeting_date": meeting.meeting_date.isoformat(),
                    "status": meeting.status
                }
                for meeting in result['meetings']
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting meetings: {e}")
        return {
            "success": False,
            "error": str(e),
            "user_id": current_user.id
        }


@router.get("/list", response_model=MeetingListResponse)
async def get_meetings(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    status: Optional[str] = Query(None, description="Filter by meeting status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's meetings with pagination and optional status filtering.
    
    - **page**: Page number (default: 1)
    - **size**: Number of meetings per page (default: 10, max: 100)
    - **status**: Filter by meeting status (scheduled, in_progress, completed, cancelled)
    """
    try:
        logger.info(f"Getting meetings for user {current_user.id} (email: {current_user.email})")
        meeting_service = MeetingService(db)
        
        result = await meeting_service.get_user_meetings(
            user_id=current_user.id,
            page=page,
            size=size,
            status=status
        )
        
        logger.info(f"Found {result['total']} meetings for user {current_user.id}")
        
        return MeetingListResponse(**result)
        
    except Exception as e:
        logger.error(f"Error getting meetings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get meetings: {str(e)}"
        )


@router.get("/{meeting_id}", response_model=MeetingResponse)
async def get_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific meeting by ID.
    User must be a participant or organizer of the meeting.
    """
    try:
        meeting_service = MeetingService(db)
        
        meeting = await meeting_service.get_meeting(meeting_id, current_user.id)
        
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found or access denied"
            )
        
        return meeting
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get meeting: {str(e)}"
        )


@router.put("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: int,
    meeting_update: MeetingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a meeting. Only the meeting organizer can update the meeting.
    Updates will be synced to Google Calendar if the meeting is connected.
    """
    try:
        meeting_service = MeetingService(db)
        
        # Filter out None values
        update_data = {k: v for k, v in meeting_update.dict().items() if v is not None}
        
        updated_meeting = await meeting_service.update_meeting(
            meeting_id=meeting_id,
            user_id=current_user.id,
            update_data=update_data
        )
        
        if not updated_meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found or you don't have permission to update it"
            )
        
        return updated_meeting
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update meeting: {str(e)}"
        )


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a meeting. Only the meeting organizer can delete the meeting.
    The meeting will also be removed from Google Calendar if connected.
    """
    try:
        meeting_service = MeetingService(db)
        
        success = await meeting_service.delete_meeting(meeting_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found or you don't have permission to delete it"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting meeting {meeting_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete meeting: {str(e)}"
        )


@router.get("/upcoming/", response_model=List[MeetingResponse])
async def get_upcoming_meetings(
    hours_ahead: int = Query(24, ge=1, le=168, description="Hours ahead to look for meetings"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get upcoming meetings for the current user within the specified time range.
    
    - **hours_ahead**: Number of hours ahead to look for meetings (default: 24, max: 168)
    """
    try:
        meeting_service = MeetingService(db)
        
        meetings = await meeting_service.get_upcoming_meetings(
            user_id=current_user.id,
            hours_ahead=hours_ahead
        )
        
        return meetings
        
    except Exception as e:
        logger.error(f"Error getting upcoming meetings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get upcoming meetings: {str(e)}"
        )


@router.post("/{meeting_id}/reminder", status_code=status.HTTP_200_OK)
async def send_meeting_reminder(
    meeting_id: int,
    reminder_request: MeetingReminderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a custom reminder for a meeting.
    Only the meeting organizer can send reminders.
    """
    try:
        meeting_service = MeetingService(db)
        
        # Verify user has access to the meeting
        meeting = await meeting_service.get_meeting(meeting_id, current_user.id)
        if not meeting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Meeting not found or access denied"
            )
        
        # Get all participants
        participants = db.execute(
            f"""
            SELECT u.username, u.email, mp.role, mp.response_status
            FROM meeting_participants mp
            JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = {meeting_id}
            """
        ).fetchall()
        
        # Send reminder emails
        emails_sent = 0
        for participant in participants:
            try:
                success = await email_service.send_meeting_reminder(
                    user_email=participant.email,
                    user_name=participant.username,
                    meeting_title=meeting.title,
                    meeting_date=meeting.meeting_date,
                    meeting_location=meeting.location,
                    meeting_url=meeting.meeting_url,
                    reminder_minutes=reminder_request.reminder_minutes
                )
                
                if success:
                    emails_sent += 1
                    # Record reminder sent
                    await meeting_service.record_reminder_sent(
                        meeting_id=meeting_id,
                        user_id=participant.user_id,
                        reminder_type='email'
                    )
                    
            except Exception as e:
                logger.error(f"Failed to send reminder to {participant.email}: {e}")
        
        return {
            "message": f"Meeting reminders sent to {emails_sent} participants",
            "total_participants": len(participants),
            "emails_sent": emails_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending meeting reminder: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send meeting reminder: {str(e)}"
        )


