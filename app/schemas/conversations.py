"""
Pydantic schemas for Conversation Management API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

from app.schemas.knowledge_base import SearchResult


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    sources: Optional[List[SearchResult]] = None
    metadata: Dict[str, Any] = {}


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class CreateSessionResponse(BaseModel):
    session_id: str
    title: str
    created_at: datetime
    message: str


class SendMessageRequest(BaseModel):
    message: str
    metadata: Optional[Dict[str, Any]] = None
    content_filters: Optional[Dict[str, Any]] = None


class SendMessageResponse(BaseModel):
    message_id: str
    content: str
    sources: Optional[List[SearchResult]] = None
    timestamp: datetime
    metadata: Dict[str, Any] = {}


class ConversationSession(BaseModel):
    id: str
    session_id: str
    title: str
    messages: List[ConversationMessage]
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any] = {}


class SessionListResponse(BaseModel):
    sessions: List[ConversationSession]
    total_count: int
    skip: int
    limit: int


class ConversationSummary(BaseModel):
    session_id: str
    title: str
    summary: str
    key_topics: List[str]
    message_count: int
    duration_minutes: float
    created_at: datetime
    last_activity: datetime


class MessageFeedback(BaseModel):
    message_id: str
    rating: int = Field(ge=1, le=5)
    feedback: Optional[str] = None
    timestamp: datetime


class ConversationAnalytics(BaseModel):
    session_id: str
    total_messages: int
    user_messages: int
    assistant_messages: int
    average_response_time: float
    topics_discussed: List[str]
    sentiment_analysis: Dict[str, float]
    engagement_score: float
    feedback_summary: Dict[str, Any]


class ExportFormat(str, Enum):
    JSON = "json"
    MARKDOWN = "markdown"
    PDF = "pdf"
    HTML = "html"


class ExportRequest(BaseModel):
    format: ExportFormat = ExportFormat.JSON
    include_sources: bool = True
    include_metadata: bool = False
