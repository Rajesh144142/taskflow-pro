from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:password@localhost:5432/task_dashboard"
    
    # JWT
    secret_key: str = "your-super-secret-key-change-this-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    version: str = "1.0.0"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 465  # Use SSL port instead of STARTTLS
    smtp_username: str = "your-email@gmail.com"
    smtp_password: str = "your-app-password"
    smtp_from_email: str = "your-email@gmail.com"
    smtp_from_name: str = "Task Management Dashboard"
    smtp_use_tls: bool = True
    
    # Server Monitoring
    admin_email: str = "admin@yourcompany.com"
    server_monitoring_enabled: bool = True
    
    class Config:
        env_file = ".env"


settings = Settings()
