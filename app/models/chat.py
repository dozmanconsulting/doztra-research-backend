from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Enum, Boolean, Integer, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
import uuid

from app.db.base_class import Base


class MessageRole(str, enum.Enum):
    """Enum for message roles in a conversation."""
    user = "user"
    assistant = "assistant"
    system = "system"


class Conversation(Base):
    """Model for chat conversations."""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    # conversation_metadata = Column(JSON, nullable=True)  # Temporarily commented out until migration is applied
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete")
    
    # Virtual properties (not stored in DB)
    message_count = None
    last_message = None


class Message(Base):
    """Model for chat messages."""
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    conversation_id = Column(String, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # AI model information
    model = Column(String, nullable=True)
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Metadata for attachments or additional features
    message_metadata = Column(JSON, nullable=True)
