"""
Document chunk model for storing document chunks and embeddings.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from uuid import uuid4

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"chunk-{uuid4()}")
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    embedding = Column(JSON, nullable=True)  # Store embedding as JSON array
    metadata = Column(JSON, nullable=True)  # For page numbers, sections, etc.
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
