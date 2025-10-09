import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, Boolean, ForeignKey, JSON, Enum
from sqlalchemy.orm import relationship
import enum

from app.db.base_class import Base


class ProjectStatus(str, enum.Enum):
    active = "active"
    archived = "archived"
    completed = "completed"


class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    type = Column(String, nullable=False)
    status = Column(Enum(ProjectStatus), default=ProjectStatus.active, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    project_metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="research_projects")
    # Use string-based reference to avoid circular imports
    generated_content = relationship("GeneratedContent", back_populates="project", cascade="all, delete-orphan", lazy="dynamic")
