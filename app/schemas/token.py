from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class Token(BaseModel):
    success: bool = True
    access_token: str
    token_type: str = "bearer"
    refresh_token: Optional[str] = None


class TokenPayload(BaseModel):
    sub: str
    exp: datetime


class TokenData(BaseModel):
    user_id: str


class RefreshTokenCreate(BaseModel):
    user_id: str
    token: str
    expires_at: datetime


class RefreshTokenInDB(RefreshTokenCreate):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True
