"""
Conversation Management API Routes
Handles conversation sessions, memory, and chat history for the knowledge base system.
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User
from app.schemas.conversations import (
    ConversationSession,
    ConversationMessage,
    CreateSessionRequest,
    CreateSessionResponse,
    SendMessageRequest,
    SendMessageResponse,
    ConversationSummary,
    SessionListResponse
)
from app.services.knowledge_base import ConversationMemory
from app.services.conversations import ConversationService

router = APIRouter(prefix="/api/v1/conversations", tags=["Conversations"])

# Initialize services
conversation_memory = ConversationMemory()
conversation_service = ConversationService()


@router.post("/", response_model=CreateSessionResponse)
async def create_conversation_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new conversation session.
    """
    try:
        session_id = str(uuid.uuid4())
        
        # Create session in database
        session = await conversation_service.create_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            title=request.title or "New Conversation",
            metadata=request.metadata or {}
        )
        
        # Initialize session in Zep AI memory
        await conversation_memory.create_session(
            session_id=session_id,
            user_id=current_user.id,
            metadata={  
                "user_name": current_user.name,
                "user_email": current_user.email,
                **request.metadata or {}
            }
        )
        
        return CreateSessionResponse(
            session_id=session_id,
            title=session.title,
            created_at=session.created_at,
            message="Conversation session created successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create conversation session: {str(e)}")


@router.get("/", response_model=SessionListResponse)
async def list_conversation_sessions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's conversation sessions.
    """
    try:
        sessions = await conversation_service.list_sessions(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        total_count = await conversation_service.count_sessions(
            db=db,
            user_id=current_user.id
        )
        
        return SessionListResponse(
            sessions=sessions,
            total_count=total_count,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list conversation sessions: {str(e)}")


@router.get("/{session_id}", response_model=ConversationSession)
async def get_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific conversation session with its messages.
    """
    try:
        session = await conversation_service.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Get messages from Zep AI memory
        messages = await conversation_memory.get_session_messages(session_id)
        
        return ConversationSession(
            id=session.id,
            session_id=session.session_id,
            title=session.title,
            messages=messages,
            created_at=session.created_at,
            updated_at=session.updated_at,
            metadata=session.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation session: {str(e)}")


@router.post("/{session_id}/messages", response_model=SendMessageResponse)
async def send_message(
    session_id: str,
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message in a conversation session.
    """
    try:
        # Verify session exists and belongs to user
        session = await conversation_service.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Add user message to memory
        user_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="user",
            content=request.message,
            timestamp=datetime.utcnow(),
            metadata=request.metadata or {}
        )
        
        await conversation_memory.add_message(session_id, user_message.dict())
        
        # Get conversation context for RAG
        conversation_context = await conversation_memory.get_relevant_memory(
            session_id=session_id,
            query=request.message
        )
        
        # Process message through knowledge base (import here to avoid circular imports)
        from app.services.knowledge_base import KnowledgeBaseService
        kb_service = KnowledgeBaseService()
        
        # Generate response using RAG
        rag_response = await kb_service.process_conversation_query(
            query=request.message,
            user_id=current_user.id,
            session_id=session_id,
            conversation_context=conversation_context,
            content_filters=request.content_filters
        )
        
        # Create assistant message
        assistant_message = ConversationMessage(
            id=str(uuid.uuid4()),
            role="assistant",
            content=rag_response["answer"],
            timestamp=datetime.utcnow(),
            sources=rag_response.get("sources", []),
            metadata={
                "processing_time": rag_response.get("processing_time", 0),
                "model_used": rag_response.get("model_used", "default"),
                "confidence_score": rag_response.get("confidence_score", 0)
            }
        )
        
        # Add assistant message to memory
        await conversation_memory.add_message(session_id, assistant_message.dict())
        
        # Update session timestamp
        await conversation_service.update_session_timestamp(
            db=db,
            session_id=session_id
        )
        
        # Queue background tasks for analytics and learning
        background_tasks.add_task(
            conversation_service.analyze_conversation_quality,
            session_id=session_id,
            user_message=user_message.dict(),
            assistant_message=assistant_message.dict()
        )
        
        return SendMessageResponse(
            message_id=assistant_message.id,
            content=assistant_message.content,
            sources=assistant_message.sources,
            timestamp=assistant_message.timestamp,
            metadata=assistant_message.metadata
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send message: {str(e)}")


@router.get("/{session_id}/messages", response_model=List[ConversationMessage])
async def get_conversation_messages(
    session_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get messages from a conversation session.
    """
    try:
        # Verify session exists and belongs to user
        session = await conversation_service.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Get messages from Zep AI memory
        messages = await conversation_memory.get_session_messages(
            session_id=session_id,
            skip=skip,
            limit=limit
        )
        
        return messages
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation messages: {str(e)}")


@router.put("/{session_id}/title")
async def update_session_title(
    session_id: str,
    title: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the title of a conversation session.
    """
    try:
        success = await conversation_service.update_session_title(
            db=db,
            session_id=session_id,
            user_id=current_user.id,
            title=title
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        return {"message": "Session title updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update session title: {str(e)}")


@router.delete("/{session_id}")
async def delete_conversation_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a conversation session and its messages.
    """
    try:
        # Delete from database
        success = await conversation_service.delete_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Delete from Zep AI memory
        await conversation_memory.delete_session(session_id)
        
        return {"message": "Conversation session deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete conversation session: {str(e)}")


@router.get("/{session_id}/summary", response_model=ConversationSummary)
async def get_conversation_summary(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a summary of the conversation session.
    """
    try:
        # Verify session exists and belongs to user
        session = await conversation_service.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Get summary from Zep AI memory
        summary = await conversation_memory.summarize_session(session_id)
        
        return ConversationSummary(
            session_id=session_id,
            title=session.title,
            summary=summary["summary"],
            key_topics=summary.get("key_topics", []),
            message_count=summary.get("message_count", 0),
            duration_minutes=summary.get("duration_minutes", 0),
            created_at=session.created_at,
            last_activity=session.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation summary: {str(e)}")


@router.post("/{session_id}/export")
async def export_conversation(
    session_id: str,
    format: str = "json",  # json, markdown, pdf
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export conversation session in various formats.
    """
    try:
        # Verify session exists and belongs to user
        session = await conversation_service.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Get all messages
        messages = await conversation_memory.get_session_messages(session_id)
        
        # Export in requested format
        exported_data = await conversation_service.export_conversation(
            session=session,
            messages=messages,
            format=format
        )
        
        # Return as streaming response for file download
        if format == "pdf":
            return StreamingResponse(
                exported_data,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=conversation_{session_id}.pdf"}
            )
        elif format == "markdown":
            return StreamingResponse(
                exported_data,
                media_type="text/markdown",
                headers={"Content-Disposition": f"attachment; filename=conversation_{session_id}.md"}
            )
        else:  # json
            return StreamingResponse(
                exported_data,
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=conversation_{session_id}.json"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export conversation: {str(e)}")


@router.post("/{session_id}/feedback")
async def submit_conversation_feedback(
    session_id: str,
    message_id: str,
    rating: int,  # 1-5 scale
    feedback: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback for a specific message in the conversation.
    """
    try:
        # Verify session exists and belongs to user
        session = await conversation_service.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Store feedback
        await conversation_service.store_message_feedback(
            db=db,
            session_id=session_id,
            message_id=message_id,
            user_id=current_user.id,
            rating=rating,
            feedback=feedback
        )
        
        return {"message": "Feedback submitted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit feedback: {str(e)}")


@router.get("/{session_id}/analytics")
async def get_conversation_analytics(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get analytics and insights for a conversation session.
    """
    try:
        # Verify session exists and belongs to user
        session = await conversation_service.get_session(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(status_code=404, detail="Conversation session not found")
        
        # Get analytics from conversation service
        analytics = await conversation_service.get_session_analytics(
            db=db,
            session_id=session_id
        )
        
        return analytics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get conversation analytics: {str(e)}")
