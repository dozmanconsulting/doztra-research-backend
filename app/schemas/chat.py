from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from enum import Enum


class MessageRole(str, Enum):
    """Enum for message roles in a conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageBase(BaseModel):
    """Base schema for message data."""
    content: str
    role: MessageRole = MessageRole.USER


class MessageCreate(MessageBase):
    """Schema for creating a new message."""
    message_metadata: Optional[Dict[str, Any]] = None


class MessageResponse(MessageBase):
    """Schema for message response."""
    id: str
    conversation_id: str
    created_at: datetime
    model: Optional[str] = None
    message_metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """Base schema for conversation data."""
    title: Optional[str] = None


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""
    initial_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""
    title: Optional[str] = None
    is_active: Optional[bool] = None


class ConversationResponse(ConversationBase):
    """Schema for conversation response."""
    id: str
    created_at: datetime
    updated_at: datetime
    is_active: bool
    message_count: Optional[int] = None
    last_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class ConversationDetailResponse(ConversationResponse):
    """Schema for detailed conversation response including messages."""
    messages: List[MessageResponse] = []
    total_messages: int = 0
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """Schema for chat message request."""
    message: str
    conversation_id: Optional[str] = None
    model: Optional[str] = "gpt-3.5-turbo"
    temperature: Optional[float] = Field(0.7, ge=0.0, le=1.0)
    max_tokens: Optional[int] = Field(1000, gt=0, le=4000)
    attachments: Optional[List[str]] = []


class ChatResponse(BaseModel):
    """Schema for chat message response."""
    conversation_id: str
    message_id: str
    content: str
    usage: Dict[str, int]
    created_at: Optional[datetime] = None
    

class TokenUsage(BaseModel):
    """Schema for token usage information."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
