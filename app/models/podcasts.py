"""
SQLAlchemy models for podcast generation and management.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class Podcast(Base):
    __tablename__ = "podcasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    podcast_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Podcast metadata
    title = Column(String(500), nullable=False)
    topic = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    
    # Generation parameters
    knowledge_query = Column(Text, nullable=True)
    content_ids = Column(JSON, default=[])  # List of content IDs used
    
    # Podcast status
    status = Column(String(50), default="pending")  # pending, generating_script, generating_audio, completed, failed
    progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # Generated content
    script_content = Column(Text, nullable=True)
    audio_file_path = Column(Text, nullable=True)
    
    # Audio properties
    duration_seconds = Column(Float, nullable=True)
    file_size_bytes = Column(Integer, nullable=True)
    audio_format = Column(String(20), default="mp3")
    
    # Generation settings
    voice_settings = Column(JSON, default={})
    podcast_settings = Column(JSON, default={})
    
    # Metadata
    podcast_metadata = Column("metadata", JSON, default={})  # Map to existing 'metadata' column
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    script_generated_at = Column(DateTime, nullable=True)
    audio_generated_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="podcasts")
    script_segments = relationship("PodcastScriptSegment", back_populates="podcast", cascade="all, delete-orphan")
    shares = relationship("PodcastShare", back_populates="podcast", cascade="all, delete-orphan")
    analytics = relationship("PodcastAnalytics", back_populates="podcast", uselist=False)


class PodcastScriptSegment(Base):
    __tablename__ = "podcast_script_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    podcast_id = Column(UUID(as_uuid=True), ForeignKey("podcasts.id"), nullable=False)
    
    # Segment identification
    segment_id = Column(String(255), nullable=False)
    segment_index = Column(Integer, nullable=False)
    
    # Segment content
    speaker = Column(String(100), nullable=False)  # host, guest, narrator
    text = Column(Text, nullable=False)
    
    # Timing information
    start_time = Column(Float, nullable=True)
    end_time = Column(Float, nullable=True)
    duration = Column(Float, nullable=True)
    
    # Voice settings for this segment
    voice_settings = Column(JSON, default={})
    
    # Segment metadata
    segment_metadata = Column("metadata", JSON, default={})  # Map to existing 'metadata' column
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    podcast = relationship("Podcast", back_populates="script_segments")


class PodcastShare(Base):
    __tablename__ = "podcast_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    podcast_id = Column(UUID(as_uuid=True), ForeignKey("podcasts.id"), nullable=False)
    
    # Share details
    share_token = Column(String(255), unique=True, nullable=False, index=True)
    public = Column(Boolean, default=True)
    
    # Access control
    password_protected = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=True)
    
    # Share statistics
    view_count = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    
    # Share settings
    allow_download = Column(Boolean, default=True)
    show_transcript = Column(Boolean, default=True)
    
    # Expiration
    expires_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_accessed = Column(DateTime, nullable=True)
    
    # Relationships
    podcast = relationship("Podcast", back_populates="shares")


class PodcastAnalytics(Base):
    __tablename__ = "podcast_analytics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    podcast_id = Column(UUID(as_uuid=True), ForeignKey("podcasts.id"), nullable=False)
    
    # Play statistics
    play_count = Column(Integer, default=0)
    unique_listeners = Column(Integer, default=0)
    download_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    
    # Engagement metrics
    average_listen_duration = Column(Float, default=0.0)
    completion_rate = Column(Float, default=0.0)
    skip_rate = Column(Float, default=0.0)
    
    # Listener feedback
    average_rating = Column(Float, nullable=True)
    rating_count = Column(Integer, default=0)
    
    # Geographic and device data
    geographic_data = Column(JSON, default={})
    device_data = Column(JSON, default={})
    referrer_data = Column(JSON, default={})
    
    # Time-based analytics
    hourly_plays = Column(JSON, default={})
    daily_plays = Column(JSON, default={})
    
    # Analytics metadata
    analytics_data = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    podcast = relationship("Podcast", back_populates="analytics")


class PodcastGeneration(Base):
    __tablename__ = "podcast_generations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    podcast_id = Column(UUID(as_uuid=True), ForeignKey("podcasts.id"), nullable=False)
    
    # Generation job details
    job_type = Column(String(50), nullable=False)  # script_generation, audio_synthesis, full_generation
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    
    # Generation parameters
    generation_params = Column(JSON, default={})
    
    # Results
    output_data = Column(JSON, nullable=True)
    error_details = Column(JSON, nullable=True)
    
    # Resource usage
    processing_time_seconds = Column(Float, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    podcast = relationship("Podcast")
