"""
Database model for storing generated research content.
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base_class import Base


class GeneratedContent(Base):
    """Model for storing generated research content."""
    __tablename__ = "generated_content"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("research_projects.id", ondelete="CASCADE"), nullable=False)
    section_title = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    content_metadata = Column(JSON, nullable=True)  # Store additional metadata about the generation
    
    # Relationships
    project = relationship("ResearchProject", foreign_keys=[project_id], back_populates="generated_content")
    feedback = relationship("ContentFeedback", back_populates="content", cascade="all, delete-orphan", lazy="dynamic")

    class Config:
        """Pydantic config."""
        from_attributes = True  # Updated from orm_mode for Pydantic v2 compatibility
