from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate
from app.services.task_service import TaskService
from app.services.websocket_service import websocket_service
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
async def get_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tasks for current user"""
    task_service = TaskService(db)
    tasks = await task_service.get_user_tasks(str(current_user.id))
    return tasks


@router.post("/", response_model=TaskResponse)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new task"""
    task_service = TaskService(db)
    task = await task_service.create_task(str(current_user.id), task_data)
    
    # Notify via WebSocket
    await websocket_service.send_task_update(
        str(current_user.id), 
        task.__dict__, 
        "created"
    )
    
    return task


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific task by ID"""
    task_service = TaskService(db)
    task = await task_service.get_task_by_id(task_id, str(current_user.id))
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return task


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update task"""
    task_service = TaskService(db)
    task = await task_service.update_task(task_id, str(current_user.id), task_data)
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Notify via WebSocket
    await websocket_service.send_task_update(
        str(current_user.id), 
        task.__dict__, 
        "updated"
    )
    
    return task


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete task"""
    task_service = TaskService(db)
    success = await task_service.delete_task(task_id, str(current_user.id))
    
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Notify via WebSocket
    await websocket_service.send_task_update(
        str(current_user.id), 
        {"task_id": task_id}, 
        "deleted"
    )
    
    return {"message": "Task deleted successfully"}
