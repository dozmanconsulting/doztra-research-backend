"""
Conversation Sessions API Routes
Simple CRUD endpoints for conversation sessions matching test expectations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.models.conversations import ConversationSession, MessageFeedback, ConversationAnalytics
from pydantic import BaseModel

router = APIRouter(prefix="/api/conversations", tags=["Conversation Sessions"])

# Pydantic models for requests/responses
class CreateSessionRequest(BaseModel):
    title: str
    settings: Optional[Dict[str, Any]] = {}
    session_metadata: Optional[Dict[str, Any]] = {}

class SessionResponse(BaseModel):
    id: str
    session_id: str
    user_id: str
    title: str
    message_count: int
    total_tokens_used: int
    created_at: datetime
    updated_at: Optional[datetime]
    last_activity: datetime
    
    class Config:
        from_attributes = True

class SessionListResponse(BaseModel):
    sessions: List[SessionResponse]
    total: int

@router.post("/sessions", response_model=SessionResponse)
async def create_conversation_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new conversation session."""
    try:
        # Generate unique session ID
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        # Create new session
        session = ConversationSession(
            session_id=session_id,
            user_id=current_user.id,
            title=request.title,
            settings=request.settings or {},
            session_metadata=request.session_metadata or {},
            message_count=0,
            total_tokens_used=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return SessionResponse(
            id=str(session.id),
            session_id=session.session_id,
            user_id=str(session.user_id),
            title=session.title,
            message_count=session.message_count,
            total_tokens_used=session.total_tokens_used,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_activity=session.last_activity
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation session: {str(e)}"
        )

@router.get("/sessions", response_model=SessionListResponse)
async def get_conversation_sessions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's conversation sessions."""
    try:
        # Query user's sessions
        sessions_query = db.query(ConversationSession).filter(
            ConversationSession.user_id == current_user.id
        )
        
        total = sessions_query.count()
        sessions = sessions_query.offset(skip).limit(limit).all()
        
        session_responses = [
            SessionResponse(
                id=str(session.id),
                session_id=session.session_id,
                user_id=str(session.user_id),
                title=session.title,
                message_count=session.message_count,
                total_tokens_used=session.total_tokens_used,
                created_at=session.created_at,
                updated_at=session.updated_at,
                last_activity=session.last_activity
            )
            for session in sessions
        ]
        
        return SessionListResponse(
            sessions=session_responses,
            total=total
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation sessions: {str(e)}"
        )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific conversation session."""
    try:
        session = db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id,
            ConversationSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found"
            )
        
        return SessionResponse(
            id=str(session.id),
            session_id=session.session_id,
            user_id=str(session.user_id),
            title=session.title,
            message_count=session.message_count,
            total_tokens_used=session.total_tokens_used,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_activity=session.last_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve conversation session: {str(e)}"
        )

@router.delete("/sessions/{session_id}")
async def delete_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a conversation session."""
    try:
        session = db.query(ConversationSession).filter(
            ConversationSession.session_id == session_id,
            ConversationSession.user_id == current_user.id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation session not found"
            )
        
        db.delete(session)
        db.commit()
        
        return {"message": "Conversation session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation session: {str(e)}"
        )
