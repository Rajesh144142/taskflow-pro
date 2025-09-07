from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    username: str
    email: str


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None


class UserLogin(BaseModel):
    username: str  # This can be either username or email
    password: str


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
