"""
Email Service Module

A professional email service implementation similar to Nodemailer for Node.js.
Provides SMTP email sending, template support, and scheduled notifications.

Author: Task Management Dashboard Team
Version: 1.0.0
"""

import asyncio
import logging
from datetime import datetime
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email import encoders
from typing import List, Optional, Dict, Any, Union
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader, Template

from app.config import settings

logger = logging.getLogger(__name__)


class EmailConfig:
    """Email configuration class for better type safety and validation."""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.smtp_from_email
        self.from_name = settings.smtp_from_name
        self.use_tls = settings.smtp_use_tls
        
    def validate(self) -> bool:
        """Validate email configuration."""
        required_fields = [
            self.smtp_server, self.smtp_username, 
            self.smtp_password, self.from_email
        ]
        return all(field and field.strip() for field in required_fields)


class EmailTemplate:
    """Email template handler with Jinja2 support."""
    
    def __init__(self, template_dir: str = "app/templates"):
        self.template_dir = Path(template_dir)
        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            autoescape=True
        )
    
    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render email template with context data."""
        try:
            template = self.env.get_template(f"{template_name}.html")
            return template.render(**context)
        except Exception as e:
            logger.error(f"Failed to render template {template_name}: {e}")
            raise


class EmailAttachment:
    """Email attachment handler."""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "application/octet-stream"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
    
    def to_mime_base(self) -> MIMEBase:
        """Convert to MIMEBase attachment."""
        part = MIMEBase(*self.content_type.split('/'))
        part.set_payload(self.content)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="{self.filename}"'
        )
        return part


class EmailMessage:
    """Professional email message builder."""
    
    def __init__(self):
        self.msg = MIMEMultipart('alternative')
        self.attachments: List[EmailAttachment] = []
    
    def set_from(self, email: str, name: Optional[str] = None):
        """Set sender information."""
        sender = f"{name} <{email}>" if name else email
        self.msg['From'] = sender
        return self
    
    def set_to(self, recipients: Union[str, List[str]]):
        """Set recipient(s)."""
        if isinstance(recipients, str):
            recipients = [recipients]
        self.msg['To'] = ', '.join(recipients)
        return self
    
    def set_subject(self, subject: str):
        """Set email subject."""
        self.msg['Subject'] = subject
        return self
    
    def set_content(self, html_content: Optional[str] = None, text_content: Optional[str] = None):
        """Set email content."""
        if text_content:
            text_part = MIMEText(text_content, 'plain', 'utf-8')
            self.msg.attach(text_part)
        
        if html_content:
            html_part = MIMEText(html_content, 'html', 'utf-8')
            self.msg.attach(html_part)
        
        return self
    
    def add_attachment(self, attachment: EmailAttachment):
        """Add attachment to email."""
        self.attachments.append(attachment)
        return self
    
    def add_headers(self, headers: Dict[str, str]):
        """Add custom headers."""
        for key, value in headers.items():
            self.msg[key] = value
        return self
    
    def build(self) -> MIMEMultipart:
        """Build the final email message."""
        for attachment in self.attachments:
            self.msg.attach(attachment.to_mime_base())
        return self.msg


class EmailService:
    """
    Professional email service implementation.
    
    Features:
    - SMTP email sending with SSL/TLS support
    - HTML and text content support
    - Template rendering with Jinja2
    - Attachment support
    - Professional error handling
    - Async/await support
    """
    
    def __init__(self):
        self.config = EmailConfig()
        self.template_handler = EmailTemplate()
        
        if not self.config.validate():
            logger.warning("Email configuration is incomplete")
    
    async def send_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        html_content: Optional[str] = None,
        text_content: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[EmailAttachment]] = None,
        reply_to: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send email with professional error handling.
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            html_content: HTML email body
            text_content: Plain text email body
            cc: CC recipients
            bcc: BCC recipients
            attachments: List of EmailAttachment objects
            reply_to: Reply-to email address
            headers: Custom headers
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Build email message
            message = EmailMessage()
            message.set_from(self.config.from_email, self.config.from_name)
            message.set_to(to)
            message.set_subject(subject)
            message.set_content(html_content, text_content)
            
            # Add optional fields
            if cc:
                message.msg['Cc'] = ', '.join(cc)
            if reply_to:
                message.msg['Reply-To'] = reply_to
            if headers:
                message.add_headers(headers)
            
            # Add attachments
            if attachments:
                for attachment in attachments:
                    message.add_attachment(attachment)
            
            # Send email
            await self._send_smtp_email(message.build(), to, cc, bcc)
            
            logger.info(f"Email sent successfully to {to}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to}: {e}")
            return False
    
    async def send_template_email(
        self,
        to: Union[str, List[str]],
        subject: str,
        template_name: str,
        template_data: Dict[str, Any],
        **kwargs
    ) -> bool:
        """
        Send email using Jinja2 template.
        
        Args:
            to: Recipient email(s)
            subject: Email subject
            template_name: Template name (without .html extension)
            template_data: Data to pass to template
            **kwargs: Additional arguments for send_email
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            html_content = self.template_handler.render_template(template_name, template_data)
            return await self.send_email(
                to=to,
                subject=subject,
                html_content=html_content,
                **kwargs
            )
        except Exception as e:
            logger.error(f"Failed to send template email {template_name}: {e}")
            return False
    
    async def send_task_notification(
        self,
        user_email: str,
        user_name: str,
        task_title: str,
        task_status: str,
        task_priority: str,
        notification_type: str = "status_change"
    ) -> bool:
        """
        Send professional task notification email.
        
        Args:
            user_email: User's email address
            user_name: User's name
            task_title: Task title
            task_status: Task status
            task_priority: Task priority
            notification_type: Type of notification
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"Task Update: {task_title}"
        
        # Create professional HTML content
        html_content = self._create_task_notification_html(
            user_name, task_title, task_status, task_priority
        )
        
        return await self.send_email(
            to=user_email,
            subject=subject,
            html_content=html_content
        )
    
    async def send_daily_summary(
        self,
        user_email: str,
        user_name: str,
        tasks_summary: Dict[str, Any]
    ) -> bool:
        """
        Send professional daily task summary email.
        
        Args:
            user_email: User's email address
            user_name: User's name
            tasks_summary: Dictionary with task statistics
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"Daily Task Summary - {datetime.now().strftime('%Y-%m-%d')}"
        
        html_content = self._create_daily_summary_html(user_name, tasks_summary)
        
        return await self.send_email(
            to=user_email,
            subject=subject,
            html_content=html_content
        )
    
    async def send_task_reminder(
        self,
        user_email: str,
        user_name: str,
        pending_tasks: List[Dict[str, Any]]
    ) -> bool:
        """
        Send task reminder email for pending/in-progress tasks.
        
        Args:
            user_email: User's email address
            user_name: User's name
            pending_tasks: List of pending/in-progress tasks
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        if not pending_tasks:
            logger.info(f"No pending tasks for {user_email}, skipping reminder")
            return True
        
        subject = f"Task Reminder: {len(pending_tasks)} pending task(s)"
        
        html_content = self._create_task_reminder_html(user_name, pending_tasks)
        
        return await self.send_email(
            to=user_email,
            subject=subject,
            html_content=html_content
        )
    
    async def send_server_down_notification(
        self,
        error_message: str,
        server_info: Dict[str, Any]
    ) -> bool:
        """
        Send server down notification to admin.
        
        Args:
            error_message: Error message that caused the server to go down
            server_info: Server information
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        subject = f"🚨 Server Down Alert - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        html_content = self._create_server_down_html(error_message, server_info)
        
        return await self.send_email(
            to=settings.admin_email,
            subject=subject,
            html_content=html_content
        )
    
    async def _send_smtp_email(
        self, 
        msg: MIMEMultipart, 
        to: List[str], 
        cc: Optional[List[str]] = None, 
        bcc: Optional[List[str]] = None
    ):
        """Send email via SMTP with proper error handling."""
        # Combine all recipients
        recipients = [to] if isinstance(to, str) else to.copy()
        if cc:
            recipients.extend([cc] if isinstance(cc, str) else cc)
        if bcc:
            recipients.extend([bcc] if isinstance(bcc, str) else bcc)
        
        # Create SMTP connection
        smtp = aiosmtplib.SMTP(
            hostname=self.config.smtp_server,
            port=self.config.smtp_port,
            use_tls=self.config.use_tls
        )
        
        try:
            await smtp.connect()
            await smtp.login(self.config.smtp_username, self.config.smtp_password)
            await smtp.send_message(msg, recipients=recipients)
        finally:
            await smtp.quit()
    
    def _create_task_notification_html(
        self, 
        user_name: str, 
        task_title: str, 
        task_status: str, 
        task_priority: str
    ) -> str:
        """Create professional task notification HTML."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Task Notification</title>
            <style>
                {self._get_email_styles()}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header">
                    <h1>📋 Task Management Dashboard</h1>
                    <p>Task Update Notification</p>
                </div>
                
                <div class="email-content">
                    <h2>Hello {user_name}!</h2>
                    <p>Your task has been updated:</p>
                    
                    <div class="task-card">
                        <h3>{task_title}</h3>
                        <div class="task-meta">
                            <span class="status-badge status-{task_status.lower()}">{task_status.title()}</span>
                            <span class="priority-badge priority-{task_priority.lower()}">{task_priority.title()}</span>
                        </div>
                        <p class="timestamp">Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    </div>
                    
                    <p>You can view and manage your tasks by logging into the dashboard.</p>
                </div>
                
                <div class="email-footer">
                    <p>This is an automated message from Task Management Dashboard</p>
                    <p>© 2025 Task Management Dashboard. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_daily_summary_html(self, user_name: str, tasks_summary: Dict[str, Any]) -> str:
        """Create professional daily summary HTML."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Daily Summary</title>
            <style>
                {self._get_email_styles()}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header summary-header">
                    <h1>📊 Daily Task Summary</h1>
                    <p>{datetime.now().strftime('%B %d, %Y')}</p>
                </div>
                
                <div class="email-content">
                    <h2>Hello {user_name}!</h2>
                    <p>Here's your task summary for today:</p>
                    
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-number">{tasks_summary.get('total', 0)}</div>
                            <div class="stat-label">Total Tasks</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{tasks_summary.get('completed', 0)}</div>
                            <div class="stat-label">Completed</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{tasks_summary.get('pending', 0)}</div>
                            <div class="stat-label">Pending</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-number">{tasks_summary.get('in_progress', 0)}</div>
                            <div class="stat-label">In Progress</div>
                        </div>
                    </div>
                    
                    <p class="motivation">Keep up the great work! 🚀</p>
                </div>
                
                <div class="email-footer">
                    <p>This is an automated message from Task Management Dashboard</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_task_reminder_html(self, user_name: str, pending_tasks: List[Dict[str, Any]]) -> str:
        """Create professional task reminder HTML."""
        tasks_html = ""
        for task in pending_tasks:
            tasks_html += f"""
            <div class="task-item">
                <h4>{task.get('title', 'Untitled Task')}</h4>
                <div class="task-meta">
                    <span class="status-badge status-{task.get('status', 'pending').lower()}">{task.get('status', 'pending').title()}</span>
                    <span class="priority-badge priority-{task.get('priority', 'medium').lower()}">{task.get('priority', 'medium').title()}</span>
                </div>
                <p class="task-description">{task.get('description', 'No description available')}</p>
                <p class="task-date">Created: {task.get('created_at', 'Unknown date')}</p>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Task Reminder</title>
            <style>
                {self._get_email_styles()}
                .task-item {{
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    padding: 15px;
                    margin: 10px 0;
                    border-radius: 5px;
                }}
                .task-item h4 {{
                    margin: 0 0 10px 0;
                    color: #856404;
                }}
                .task-description {{
                    color: #6c757d;
                    font-size: 14px;
                    margin: 10px 0;
                }}
                .task-date {{
                    color: #6c757d;
                    font-size: 12px;
                    margin: 5px 0 0 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header" style="background: linear-gradient(135deg, #ffc107 0%, #ff8c00 100%);">
                    <h1>⏰ Task Reminder</h1>
                    <p>You have {len(pending_tasks)} pending task(s)</p>
                </div>
                
                <div class="email-content">
                    <h2>Hello {user_name}!</h2>
                    <p>This is a friendly reminder that you have pending tasks that need your attention:</p>
                    
                    {tasks_html}
                    
                    <div class="motivation">
                        <p>💪 Keep up the great work! Complete these tasks to stay on track.</p>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>This is an automated reminder from Task Management Dashboard</p>
                    <p>© 2025 Task Management Dashboard. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_server_down_html(self, error_message: str, server_info: Dict[str, Any]) -> str:
        """Create server down notification HTML."""
        return f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Server Down Alert</title>
            <style>
                {self._get_email_styles()}
                .alert-container {{
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 8px;
                    padding: 20px;
                    margin: 20px 0;
                }}
                .error-details {{
                    background-color: #fff;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 15px 0;
                    font-family: monospace;
                    font-size: 12px;
                    color: #721c24;
                }}
                .server-info {{
                    background-color: #d1ecf1;
                    border-radius: 5px;
                    padding: 15px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="email-header" style="background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);">
                    <h1>🚨 Server Down Alert</h1>
                    <p>Task Management Dashboard Server</p>
                </div>
                
                <div class="email-content">
                    <div class="alert-container">
                        <h2>⚠️ Critical Alert</h2>
                        <p>The Task Management Dashboard server has encountered an error and may be down.</p>
                    </div>
                    
                    <h3>Error Details:</h3>
                    <div class="error-details">
                        {error_message}
                    </div>
                    
                    <h3>Server Information:</h3>
                    <div class="server-info">
                        <p><strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p><strong>Server:</strong> {server_info.get('server', 'Unknown')}</p>
                        <p><strong>Port:</strong> {server_info.get('port', 'Unknown')}</p>
                        <p><strong>Environment:</strong> {server_info.get('environment', 'Unknown')}</p>
                    </div>
                    
                    <div class="motivation">
                        <p>🔧 Please check the server logs and restart the service if necessary.</p>
                    </div>
                </div>
                
                <div class="email-footer">
                    <p>This is an automated alert from Task Management Dashboard Monitoring</p>
                    <p>© 2025 Task Management Dashboard. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _get_email_styles(self) -> str:
        """Get professional email CSS styles."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            margin: 0;
            padding: 0;
            background-color: #f5f5f5;
        }
        .email-container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .email-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .summary-header {
            background: linear-gradient(135deg, #2196F3 0%, #21CBF3 100%);
        }
        .email-header h1 {
            margin: 0 0 10px 0;
            font-size: 24px;
        }
        .email-header p {
            margin: 0;
            opacity: 0.9;
        }
        .email-content {
            padding: 30px;
        }
        .email-content h2 {
            color: #333;
            margin-top: 0;
        }
        .task-card {
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            border-left: 4px solid #667eea;
        }
        .task-card h3 {
            margin: 0 0 15px 0;
            color: #333;
        }
        .task-meta {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
        }
        .status-badge, .priority-badge {
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }
        .status-pending { background-color: #ff9800; color: white; }
        .status-in_progress { background-color: #2196F3; color: white; }
        .status-completed { background-color: #4CAF50; color: white; }
        .priority-low { background-color: #9E9E9E; color: white; }
        .priority-medium { background-color: #FF9800; color: white; }
        .priority-high { background-color: #F44336; color: white; }
        .timestamp {
            color: #666;
            font-size: 14px;
            margin: 0;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }
        .stat-card {
            text-align: center;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 8px;
        }
        .stat-number {
            font-size: 32px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        .stat-label {
            color: #666;
            font-size: 14px;
        }
        .motivation {
            text-align: center;
            font-size: 18px;
            color: #667eea;
            margin: 30px 0;
        }
        .email-footer {
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 12px;
        }
        """

    async def send_meeting_reminder(
        self,
        user_email: str,
        user_name: str,
        meeting_title: str,
        meeting_date: datetime,
        meeting_location: Optional[str] = None,
        meeting_url: Optional[str] = None,
        reminder_minutes: int = 15
    ) -> bool:
        """Send meeting reminder email to user."""
        try:
            html_content = self._create_meeting_reminder_html(
                user_name=user_name,
                meeting_title=meeting_title,
                meeting_date=meeting_date,
                meeting_location=meeting_location,
                meeting_url=meeting_url,
                reminder_minutes=reminder_minutes
            )
            
            success = await self.send_email(
                to=user_email,
                subject=f"📅 Meeting Reminder: {meeting_title}",
                html_content=html_content,
                text_content=f"Meeting Reminder\n\nHello {user_name},\n\nYou have a meeting '{meeting_title}' scheduled for {meeting_date.strftime('%Y-%m-%d %H:%M')}.\n\nLocation: {meeting_location or 'TBD'}\nMeeting URL: {meeting_url or 'N/A'}\n\nThis reminder is sent {reminder_minutes} minutes before the meeting.\n\nBest regards,\nTask Management Dashboard"
            )
            
            if success:
                logger.info(f"Meeting reminder sent to {user_email}")
            else:
                logger.error(f"Failed to send meeting reminder to {user_email}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending meeting reminder to {user_email}: {e}")
            return False

    def _create_meeting_reminder_html(
        self,
        user_name: str,
        meeting_title: str,
        meeting_date: datetime,
        meeting_location: Optional[str] = None,
        meeting_url: Optional[str] = None,
        reminder_minutes: int = 15
    ) -> str:
        """Create HTML content for meeting reminder email."""
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Meeting Reminder</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f4f4f4;
                }}
                .email-container {{
                    background-color: white;
                    border-radius: 10px;
                    padding: 30px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #667eea;
                }}
                .header h1 {{
                    color: #667eea;
                    margin: 0;
                    font-size: 28px;
                }}
                .meeting-card {{
                    background-color: #f8f9fa;
                    border-radius: 8px;
                    padding: 25px;
                    margin: 20px 0;
                    border-left: 4px solid #667eea;
                }}
                .meeting-title {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin: 0 0 15px 0;
                }}
                .meeting-details {{
                    margin: 15px 0;
                }}
                .detail-row {{
                    display: flex;
                    align-items: center;
                    margin: 10px 0;
                    padding: 8px 0;
                }}
                .detail-icon {{
                    width: 20px;
                    margin-right: 10px;
                    text-align: center;
                }}
                .detail-label {{
                    font-weight: 600;
                    color: #555;
                    min-width: 80px;
                }}
                .detail-value {{
                    color: #333;
                }}
                .reminder-badge {{
                    background-color: #ff9800;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 14px;
                    font-weight: 600;
                    display: inline-block;
                    margin: 15px 0;
                }}
                .cta-button {{
                    display: inline-block;
                    background-color: #667eea;
                    color: white;
                    padding: 12px 24px;
                    text-decoration: none;
                    border-radius: 6px;
                    font-weight: 600;
                    margin: 20px 0;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 1px solid #eee;
                    color: #666;
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>📅 Meeting Reminder</h1>
                </div>
                
                <p>Hello <strong>{user_name}</strong>,</p>
                
                <div class="meeting-card">
                    <div class="meeting-title">{meeting_title}</div>
                    
                    <div class="reminder-badge">
                        ⏰ Reminder: {reminder_minutes} minutes before meeting
                    </div>
                    
                    <div class="meeting-details">
                        <div class="detail-row">
                            <span class="detail-icon">📅</span>
                            <span class="detail-label">Date:</span>
                            <span class="detail-value">{meeting_date.strftime('%A, %B %d, %Y')}</span>
                        </div>
                        <div class="detail-row">
                            <span class="detail-icon">🕐</span>
                            <span class="detail-label">Time:</span>
                            <span class="detail-value">{meeting_date.strftime('%I:%M %p')}</span>
                        </div>
                        {f'<div class="detail-row"><span class="detail-icon">📍</span><span class="detail-label">Location:</span><span class="detail-value">{meeting_location}</span></div>' if meeting_location else ''}
                        {f'<div class="detail-row"><span class="detail-icon">🔗</span><span class="detail-label">Meeting URL:</span><span class="detail-value"><a href="{meeting_url}" style="color: #667eea;">Join Meeting</a></span></div>' if meeting_url else ''}
                    </div>
                </div>
                
                {f'<div style="text-align: center;"><a href="{meeting_url}" class="cta-button">Join Meeting</a></div>' if meeting_url else ''}
                
                <p>Please make sure you're prepared for the meeting. If you need to reschedule or have any questions, please contact the meeting organizer.</p>
                
                <div class="footer">
                    <p>This is an automated reminder from Task Management Dashboard</p>
                    <p>© 2024 Task Management Dashboard. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html_content


# Global email service instance
email_service = EmailService()