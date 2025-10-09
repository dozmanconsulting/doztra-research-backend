from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
from app.models.user import SubscriptionPlan, SubscriptionStatus, UserRole, ModelTier
from app.schemas.user_preferences import UserPreferences
from app.schemas.usage_statistics import UsageStatistics


class SubscriptionBase(BaseModel):
    plan: SubscriptionPlan
    status: SubscriptionStatus
    expires_at: Optional[datetime] = None
    is_active: bool = True
    auto_renew: bool = False
    token_limit: Optional[int] = None
    max_model_tier: str = ModelTier.GPT_3_5_TURBO


class SubscriptionCreate(SubscriptionBase):
    user_id: str
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    payment_method_id: Optional[str] = None


class SubscriptionUpdate(BaseModel):
    plan: Optional[SubscriptionPlan] = None
    status: Optional[SubscriptionStatus] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = None
    auto_renew: Optional[bool] = None
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    token_limit: Optional[int] = None
    max_model_tier: Optional[str] = None


class SubscriptionInDBBase(SubscriptionBase):
    id: str
    user_id: str
    start_date: datetime
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    payment_method_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Subscription(SubscriptionInDBBase):
    pass


class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.USER


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    subscription: Optional[Dict[str, Any]] = None
    
    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    password: Optional[str] = None


class UserInDBBase(UserBase):
    id: str
    role: UserRole
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserInDB(UserInDBBase):
    hashed_password: str
    subscription: Optional[Subscription] = None
    preferences: Optional[UserPreferences] = None
    usage: Optional[UsageStatistics] = None


class User(UserInDBBase):
    """User schema without password."""
    subscription: Optional[Subscription] = None
    preferences: Optional[UserPreferences] = None
    usage: Optional[UsageStatistics] = None
    
    model_config = {
        "from_attributes": True,
        "json_encoders": {
            uuid.UUID: str
        }
    }
    
    @validator("id", "subscription.id", "subscription.user_id", pre=True)
    def convert_uuid_to_str(cls, v):
        if isinstance(v, uuid.UUID):
            return str(v)
        return v


class UserWithToken(UserBase):
    """User schema with token information."""
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str
    success: bool = True
