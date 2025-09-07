from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserUpdate
from app.utils.security import get_password_hash
from typing import Optional


class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> Optional[User]:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return None
        
        # Update fields if provided
        if user_data.username is not None:
            user.username = user_data.username
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user account"""
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        self.db.delete(user)
        self.db.commit()
        return True
