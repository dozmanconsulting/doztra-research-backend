from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime


class JobApplicationCreate(BaseModel):
    name: str
    email: EmailStr
    role: str
    linkedin: Optional[str] = None
    portfolio: Optional[str] = None
    cover_letter: Optional[str] = None


class JobApplicationResponse(BaseModel):
    id: str
    success: bool = True
    message: str = "Application received"
    created_at: datetime

    class Config:
        from_attributes = True
