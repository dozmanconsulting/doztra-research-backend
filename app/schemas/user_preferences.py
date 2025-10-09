from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class UserPreferencesBase(BaseModel):
    theme: Optional[str] = "light"
    notifications: Optional[bool] = True
    default_model: Optional[str] = "gpt-4"


class UserPreferencesCreate(UserPreferencesBase):
    user_id: str


class UserPreferencesUpdate(UserPreferencesBase):
    pass


class UserPreferencesInDBBase(UserPreferencesBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPreferences(UserPreferencesInDBBase):
    pass
