"""
Database model for storing user feedback on generated content.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class ContentFeedback(Base):
    """Model for storing user feedback on generated content."""
    __tablename__ = "content_feedback"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    content_id = Column(String, ForeignKey("generated_content.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5 star rating
    comments = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    feedback_metadata = Column(JSON, nullable=True)  # Additional feedback data
    
    # Relationships
    content = relationship("GeneratedContent", foreign_keys=[content_id], back_populates="feedback")
    user = relationship("User", foreign_keys=[user_id])

    class Config:
        """Pydantic config."""
        from_attributes = True  # Updated from orm_mode for Pydantic v2 compatibility
