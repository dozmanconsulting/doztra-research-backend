from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any
import secrets
import os
from pathlib import Path
from datetime import timedelta


class Settings(BaseSettings):
    PROJECT_NAME: str = "Doztra Auth Service"
    API_V1_STR: str = "/api"
    
    # Environment
    ENVIRONMENT: str = "development"  # Options: development, production, test
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    ALGORITHM: str = "HS256"
    
    # Database
    DATABASE_URL: str = "sqlite:///./doztra_auth.db"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Frontend dev server
        "http://localhost:8000",  # Backend dev server
        "https://doztra.ai",      # Production frontend
        "https://doztra.netlify.app",  # Netlify deployment
        "https://www.doztra.netlify.app",  # Netlify with www subdomain
        "https://doztra-ai.netlify.app",  # New Netlify deployment
        "https://www.doztra-ai.netlify.app",  # New Netlify with www subdomain
    ]
    
    # Email settings
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = "noreply@doztra.ai"
    EMAILS_FROM_NAME: str = "Doztra AI"
    
    # Password reset
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS: int = 24
    
    # Email verification
    EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS: int = 48
    
    # AI Service
    OPENAI_API_KEY: str = ""
    OPENAI_API_URL: str = "https://api.openai.com/v1"
    DEFAULT_AI_MODEL: str = "gpt-3.5-turbo"
    MAX_TOKENS_PER_REQUEST: int = 4000

    # Google API
    GOOGLE_API_KEY: Optional[str] = None
    
    # Additional LLM Settings
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_BASE_URL: Optional[str] = None
    
    # LLM Model Settings
    LLM_REASONING: str = "gpt-4-turbo"  # Upgraded from gpt-3.5-turbo for higher quality academic content
    LLM_REFINEMENT: str = "gpt-3.5-turbo"
    LLM_CONVERSATION: str = "gpt-3.5-turbo"
    LLM_CREATIVE: str = "gpt-3.5-turbo"
    LLM_CODE: str = "gpt-3.5-turbo"
    LLM_REGULAR: str = "gpt-3.5-turbo"
    LLM_DEFAULT_EXECUTION: str = "gpt-3.5-turbo"
    
    # Document Processing Settings
    UPLOAD_DIR: str = "./uploads"
    DOCUMENT_CHUNKS_DIR: str = "./document_chunks"
    MAX_CONCURRENT_PROCESSING: int = 3
    DEFAULT_CHUNK_SIZE: int = 1000
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    
    # Storage Settings
    USE_S3_STORAGE: bool = False
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"
    AWS_BUCKET_NAME: Optional[str] = None
    
    # Google Cloud Storage Settings
    USE_GCS_STORAGE: bool = False
    GCS_BUCKET_NAME: Optional[str] = None
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    
    # Document Processing Optimization
    PARALLEL_EMBEDDING_GENERATION: bool = True
    MAX_PARALLEL_EMBEDDINGS: int = 5
    OPTIMIZE_CHUNK_SIZE: bool = True
    
    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
