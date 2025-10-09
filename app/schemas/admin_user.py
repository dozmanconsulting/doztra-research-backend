from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from app.models.user import UserRole, SubscriptionPlan


class UserStatusUpdate(BaseModel):
    """Schema for updating user status."""
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    role: Optional[str] = None


class AdminUserCreate(BaseModel):
    """Schema for creating a user by admin."""
    email: EmailStr
    name: str
    password: str = Field(..., min_length=8)
    role: str = UserRole.USER
    is_active: bool = True
    is_verified: bool = True
    subscription: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "name": "John Doe",
                "password": "StrongPassword123!",
                "role": "user",
                "is_active": True,
                "is_verified": True,
                "subscription": {
                    "plan": "basic",
                    "payment_method_id": "pm_1234567890"
                }
            }
        }
