"""
Extended user schemas with OAuth support.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserOAuthBase(BaseModel):
    """Base schema for user OAuth data."""
    oauth_provider: Optional[str] = Field(None, description="OAuth provider (e.g., 'google')")
    oauth_user_id: Optional[str] = Field(None, description="User ID from the OAuth provider")


class UserOAuthCreate(UserOAuthBase):
    """Schema for creating a user with OAuth data."""
    email: EmailStr
    name: str
    oauth_access_token: str
    oauth_refresh_token: Optional[str] = None


class UserOAuthUpdate(UserOAuthBase):
    """Schema for updating a user's OAuth data."""
    oauth_access_token: Optional[str] = None
    oauth_refresh_token: Optional[str] = None
    oauth_token_expires_at: Optional[datetime] = None


class UserOAuthRead(UserOAuthBase):
    """Schema for reading a user's OAuth data."""
    oauth_provider: Optional[str] = None
    
    class Config:
        orm_mode = True
