from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from app.models.support import SupportChat, SupportMessage, Representative
from app.schemas.support import SupportChatRequest, SupportMessageRequest
from typing import Optional, List
import uuid
from datetime import datetime, timedelta


class SupportService:
    
    @staticmethod
    def create_support_chat(db: Session, request: SupportChatRequest) -> SupportChat:
        """Create a new support chat session"""
        chat = SupportChat(
            user_email=request.user_email,
            user_name=request.user_name,
            priority=request.priority,
            status="waiting"
        )
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        # Add initial system message if provided
        if request.initial_message:
            initial_msg = SupportMessage(
                chat_id=chat.id,
                sender_type="user",
                sender_name=request.user_name,
                message=request.initial_message
            )
            db.add(initial_msg)
            db.commit()
        
        return chat
    
    @staticmethod
    def get_available_representative(db: Session) -> Optional[Representative]:
        """Find an available representative"""
        return db.query(Representative).filter(
            and_(
                Representative.is_online == True,
                Representative.status == "online"
            )
        ).first()
    
    @staticmethod
    def get_queue_position(db: Session, chat_id: str) -> int:
        """Get position in queue for a chat"""
        chat = db.query(SupportChat).filter(SupportChat.id == chat_id).first()
        if not chat:
            return 0
            
        # Count chats created before this one that are still waiting
        position = db.query(SupportChat).filter(
            and_(
                SupportChat.status == "waiting",
                SupportChat.created_at < chat.created_at
            )
        ).count()
        
        return position + 1
    
    @staticmethod
    def estimate_wait_time(db: Session) -> int:
        """Estimate wait time in minutes"""
        queue_length = db.query(SupportChat).filter(
            SupportChat.status == "waiting"
        ).count()
        
        online_reps = db.query(Representative).filter(
            Representative.is_online == True
        ).count()
        
        if online_reps == 0:
            return 60  # Default 1 hour if no reps online
        
        # Estimate 5 minutes per person in queue per representative
        return max(1, (queue_length * 5) // online_reps)
    
    @staticmethod
    def send_message(db: Session, chat_id: str, request: SupportMessageRequest) -> SupportMessage:
        """Send a message in a support chat"""
        message = SupportMessage(
            chat_id=chat_id,
            sender_type=request.sender_type,
            message=request.message
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        return message
    
    @staticmethod
    def get_chat_messages(db: Session, chat_id: str) -> List[SupportMessage]:
        """Get all messages for a chat"""
        return db.query(SupportMessage).filter(
            SupportMessage.chat_id == chat_id
        ).order_by(SupportMessage.timestamp.asc()).all()