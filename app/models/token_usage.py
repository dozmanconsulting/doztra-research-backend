from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.db.base_class import Base
import uuid


class RequestType(str, enum.Enum):
    CHAT = "chat"
    PLAGIARISM = "plagiarism"
    PROMPT = "prompt"


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    request_type = Column(Enum(RequestType), nullable=False)
    model = Column(String, nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    request_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="token_usage")


class TokenUsageSummary(Base):
    __tablename__ = "token_usage_summary"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    day = Column(Integer, nullable=False)
    chat_prompt_tokens = Column(Integer, default=0, nullable=False)
    chat_completion_tokens = Column(Integer, default=0, nullable=False)
    chat_total_tokens = Column(Integer, default=0, nullable=False)
    plagiarism_tokens = Column(Integer, default=0, nullable=False)
    prompt_generation_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="token_usage_summary")
