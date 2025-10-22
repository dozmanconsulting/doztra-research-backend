from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.token_usage import RequestType


class TokenUsageBase(BaseModel):
    request_type: RequestType
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    request_id: Optional[str] = None
    conversation_id: Optional[str] = None


class TokenUsageCreate(TokenUsageBase):
    user_id: str


class TokenUsageInDBBase(TokenUsageBase):
    id: str
    user_id: str
    date: datetime

    class Config:
        from_attributes = True


class TokenUsage(TokenUsageInDBBase):
    pass


class TokenUsageSummaryBase(BaseModel):
    year: int
    month: int
    day: int
    chat_prompt_tokens: int
    chat_completion_tokens: int
    chat_total_tokens: int
    plagiarism_tokens: int
    prompt_generation_tokens: int
    total_tokens: int


class TokenUsageSummaryCreate(TokenUsageSummaryBase):
    user_id: str


class TokenUsageSummaryInDBBase(TokenUsageSummaryBase):
    id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenUsageSummary(TokenUsageSummaryInDBBase):
    pass


class TokenUsageRecord(BaseModel):
    id: str
    date: datetime
    request_type: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    request_id: Optional[str] = None


class TokenUsageHistory(BaseModel):
    total_records: int
    total_pages: int
    current_page: int
    records_per_page: int
    history: List[TokenUsageRecord]


class DailyUsage(BaseModel):
    date: str
    total_tokens: int


class TokenUsageStatistics(BaseModel):
    current_period: Dict[str, Any]
    breakdown: Dict[str, Any]
    models: Dict[str, int]
    daily_usage: List[DailyUsage]


class TokenUsageTrack(BaseModel):
    request_type: RequestType
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int
    request_id: Optional[str] = None
    conversation_id: Optional[str] = None
