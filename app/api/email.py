"""
Email API Module

Professional email API endpoints for the Task Management Dashboard.
Provides email sending, template support, and notification services.

Author: Task Management Dashboard Team
Version: 1.0.0
"""

from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.database import get_db
from app.services.email_service import email_service, EmailAttachment
from app.api.auth import get_current_user
from app.models.user import User
from app.config import settings

router = APIRouter(prefix="/api/email", tags=["email"])


class EmailRequest(BaseModel):
    """Email request model with validation."""
    to: Union[str, List[str]] = Field(..., description="Recipient email(s)")
    subject: str = Field(..., min_length=1, max_length=200, description="Email subject")
    html_content: Optional[str] = Field(None, description="HTML email body")
    text_content: Optional[str] = Field(None, description="Plain text email body")
    cc: Optional[List[str]] = Field(None, description="CC recipients")
    bcc: Optional[List[str]] = Field(None, description="BCC recipients")
    reply_to: Optional[EmailStr] = Field(None, description="Reply-to email address")
    
    class Config:
        json_schema_extra = {
            "example": {
                "to": "user@example.com",
                "subject": "Test Email",
                "html_content": "<h1>Hello!</h1><p>This is a test email.</p>",
                "text_content": "Hello! This is a test email."
            }
        }


class TaskNotificationRequest(BaseModel):
    """Task notification request model."""
    task_title: str = Field(..., min_length=1, max_length=200, description="Task title")
    task_status: str = Field(..., description="Task status")
    task_priority: str = Field(..., description="Task priority")
    notification_type: str = Field(default="status_change", description="Notification type")
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_title": "Complete Project Documentation",
                "task_status": "completed",
                "task_priority": "high",
                "notification_type": "status_change"
            }
        }


class EmailResponse(BaseModel):
    """Standard email response model."""
    message: str
    success: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Email sent successfully",
                "success": True
            }
        }


@router.post("/send", response_model=EmailResponse)
async def send_custom_email(
    email_request: EmailRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a custom email with HTML/text content.
    
    This endpoint allows authenticated users to send custom emails
    with full control over content and recipients.
    """
    try:
        success = await email_service.send_email(
            to=email_request.to,
            subject=email_request.subject,
            html_content=email_request.html_content,
            text_content=email_request.text_content,
            cc=email_request.cc,
            bcc=email_request.bcc,
            reply_to=email_request.reply_to
        )
        
        if success:
            return EmailResponse(message="Email sent successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email service error: {str(e)}"
        )


@router.post("/notifications/task", response_model=EmailResponse)
async def send_task_notification(
    notification_request: TaskNotificationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a professional task notification email.
    
    Sends a beautifully formatted email notification when task status changes.
    """
    try:
        success = await email_service.send_task_notification(
            user_email=current_user.email,
            user_name=current_user.username,
            task_title=notification_request.task_title,
            task_status=notification_request.task_status,
            task_priority=notification_request.task_priority,
            notification_type=notification_request.notification_type
        )
        
        if success:
            return EmailResponse(message="Task notification sent successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send task notification"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Notification service error: {str(e)}"
        )


@router.post("/notifications/summary", response_model=EmailResponse)
async def send_daily_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a daily task summary email.
    
    Sends a comprehensive daily summary with task statistics and progress.
    """
    try:
        # Create sample task summary (in production, this would come from the database)
        sample_summary = {
            "total": 5,
            "completed": 2,
            "pending": 2,
            "in_progress": 1
        }
        
        success = await email_service.send_daily_summary(
            user_email=current_user.email,
            user_name=current_user.username,
            tasks_summary=sample_summary
        )
        
        if success:
            return EmailResponse(message="Daily summary sent successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send daily summary"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Summary service error: {str(e)}"
        )


@router.post("/templates/welcome", response_model=EmailResponse)
async def send_welcome_email(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a welcome email using HTML template.
    
    Sends a professional welcome email with dashboard information.
    """
    try:
        success = await email_service.send_template_email(
            to=current_user.email,
            subject="Welcome to Task Management Dashboard!",
            template_name="welcome",
            template_data={
                "user_name": current_user.username,
                "dashboard_url": "http://localhost:8000/frontend/index.html"
            }
        )
        
        if success:
            return EmailResponse(message="Welcome email sent successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send welcome email"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Welcome email service error: {str(e)}"
        )


@router.post("/test-reminder")
async def send_test_task_reminder(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a test 12-hour task reminder email.
    
    This endpoint simulates the 12-hour reminder system for testing.
    """
    try:
        from app.services.task_service import TaskService
        task_service = TaskService(db)
        
        # Get user's pending tasks
        pending_tasks = await task_service.get_pending_tasks_for_user(str(current_user.id))
        
        if not pending_tasks:
            return EmailResponse(message="No pending tasks found - reminder not sent")
        
        success = await email_service.send_task_reminder(
            user_email=current_user.email,
            user_name=current_user.username,
            pending_tasks=pending_tasks
        )
        
        if success:
            return EmailResponse(message=f"Test reminder sent successfully for {len(pending_tasks)} tasks")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test reminder"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test reminder service error: {str(e)}"
        )


@router.post("/test-server-alert")
async def send_test_server_alert(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a test server down notification email.
    
    This endpoint simulates the server monitoring system for testing.
    """
    try:
        import socket
        
        server_info = {
            'server': socket.gethostname(),
            'port': 8000,
            'environment': 'development'
        }
        
        success = await email_service.send_server_down_notification(
            error_message="Test server down alert - This is a test notification",
            server_info=server_info
        )
        
        if success:
            return EmailResponse(message="Test server alert sent successfully")
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test server alert"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test server alert service error: {str(e)}"
        )


@router.get("/health")
async def email_service_health():
    """
    Check email service health status.
    
    Returns the current status of the email service configuration.
    """
    try:
        is_configured = email_service.config.validate()
        return {
            "status": "healthy" if is_configured else "misconfigured",
            "smtp_server": email_service.config.smtp_server,
            "smtp_port": email_service.config.smtp_port,
            "from_email": email_service.config.from_email,
            "admin_email": settings.admin_email,
            "configured": is_configured
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "configured": False
        }