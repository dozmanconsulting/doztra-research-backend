"""
Schemas for generated content API.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


class GeneratedContentBase(BaseModel):
    """Base schema for generated content."""
    section_title: str
    content: str
    content_metadata: Optional[Dict[str, Any]] = None


class GeneratedContentCreate(GeneratedContentBase):
    """Schema for creating generated content."""
    project_id: str


class GeneratedContentUpdate(BaseModel):
    """Schema for updating generated content."""
    content: Optional[str] = None
    content_metadata: Optional[Dict[str, Any]] = None
    version: Optional[int] = None


class GeneratedContentInDB(GeneratedContentBase):
    """Schema for generated content in DB."""
    id: str
    project_id: str
    version: int
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic config."""
        from_attributes = True  # Updated from orm_mode for Pydantic v2 compatibility


class GeneratedContentResponse(GeneratedContentInDB):
    """Schema for generated content response."""
    pass


class GeneratedContentList(BaseModel):
    """Schema for list of generated content."""
    items: List[GeneratedContentResponse]
    total: int
    skip: int
    limit: int
