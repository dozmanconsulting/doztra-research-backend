"""
SQLAlchemy models for conversation sessions and messages.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class ConversationSession(Base):
    __tablename__ = "conversation_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Session metadata
    title = Column(String(500), nullable=False)
    zep_session_id = Column(String(255), nullable=True)  # Zep AI session ID
    
    # Session statistics
    message_count = Column(Integer, default=0)
    total_tokens_used = Column(Integer, default=0)
    
    # Session settings and metadata
    metadata = Column(JSON, default={})
    settings = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="conversation_sessions")
    feedback = relationship("MessageFeedback", back_populates="session", cascade="all, delete-orphan")
    analytics = relationship("ConversationAnalytics", back_populates="session", uselist=False)


class MessageFeedback(Base):
    __tablename__ = "message_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Message identification
    message_id = Column(String(255), nullable=False)  # Zep message ID
    message_role = Column(String(20), nullable=False)  # user, assistant, system
    
    # Feedback data
    rating = Column(Integer, nullable=False)  # 1-5 scale
    feedback_text = Column(Text, nullable=True)
    feedback_type = Column(String(50), nullable=True)  # helpful, accurate, relevant, etc.
    
    # Feedback metadata
    metadata = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    session = relationship("ConversationSession", back_populates="feedback")
    user = relationship("User")


class ConversationAnalytics(Base):
    __tablename__ = "conversation_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    
    # Message statistics
    total_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)
    assistant_messages = Column(Integer, default=0)
    
    # Performance metrics
    average_response_time = Column(Float, default=0.0)
    total_processing_time = Column(Float, default=0.0)
    
    # Content analysis
    topics_discussed = Column(JSON, default=[])
    sentiment_scores = Column(JSON, default={})
    complexity_score = Column(Float, nullable=True)
    
    # Engagement metrics
    engagement_score = Column(Float, default=0.0)
    session_duration_minutes = Column(Float, default=0.0)
    
    # Quality metrics
    average_rating = Column(Float, nullable=True)
    feedback_count = Column(Integer, default=0)
    
    # Analytics metadata
    analytics_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    session = relationship("ConversationSession", back_populates="analytics")


class ConversationExport(Base):
    __tablename__ = "conversation_exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("conversation_sessions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Export details
    export_format = Column(String(20), nullable=False)  # json, markdown, pdf, html
    file_path = Column(Text, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    
    # Export settings
    include_sources = Column(Boolean, default=True)
    include_metadata = Column(Boolean, default=False)
    export_settings = Column(JSON, default={})
    
    # Export status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    session = relationship("ConversationSession")
    user = relationship("User")
