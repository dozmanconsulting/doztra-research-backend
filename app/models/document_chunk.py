"""
Document chunk model for storing document chunks and embeddings.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from uuid import uuid4

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"chunk-{uuid4()}")
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(JSONB, nullable=True)  # Store embedding as JSONB array
    metadata = Column(JSONB, nullable=True)  # Match DB column name: metadata (not chunk_metadata)
    created_at = Column(DateTime, default=func.now(), nullable=False)  # Match DB schema
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
