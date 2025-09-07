from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.utils.security import get_password_hash, verify_password, create_access_token
from datetime import timedelta
from app.config import settings


class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        # Check if user already exists
        existing_user = self.db.execute(
            select(User).where(User.email == user_data.email)
        ).scalar_one_or_none()
        
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    async def authenticate_user(self, email: str, password: str) -> User | None:
        """Authenticate user with email and password"""
        user = self.db.execute(
            select(User).where(User.email == email)
        ).scalar_one_or_none()
        
        if not user or not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    async def create_access_token(self, user: User) -> str:
        """Create access token for user"""
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email},
            expires_delta=access_token_expires
        )
        return access_token