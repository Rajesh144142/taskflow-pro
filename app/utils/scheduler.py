from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from app.services.task_service import TaskService
from app.services.email_service import email_service
from app.services.meeting_service import MeetingService
from app.database import SessionLocal
from app.config import settings
from sqlalchemy import text
import logging
import asyncio
from typing import List

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = AsyncIOScheduler()


async def cleanup_old_tasks():
    """Cron job: Clean up old completed tasks (runs daily at 2 AM)"""
    try:
        db = SessionLocal()
        task_service = TaskService(db)
        deleted_count = await task_service.cleanup_old_tasks()
        logger.info(f"Cleaned up {deleted_count} old completed tasks")
    except Exception as e:
        logger.error(f"Error in cleanup_old_tasks: {e}")
    finally:
        db.close()


async def update_statistics():
    """Cron job: Update user statistics (runs hourly)"""
    try:
        db = SessionLocal()
        task_service = TaskService(db)
        await task_service.update_user_statistics()
        logger.info("Updated user statistics")
    except Exception as e:
        logger.error(f"Error in update_statistics: {e}")
    finally:
        db.close()


async def health_check():
    """Cron job: System health check (runs every 5 minutes)"""
    try:
        db = SessionLocal()
        # Simple health check - just verify database connection
        db.execute(text("SELECT 1"))
        logger.info("Health check passed")
    except Exception as e:
        logger.error(f"Health check failed: {e}")
    finally:
        db.close()


async def send_daily_summaries():
    """Cron job: Send daily task summaries to all users (runs daily at 9 AM)"""
    try:
        db = SessionLocal()
        task_service = TaskService(db)
        
        # Get all active users
        users = db.execute(text("SELECT id, username, email FROM users WHERE is_active = true")).fetchall()
        
        for user in users:
            try:
                # Get user's task summary
                tasks_summary = await task_service.get_user_task_summary(str(user.id))
                
                # Send email summary
                await email_service.send_daily_summary(
                    user_email=user.email,
                    user_name=user.username,
                    tasks_summary=tasks_summary
                )
                logger.info(f"Daily summary sent to {user.email}")
                
            except Exception as e:
                logger.error(f"Failed to send summary to {user.email}: {e}")
        
        logger.info(f"Daily summaries sent to {len(users)} users")
        
    except Exception as e:
        logger.error(f"Error in send_daily_summaries: {e}")
    finally:
        db.close()


async def send_task_reminders():
    """Cron job: Send reminders for overdue tasks (runs every 2 hours)"""
    try:
        db = SessionLocal()
        task_service = TaskService(db)
        
        # Get overdue tasks
        overdue_tasks = await task_service.get_overdue_tasks()
        
        for task in overdue_tasks:
            try:
                # Get user info
                user = db.execute(
                    text("SELECT username, email FROM users WHERE id = :user_id"),
                    {"user_id": task.user_id}
                ).fetchone()
                
                if user:
                    await email_service.send_task_notification(
                        user_email=user.email,
                        user_name=user.username,
                        task_title=task.title,
                        task_status=task.status.value,
                        task_priority=task.priority.value,
                        notification_type="reminder"
                    )
                    logger.info(f"Reminder sent for task '{task.title}' to {user.email}")
                    
            except Exception as e:
                logger.error(f"Failed to send reminder for task {task.id}: {e}")
        
        logger.info(f"Task reminders sent for {len(overdue_tasks)} tasks")
        
    except Exception as e:
        logger.error(f"Error in send_task_reminders: {e}")
    finally:
        db.close()


async def send_12_hour_task_reminders():
    """Cron job: Send 12-hour task reminders for pending/in-progress tasks (runs every 12 hours)"""
    try:
        db = SessionLocal()
        task_service = TaskService(db)
        
        # Get users in batches to handle large user bases
        batch_size = 100  # Process 100 users at a time
        offset = 0
        total_emails_sent = 0
        
        while True:
            # Get users in batches
            users_batch = db.execute(
                text("""
                    SELECT id, username, email 
                    FROM users 
                    WHERE is_active = true 
                    ORDER BY id 
                    LIMIT :limit OFFSET :offset
                """),
                {"limit": batch_size, "offset": offset}
            ).fetchall()
            
            if not users_batch:
                break  # No more users
            
            # Process batch of users
            batch_emails_sent = await process_user_batch(db, task_service, users_batch)
            total_emails_sent += batch_emails_sent
            
            offset += batch_size
            
            # Small delay between batches to prevent overwhelming the system
            await asyncio.sleep(1)
        
        logger.info(f"12-hour task reminders sent to {total_emails_sent} users (processed in batches)")
        
    except Exception as e:
        logger.error(f"Error in send_12_hour_task_reminders: {e}")
    finally:
        db.close()


async def process_user_batch(db: SessionLocal, task_service: TaskService, users_batch: List) -> int:
    """Process a batch of users for task reminders"""
    emails_sent = 0
    
    # Get pending tasks for this batch of users
    user_ids = [str(user.id) for user in users_batch]
    
    # Query tasks for this batch only
    tasks_query = text("""
        SELECT u.id as user_id, u.username, u.email,
               t.id as task_id, t.title, t.description, t.status, t.priority, t.created_at
        FROM users u
        LEFT JOIN tasks t ON u.id = t.user_id
        WHERE u.id = ANY(:user_ids) 
        AND (t.status IN ('pending', 'in_progress') OR t.status IS NULL)
        ORDER BY u.id, t.created_at DESC
    """)
    
    result = db.execute(tasks_query, {"user_ids": user_ids}).fetchall()
    
    # Group tasks by user
    user_tasks = {}
    for row in result:
        user_id = str(row.user_id)
        
        if user_id not in user_tasks:
            user_tasks[user_id] = {
                'user_info': {
                    'id': row.user_id,
                    'username': row.username,
                    'email': row.email
                },
                'tasks': []
            }
        
        if row.task_id is not None:
            task_dict = {
                'id': row.task_id,
                'title': row.title,
                'description': row.description or 'No description',
                'status': row.status,
                'priority': row.priority,
                'created_at': row.created_at.strftime('%Y-%m-%d %H:%M') if row.created_at else 'Unknown'
            }
            user_tasks[user_id]['tasks'].append(task_dict)
    
    # Send emails for this batch
    for user_id, user_data in user_tasks.items():
        try:
            user_info = user_data['user_info']
            pending_tasks = user_data['tasks']
            
            if pending_tasks:
                # Send email with timeout to prevent hanging
                success = await asyncio.wait_for(
                    email_service.send_task_reminder(
                        user_email=user_info['email'],
                        user_name=user_info['username'],
                        pending_tasks=pending_tasks
                    ),
                    timeout=30  # 30 second timeout per email
                )
                
                if success:
                    emails_sent += 1
                    logger.info(f"12-hour reminder sent to {user_info['email']} for {len(pending_tasks)} tasks")
                else:
                    logger.warning(f"Failed to send reminder to {user_info['email']}")
            else:
                logger.info(f"No pending tasks for {user_info['email']}, skipping reminder")
                
        except asyncio.TimeoutError:
            logger.error(f"Timeout sending reminder to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to send 12-hour reminder to user {user_id}: {e}")
    
    return emails_sent


async def monitor_server_health():
    """Cron job: Monitor server health and send alerts if down (runs every 5 minutes)"""
    try:
        import requests
        import socket
        
        # Check if server is responding
        error_message = "Server not responding"
        try:
            response = requests.get("http://localhost:8000/health", timeout=10)
            if response.status_code == 200:
                logger.info("Server health check passed")
                return
        except Exception as e:
            logger.error(f"Server health check failed: {e}")
            error_message = str(e)
        
        # If we reach here, server is down
        server_info = {
            'server': socket.gethostname(),
            'port': 8000,
            'environment': 'production' if not settings.debug else 'development'
        }
        
        await email_service.send_server_down_notification(
            error_message=error_message,
            server_info=server_info
        )
        
        logger.error("Server down notification sent to admin")
        
    except Exception as e:
        logger.error(f"Error in monitor_server_health: {e}")


async def send_meeting_reminders():
    """Cron job: Send meeting reminders based on user-defined reminder times (runs every minute)"""
    try:
        db = SessionLocal()
        meeting_service = MeetingService(db)
        
        # Get meetings that need reminders (check every minute for accuracy)
        meetings_needing_reminders = await meeting_service.get_meetings_needing_reminders()
        
        total_reminders_sent = 0
        
        for meeting_data in meetings_needing_reminders:
            meeting = meeting_data['meeting']
            participants = meeting_data['participants']
            
            try:
                # Send reminders to all participants
                for participant in participants:
                    try:
                        success = await email_service.send_meeting_reminder(
                            user_email=participant.email,
                            user_name=participant.username,
                            meeting_title=meeting.title,
                            meeting_date=meeting.meeting_date,
                            meeting_location=meeting.location,
                            meeting_url=meeting.meeting_url,
                            reminder_minutes=meeting.reminder_minutes
                        )
                        
                        if success:
                            total_reminders_sent += 1
                            # Record reminder sent
                            await meeting_service.record_reminder_sent(
                                meeting_id=meeting.id,
                                user_id=participant.user_id,
                                reminder_type='email'
                            )
                            logger.info(f"Meeting reminder sent to {participant.email} for meeting '{meeting.title}'")
                        else:
                            logger.warning(f"Failed to send meeting reminder to {participant.email}")
                            
                    except Exception as e:
                        logger.error(f"Error sending meeting reminder to {participant.email}: {e}")
                        
            except Exception as e:
                logger.error(f"Error processing meeting {meeting.id}: {e}")
        
        logger.info(f"Meeting reminders sent: {total_reminders_sent} reminders processed")
        
    except Exception as e:
        logger.error(f"Error in send_meeting_reminders: {e}")
    finally:
        db.close()


def setup_scheduler():
    """Setup and start the scheduler with cron jobs"""
    # Add cron jobs
    scheduler.add_job(
        cleanup_old_tasks,
        CronTrigger(hour=2, minute=0),  # Daily at 2 AM
        id="cleanup_old_tasks",
        name="Clean up old completed tasks"
    )
    
    scheduler.add_job(
        update_statistics,
        CronTrigger(minute=0),  # Every hour
        id="update_statistics",
        name="Update user statistics"
    )
    
    scheduler.add_job(
        health_check,
        CronTrigger(minute="*/5"),  # Every 5 minutes
        id="health_check",
        name="System health check"
    )
    
    scheduler.add_job(
        send_daily_summaries,
        CronTrigger(hour=9, minute=0),  # Daily at 9 AM
        id="send_daily_summaries",
        name="Send daily task summaries"
    )
    
    scheduler.add_job(
        send_task_reminders,
        CronTrigger(hour="*/2"),  # Every 2 hours
        id="send_task_reminders",
        name="Send task reminders"
    )
    
    scheduler.add_job(
        send_12_hour_task_reminders,
        CronTrigger(hour="*/12"),  # Every 12 hours (6 AM & 6 PM)
        id="send_12_hour_task_reminders",
        name="Send 12-hour task reminders"
    )
    
    scheduler.add_job(
        monitor_server_health,
        CronTrigger(minute="*/5"),  # Every 5 minutes
        id="monitor_server_health",
        name="Monitor server health"
    )
    scheduler.add_job(
        send_meeting_reminders,
        CronTrigger(minute="*"),  # Every minute for accurate timing
        id="send_meeting_reminders",
        name="Send meeting reminders"
    )
    
    # Start scheduler
    scheduler.start()
    logger.info("Scheduler started with cron jobs")


def shutdown_scheduler():
    """Shutdown the scheduler"""
    scheduler.shutdown()
    logger.info("Scheduler shutdown")
