from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.support import *
from app.services.support_service import SupportService
from app.models.support import Representative, SupportChat
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/support/request", response_model=SupportChatResponse)
async def request_support(
    request: SupportChatRequest,
    db: Session = Depends(get_db)
):
    """Request human support - create a new chat session"""
    try:
        # Create new support chat
        chat = SupportService.create_support_chat(db, request)
        
        # Check for available representatives
        available_rep = SupportService.get_available_representative(db)
        
        if available_rep:
            # Assign to representative immediately
            chat.representative_id = available_rep.id
            chat.status = "connected"
            db.commit()
            
            return SupportChatResponse(
                chat_id=str(chat.id),
                status=SupportChatStatus.CONNECTED,
                message=f"Connected to {available_rep.name}. How can I help you today?",
                representative_name=available_rep.name
            )
        else:
            # Add to queue
            queue_position = SupportService.get_queue_position(db, str(chat.id))
            wait_time = SupportService.estimate_wait_time(db)
            
            return SupportChatResponse(
                chat_id=str(chat.id),
                status=SupportChatStatus.WAITING,
                estimated_wait_time=wait_time,
                message="All representatives are currently busy. You've been added to the queue.",
                queue_position=queue_position
            )
            
    except Exception as e:
        logger.error(f"Error creating support chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create support chat"
        )


@router.post("/support/chat/{chat_id}/message", response_model=SupportMessageResponse)
async def send_support_message(
    chat_id: str,
    request: SupportMessageRequest,
    db: Session = Depends(get_db)
):
    """Send a message in a support chat"""
    try:
        message = SupportService.send_message(db, chat_id, request)
        
        return SupportMessageResponse(
            message_id=str(message.id),
            chat_id=str(message.chat_id),
            message=message.message,
            sender_type=message.sender_type,
            sender_name=message.sender_name,
            timestamp=message.timestamp,
            delivered=True
        )
        
    except Exception as e:
        logger.error(f"Error sending support message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.get("/support/status", response_model=SupportStatusResponse)
async def get_support_status(db: Session = Depends(get_db)):
    """Get current support system status"""
    try:
        online_reps = db.query(Representative).filter(
            Representative.is_online == True
        ).count()
        
        total_reps = db.query(Representative).count()
        
        queue_length = db.query(SupportChat).filter(
            SupportChat.status == "waiting"
        ).count()
        
        wait_time = SupportService.estimate_wait_time(db)
        
        return SupportStatusResponse(
            representatives_online=online_reps,
            total_representatives=total_reps,
            current_queue_length=queue_length,
            average_wait_time=wait_time,
            is_available=online_reps > 0
        )
        
    except Exception as e:
        logger.error(f"Error getting support status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get support status"
        )


@router.get("/support/chat/{chat_id}/messages")
async def get_chat_messages(
    chat_id: str,
    db: Session = Depends(get_db)
):
    """Get all messages for a support chat"""
    try:
        messages = SupportService.get_chat_messages(db, chat_id)
        
        return [
            SupportMessageResponse(
                message_id=str(msg.id),
                chat_id=str(msg.chat_id),
                message=msg.message,
                sender_type=msg.sender_type,
                sender_name=msg.sender_name,
                timestamp=msg.timestamp,
                delivered=True
            )
            for msg in messages
        ]
        
    except Exception as e:
        logger.error(f"Error getting chat messages: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get messages"
        )