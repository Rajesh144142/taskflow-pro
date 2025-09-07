from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.services.user_service import UserService
from app.api.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_user_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile"""
    user_service = UserService(db)
    updated_user = await user_service.update_user(str(current_user.id), user_data)
    
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return updated_user


@router.delete("/me")
async def delete_user_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current user account"""
    user_service = UserService(db)
    success = await user_service.delete_user(str(current_user.id))
    
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User account deleted successfully"}
