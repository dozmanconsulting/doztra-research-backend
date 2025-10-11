"""
Document model for storing document metadata and status.
"""
from sqlalchemy import Column, String, DateTime, Integer, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from uuid import uuid4

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True, default=lambda: f"doc-{uuid4()}")
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=True)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path to file in storage
    file_type = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)
    upload_date = Column(DateTime, default=func.now(), nullable=False)
    processing_status = Column(String, default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    metadata = Column(JSON, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="documents")
