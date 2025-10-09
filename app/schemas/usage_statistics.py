from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class UsageStatisticsBase(BaseModel):
    chat_messages: int = 0
    plagiarism_checks: int = 0
    prompts_generated: int = 0
    tokens_used: int = 0
    tokens_limit: Optional[int] = None


class UsageStatisticsCreate(UsageStatisticsBase):
    user_id: str


class UsageStatisticsUpdate(BaseModel):
    chat_messages: Optional[int] = None
    plagiarism_checks: Optional[int] = None
    prompts_generated: Optional[int] = None
    tokens_used: Optional[int] = None
    tokens_limit: Optional[int] = None


class UsageStatisticsInDBBase(UsageStatisticsBase):
    id: str
    user_id: str
    last_reset_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UsageStatistics(UsageStatisticsInDBBase):
    pass


class UsageResponse(BaseModel):
    chat_messages: Dict[str, Any]
    plagiarism_checks: Dict[str, Any]
    prompts_generated: Dict[str, Any]
    tokens: Dict[str, Any]
