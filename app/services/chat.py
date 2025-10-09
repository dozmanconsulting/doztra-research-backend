"""
Chat service for managing conversations and messages.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime
from fastapi import HTTPException, status

from app.models.chat import Conversation, Message, MessageRole
from app.models.user import User
from app.services.token_usage import record_token_usage
from app.services.ai import get_ai_response, moderate_content


def create_conversation(
    db: Session, 
    user_id: str, 
    title: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Conversation:
    """
    Create a new conversation.
    
    Args:
        db: Database session
        user_id: ID of the user creating the conversation
        title: Optional title for the conversation
        metadata: Optional metadata for the conversation
        
    Returns:
        Newly created Conversation object
    """
    # Create conversation object with basic fields
    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title or "New Conversation"
    )
    
    # Store metadata in memory for future use when the column is available
    if metadata is not None:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Metadata provided but not stored in database: {metadata}")
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


def get_user_conversations(
    db: Session, 
    user_id: str, 
    skip: int = 0, 
    limit: int = 20,
    sort_by: str = "updated_at",
    sort_order: str = "desc"
) -> List[Conversation]:
    """
    Get all conversations for a user.
    
    Args:
        db: Database session
        user_id: ID of the user
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        sort_by: Field to sort by
        sort_order: Sort order (asc or desc)
        
    Returns:
        List of Conversation objects
    """
    # Validate sort_by field to prevent SQL injection
    valid_sort_fields = ["created_at", "updated_at", "title"]
    if sort_by not in valid_sort_fields:
        sort_by = "updated_at"  # Default to updated_at if invalid field
    
    # Get the sort column
    sort_column = getattr(Conversation, sort_by)
    
    # Apply sort order
    if sort_order.lower() == "asc":
        sort_column = sort_column.asc()
    else:
        sort_column = sort_column.desc()
    
    try:
        # Use a simple query to avoid issues with missing columns
        from sqlalchemy import select
        
        # Create a direct SQL query that only selects specific columns
        stmt = select(
            Conversation.id,
            Conversation.user_id,
            Conversation.title,
            Conversation.created_at,
            Conversation.updated_at,
            Conversation.is_active
        ).where(
            Conversation.user_id == user_id,
            Conversation.is_active == True
        ).order_by(sort_column).offset(skip).limit(limit)
        
        result = db.execute(stmt)
        conversations = []
        for row in result:
            conv = Conversation(
                id=row.id,
                user_id=row.user_id,
                title=row.title,
                created_at=row.created_at,
                updated_at=row.updated_at,
                is_active=row.is_active
            )
            # Add message count and last message preview for frontend
            from sqlalchemy import func
            from app.models.chat import Message
            message_count = db.query(func.count(Message.id)).filter(Message.conversation_id == conv.id).scalar() or 0
            conv.message_count = message_count
            
            # Get last message for preview
            last_message = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at.desc()).first()
            if last_message:
                # Truncate long messages
                preview = last_message.content[:50] + "..." if len(last_message.content) > 50 else last_message.content
                conv.last_message = preview
                
            conversations.append(conv)
        return conversations
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_user_conversations: {str(e)}")
        # Return empty list in case of error
        return []


def get_conversation(
    db: Session, 
    conversation_id: str, 
    user_id: str
) -> Optional[Conversation]:
    """
    Get a specific conversation.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user (for authorization)
        
    Returns:
        Conversation object if found, None otherwise
    """
    try:
        # Use a more explicit query to avoid issues with missing columns
        from sqlalchemy import select
        
        stmt = select(
            Conversation.id,
            Conversation.user_id,
            Conversation.title,
            Conversation.created_at,
            Conversation.updated_at,
            Conversation.is_active
        ).where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
            Conversation.is_active == True
        )
        
        result = db.execute(stmt).first()
        if not result:
            return None
            
        return Conversation(
            id=result.id,
            user_id=result.user_id,
            title=result.title,
            created_at=result.created_at,
            updated_at=result.updated_at,
            is_active=result.is_active
        )
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in get_conversation: {str(e)}")
        return None


def update_conversation(
    db: Session, 
    conversation_id: str, 
    user_id: str, 
    title: Optional[str] = None,
    is_active: Optional[bool] = None
) -> Optional[Conversation]:
    """
    Update a conversation's attributes.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation to update
        user_id: ID of the user (for authorization)
        title: New title for the conversation
        is_active: New active status
        
    Returns:
        Updated Conversation object if found, None otherwise
    """
    conversation = get_conversation(db, conversation_id, user_id)
    if not conversation:
        return None
        
    if title is not None:
        conversation.title = title
    
    if is_active is not None:
        conversation.is_active = is_active
    
    conversation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(conversation)
    return conversation


def delete_conversation(
    db: Session, 
    conversation_id: str, 
    user_id: str
) -> bool:
    """
    Soft delete a conversation.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation to delete
        user_id: ID of the user (for authorization)
        
    Returns:
        True if successful, False otherwise
    """
    conversation = get_conversation(db, conversation_id, user_id)
    if not conversation:
        return False
        
    conversation.is_active = False
    db.commit()
    return True


def create_message(
    db: Session, 
    conversation_id: str, 
    content: str, 
    role: MessageRole, 
    model: Optional[str] = None,
    prompt_tokens: Optional[int] = None,
    completion_tokens: Optional[int] = None,
    message_metadata: Optional[Dict[str, Any]] = None
) -> Message:
    # Add detailed logging
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Creating message with role: {role}, type: {type(role)}, value: {role.value if hasattr(role, 'value') else 'unknown'}")
    """
    Create a new message in a conversation.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        content: Message content
        role: Role of the message sender
        model: AI model used (for assistant messages)
        prompt_tokens: Number of prompt tokens used
        completion_tokens: Number of completion tokens used
        message_metadata: Additional metadata for the message
        
    Returns:
        Newly created Message object
    """
    # Convert role to string if it's an enum
    role_value = role.value if hasattr(role, 'value') else str(role).lower()
    logger.info(f"Using role value: {role_value}")
    
    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        content=content,
        role=role_value,  # Use the string value
        model=model,
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=None if prompt_tokens is None or completion_tokens is None else prompt_tokens + completion_tokens,
        message_metadata=message_metadata
    )
    db.add(message)
    
    # Update conversation timestamp
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation:
        conversation.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(message)
    return message


def get_conversation_messages(
    db: Session, 
    conversation_id: str, 
    user_id: str,
    skip: int = 0,
    limit: int = 50
) -> List[Message]:
    """
    Get messages in a conversation with pagination.
    
    Args:
        db: Database session
        conversation_id: ID of the conversation
        user_id: ID of the user (for authorization)
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        
    Returns:
        List of Message objects
    """
    conversation = get_conversation(db, conversation_id, user_id)
    if not conversation:
        return []
        
    return db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).offset(skip).limit(limit).all()


async def process_chat_message(
    db: Session, 
    user: User, 
    message_content: str, 
    conversation_id: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000,
    attachments: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Process a chat message and get AI response.
    
    Args:
        db: Database session
        user: User object
        message_content: Content of the user's message
        conversation_id: ID of existing conversation (optional)
        model: AI model to use
        temperature: Temperature parameter for AI
        max_tokens: Maximum tokens for AI response
        attachments: List of attachment IDs
        
    Returns:
        Dictionary with conversation_id, message_id, content, and usage
    """
    # Check for content moderation
    is_flagged = await moderate_content(message_content)
    if is_flagged:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message content violates content policy"
        )
    
    # Create or get conversation
    if not conversation_id:
        # Extract title from first message
        title = message_content[:30] + "..." if len(message_content) > 30 else message_content
        # Create a new conversation without metadata for now
        conversation = create_conversation(db, user.id, title)
    else:
        conversation = get_conversation(db, conversation_id, user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
    
    # Create user message
    message_metadata = {"attachments": attachments} if attachments else None
    user_message = create_message(
        db, 
        conversation.id, 
        message_content, 
        MessageRole.user,
        message_metadata=message_metadata
    )
    
    # Get conversation history for context
    conversation_messages = get_conversation_messages(db, conversation.id, user.id)
    
    # Format messages for AI (limit context window to last 20 messages)
    formatted_messages = [
        {"role": msg.role, "content": msg.content} 
        for msg in conversation_messages[-20:]
    ]
    
    # Get AI response
    try:
        ai_response, usage = await get_ai_response(
            formatted_messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Record token usage
        from app.schemas.token_usage import TokenUsageTrack
        from app.models.token_usage import RequestType
        
        token_usage = TokenUsageTrack(
            request_type=RequestType.CHAT,
            model=model,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"],
            total_tokens=usage["total_tokens"]
        )
        
        record_token_usage(db, user.id, token_usage)
        
        # Create assistant message
        assistant_message = create_message(
            db, 
            conversation.id, 
            ai_response, 
            MessageRole.assistant,
            model=model,
            prompt_tokens=usage["prompt_tokens"],
            completion_tokens=usage["completion_tokens"]
        )
        
        return {
            "conversation_id": conversation.id,
            "message_id": assistant_message.id,
            "content": ai_response,
            "usage": usage
        }
    except Exception as e:
        # Log the error with detailed information
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing chat message: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        # Rollback the transaction
        db.rollback()
        
        # Raise a more specific error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message"
        ) from e
