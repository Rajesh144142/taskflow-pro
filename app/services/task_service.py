from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from app.models.task import Task, TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta


class TaskService:
    def __init__(self, db: Session):
        self.db = db
    
    async def create_task(self, user_id: str, task_data: TaskCreate) -> Task:
        """Create a new task for user"""
        task = Task(
            user_id=int(user_id),
            title=task_data.title,
            description=task_data.description,
            status=task_data.status,
            priority=task_data.priority
        )
        
        self.db.add(task)
        self.db.commit()
        self.db.refresh(task)
        return task
    
    async def get_user_tasks(self, user_id: str) -> List[Task]:
        """Get all tasks for a user"""
        tasks = self.db.execute(
            select(Task).where(Task.user_id == int(user_id)).order_by(Task.created_at.desc())
        ).scalars().all()
        return list(tasks)
    
    async def get_task_by_id(self, task_id: str, user_id: str) -> Optional[Task]:
        """Get specific task by ID for user"""
        return self.db.execute(
            select(Task).where(Task.id == int(task_id), Task.user_id == int(user_id))
        ).scalar_one_or_none()
    
    async def update_task(self, task_id: str, user_id: str, task_data: TaskUpdate) -> Optional[Task]:
        """Update task"""
        task = await self.get_task_by_id(task_id, user_id)
        if not task:
            return None
        
        # Update fields if provided
        if task_data.title is not None:
            task.title = task_data.title
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.status is not None:
            task.status = task_data.status
        if task_data.priority is not None:
            task.priority = task_data.priority
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    async def delete_task(self, task_id: str, user_id: str) -> bool:
        """Delete task"""
        task = await self.get_task_by_id(task_id, user_id)
        if not task:
            return False
        
        self.db.delete(task)
        self.db.commit()
        return True
    
    async def get_user_task_summary(self, user_id: str) -> Dict[str, int]:
        """Get task summary statistics for a user"""
        from sqlalchemy import func
        
        # Get task counts by status
        result = self.db.execute(
            select(Task.status, func.count(Task.id))
            .where(Task.user_id == int(user_id))
            .group_by(Task.status)
        ).fetchall()
        
        summary = {"total": 0, "pending": 0, "in_progress": 0, "completed": 0}
        
        for status, count in result:
            summary[status.value] = count
            summary["total"] += count
        
        return summary
    
    async def get_overdue_tasks(self) -> List[Task]:
        """Get tasks that are overdue (pending for more than 24 hours)"""
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Tasks that are pending and created more than 24 hours ago
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        overdue_tasks = self.db.execute(
            select(Task)
            .where(
                Task.status == TaskStatus.PENDING,
                Task.created_at < cutoff_time
            )
        ).scalars().all()
        
        return list(overdue_tasks)
    
    async def get_pending_tasks_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get pending and in-progress tasks for a specific user.
        Returns only tasks that need attention (not completed).
        
        Args:
            user_id: User ID
            
        Returns:
            List of task dictionaries with relevant information
        """
        tasks = self.db.execute(
            select(Task)
            .where(
                Task.user_id == int(user_id),
                Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
            )
            .order_by(Task.created_at.desc())
        ).scalars().all()
        
        # Convert to dictionary format for email
        task_list = []
        for task in tasks:
            task_dict = {
                'id': task.id,
                'title': task.title,
                'description': task.description or 'No description',
                'status': task.status.value,
                'priority': task.priority.value,
                'created_at': task.created_at.strftime('%Y-%m-%d %H:%M'),
                'updated_at': task.updated_at.strftime('%Y-%m-%d %H:%M') if task.updated_at else None
            }
            task_list.append(task_dict)
        
        return task_list
    
    async def get_all_pending_tasks(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all pending and in-progress tasks for all users.
        Returns a dictionary with user_id as key and their tasks as value.
        
        Returns:
            Dictionary mapping user_id to list of pending tasks
        """
        from sqlalchemy import text
        
        # Get all users with their pending tasks
        query = text("""
            SELECT u.id as user_id, u.username, u.email,
                   t.id as task_id, t.title, t.description, t.status, t.priority, t.created_at
            FROM users u
            LEFT JOIN tasks t ON u.id = t.user_id
            WHERE t.status IN ('pending', 'in_progress') OR t.status IS NULL
            ORDER BY u.id, t.created_at DESC
        """)
        
        result = self.db.execute(query).fetchall()
        
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
            
            # Only add task if it exists (not NULL)
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
        
        return user_tasks
    
    async def cleanup_old_tasks(self) -> int:
        """Clean up old completed tasks (older than 30 days)"""
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        result = self.db.execute(
            delete(Task).where(
                Task.status == TaskStatus.COMPLETED,
                Task.created_at < cutoff_date
            )
        )
        self.db.commit()
        return result.rowcount
    
    async def update_user_statistics(self):
        """Update user statistics (placeholder for future implementation)"""
        # This could update user statistics like total tasks, completion rate, etc.
        pass