import os
from typing import List
from dotenv import load_dotenv

# Load .env file (equivalent to require('dotenv').config() in Node.js)
load_dotenv()

class Settings:
    """
    Node.js style environment variable configuration
    Equivalent to: const config = { smtp_username: process.env.SMTP_USERNAME || 'default' }
    """
    
    # Database - Node.js style: process.env.DATABASE_URL || 'default'
    database_url: str = os.environ.get('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/task_dashboard')
    
    # JWT - Node.js style: process.env.SECRET_KEY || 'default'
    secret_key: str = os.environ.get('SECRET_KEY', 'your-super-secret-key-change-this-in-production')
    algorithm: str = os.environ.get('ALGORITHM', 'HS256')
    access_token_expire_minutes: int = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    
    # Application - Node.js style: process.env.PORT || 8000
    version: str = os.environ.get('VERSION', '1.0.0')
    debug: bool = os.environ.get('DEBUG', 'true').lower() == 'true'
    host: str = os.environ.get('HOST', '0.0.0.0')
    port: int = int(os.environ.get('PORT', '8080'))
    
    # CORS - Node.js style: process.env.ALLOWED_ORIGINS || 'default'
    allowed_origins: List[str] = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:3000,http://localhost:8000').split(',')
    
    # Email Configuration - Node.js style: process.env.SMTP_USERNAME || 'default'
    smtp_server: str = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port: int = int(os.environ.get('SMTP_PORT', '465'))
    smtp_username: str = os.environ.get('SMTP_USERNAME', 'your-email@gmail.com')
    smtp_password: str = os.environ.get('SMTP_PASSWORD', 'your-app-password')
    smtp_from_email: str = os.environ.get('SMTP_FROM_EMAIL', 'your-email@gmail.com')
    smtp_from_name: str = os.environ.get('SMTP_FROM_NAME', 'Task Management Dashboard')
    smtp_use_tls: bool = os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true'
    
    # Server Monitoring - Node.js style: process.env.ADMIN_EMAIL || 'default'
    admin_email: str = os.environ.get('ADMIN_EMAIL', 'admin@yourcompany.com')
    server_monitoring_enabled: bool = os.environ.get('SERVER_MONITORING_ENABLED', 'true').lower() == 'true'


# Create settings instance (equivalent to module.exports = config in Node.js)
settings = Settings()
