from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base_class import Base
import uuid


class UsageStatistics(Base):
    __tablename__ = "usage_statistics"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    chat_messages = Column(Integer, default=0)
    plagiarism_checks = Column(Integer, default=0)
    prompts_generated = Column(Integer, default=0)
    tokens_used = Column(Integer, default=0)
    tokens_limit = Column(Integer, nullable=True)
    last_reset_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="usage_statistics")
