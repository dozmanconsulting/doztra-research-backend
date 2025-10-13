from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.db.base_class import Base


class SupportChat(Base):
    __tablename__ = "support_chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    representative_id = Column(UUID(as_uuid=True), ForeignKey("representatives.id"), nullable=True)
    user_email = Column(String, nullable=True)
    user_name = Column(String, nullable=True)
    status = Column(String, default="waiting")  # waiting, connected, ended
    priority = Column(String, default="normal")  # normal, high, urgent
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    user_rating = Column(Integer, nullable=True)
    
    # Relationships
    messages = relationship("SupportMessage", back_populates="chat")
    representative = relationship("Representative", back_populates="chats")


class SupportMessage(Base):
    __tablename__ = "support_messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("support_chats.id"))
    sender_id = Column(UUID(as_uuid=True), nullable=True)
    sender_type = Column(String)  # user, representative, system
    sender_name = Column(String, nullable=True)
    message = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    is_read = Column(Boolean, default=False)
    
    # Relationships
    chat = relationship("SupportChat", back_populates="messages")


class Representative(Base):
    __tablename__ = "representatives"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    status = Column(String, default="offline")  # online, offline, busy, away
    max_concurrent_chats = Column(Integer, default=5)
    is_online = Column(Boolean, default=False)
    last_seen = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    chats = relationship("SupportChat", back_populates="representative")