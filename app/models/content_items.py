"""
SQLAlchemy models for content items in the knowledge base.
"""

from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Float, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base_class import Base


class ContentItem(Base):
    __tablename__ = "content_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Content metadata
    title = Column(String(500), nullable=False)
    content_type = Column(String(50), nullable=False)  # text, file, audio, video, url, youtube
    file_path = Column(Text, nullable=True)
    source_url = Column(Text, nullable=True)
    
    # Processing status
    processing_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    processing_progress = Column(Float, default=0.0)
    error_message = Column(Text, nullable=True)
    
    # Content analysis
    word_count = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)  # For audio/video content
    file_size_bytes = Column(Integer, nullable=True)
    language = Column(String(10), default="en")
    
    # Metadata and settings  
    content_metadata = Column("metadata", JSON, default={})  # Map to existing 'metadata' column
    extraction_settings = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="content_items")
    chunks = relationship("ContentChunk", back_populates="content_item", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="content_item")


class ContentChunk(Base):
    __tablename__ = "content_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chunk_id = Column(String(255), unique=True, nullable=False, index=True)
    content_item_id = Column(UUID(as_uuid=True), ForeignKey("content_items.id"), nullable=False)
    
    # Chunk content
    text = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    start_char = Column(Integer, nullable=True)
    end_char = Column(Integer, nullable=True)
    
    # Vector embedding (stored as JSON array)
    embedding = Column(JSON, nullable=True)
    embedding_model = Column(String(100), nullable=True)
    
    # Chunk metadata
    chunk_metadata = Column("metadata", JSON, default={})  # Map to existing 'metadata' column
    word_count = Column(Integer, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="chunks")


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(String(255), unique=True, nullable=False, index=True)
    content_item_id = Column(UUID(as_uuid=True), ForeignKey("content_items.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Job details
    job_type = Column(String(50), nullable=False)  # transcription, embedding, extraction, etc.
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    progress = Column(Float, default=0.0)
    
    # Job configuration
    parameters = Column(JSON, default={})
    
    # Results and errors
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    content_item = relationship("ContentItem", back_populates="processing_jobs")
    user = relationship("User")


class VectorIndex(Base):
    __tablename__ = "vector_indexes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Index metadata
    index_name = Column(String(255), nullable=False)
    collection_name = Column(String(255), nullable=False)  # Milvus collection name
    dimension = Column(Integer, nullable=False)
    metric_type = Column(String(50), default="COSINE")
    
    # Index statistics
    total_vectors = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    # Configuration
    index_params = Column(JSON, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User")
