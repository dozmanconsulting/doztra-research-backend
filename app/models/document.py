"""
Document model for storing document metadata and status.
"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from uuid import uuid4

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"doc-{uuid4()}")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # Match DB: UUID type
    title = Column(String, nullable=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path to file in storage
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=func.now(), nullable=False)
    processing_status = Column(String, default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    document_metadata = Column(JSONB, nullable=True)  # Match DB: JSONB type
    created_at = Column(DateTime, default=func.now(), nullable=False)  # Match DB schema
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)  # Match DB schema
    
    # Relationships
    user = relationship("User", back_populates="documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
