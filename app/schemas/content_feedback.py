"""
Schemas for content feedback API.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class ContentFeedbackBase(BaseModel):
    """Base schema for content feedback."""
    rating: int = Field(..., ge=1, le=5, description="Rating from 1-5 stars")
    comments: Optional[str] = None
    feedback_metadata: Optional[Dict[str, Any]] = None


class ContentFeedbackCreate(ContentFeedbackBase):
    """Schema for creating content feedback."""
    content_id: str


class ContentFeedbackUpdate(BaseModel):
    """Schema for updating content feedback."""
    rating: Optional[int] = Field(None, ge=1, le=5, description="Rating from 1-5 stars")
    comments: Optional[str] = None
    feedback_metadata: Optional[Dict[str, Any]] = None


class ContentFeedbackInDB(ContentFeedbackBase):
    """Schema for content feedback in DB."""
    id: str
    content_id: str
    user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        orm_mode = True


class ContentFeedbackResponse(ContentFeedbackInDB):
    """Schema for content feedback response."""
    pass


class ContentFeedbackList(BaseModel):
    """Schema for list of content feedback."""
    items: List[ContentFeedbackResponse]
    total: int
    skip: int
    limit: int
