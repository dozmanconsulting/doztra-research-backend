"""
API routes for chat functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("Initializing chat API routes")

from app.db.session import get_db
from app.services.auth import get_current_active_user
from app.models.user import User
from app.services.chat import (
    get_user_conversations,
    get_conversation,
    get_conversation_messages,
    create_conversation,
    update_conversation,
    delete_conversation,
    process_chat_message
)
from app.services import openai_service
from app.schemas.chat import (
    ConversationResponse,
    ConversationDetailResponse,
    ConversationUpdate,
    ChatRequest,
    ChatResponse,
    MessageResponse,
    ConversationCreate
)
from app.services.token_usage import require_tokens
logger = logging.getLogger(__name__)

router = APIRouter()


# Document-based query models
class QueryRequest(BaseModel):
    """Request model for document-based queries."""
    message: str = Field(..., description="The user's query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to use as context")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options for the query")


class DocumentSearchRequest(BaseModel):
    """Request model for semantic search across documents."""
    query: str = Field(..., description="The search query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to restrict the search to")
    top_k: int = Field(5, description="Number of results to return")


@router.post("/messages", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Send a message to the AI assistant and get a response.
    
    This endpoint processes a user message and returns an AI-generated response.
    If no conversation_id is provided, a new conversation will be created.
    
    Parameters:
    - **message**: The message content to send
    - **conversation_id**: Optional ID of an existing conversation
    - **model**: AI model to use (default: gpt-3.5-turbo)
    - **temperature**: Controls randomness (0-1)
    - **max_tokens**: Maximum tokens in the response
    - **attachments**: Optional list of attachment IDs
    
    Returns:
    - **conversation_id**: ID of the conversation
    - **message_id**: ID of the AI response message
    - **content**: The AI response text
    - **usage**: Token usage statistics
    - **created_at**: Timestamp of when the response was created
    """
    try:
        from app.utils.uuid_helper import convert_uuid_to_str
        
        require_tokens(db, current_user.id, estimated_tokens=request.max_tokens or 500)
        
        response = await process_chat_message(
            db,
            current_user,
            request.message,
            conversation_id=request.conversation_id,
            model=request.model,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            attachments=request.attachments
        )
        
        # Convert any UUID objects to strings
        response = convert_uuid_to_str(response)
        
        return ChatResponse(
            conversation_id=response["conversation_id"],
            message_id=response["message_id"],
            content=response["content"],
            usage=response["usage"],
            created_at=datetime.utcnow()
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing chat message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    sort_by: str = Query("updated_at", description="Field to sort by"),
    sort_order: str = Query("desc", description="Sort order (asc or desc)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all conversations for the current user.
    
    This endpoint returns a paginated list of the user's conversations,
    sorted according to the specified criteria.
    
    Parameters:
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (default: 20, max: 100)
    - **sort_by**: Field to sort by (default: "updated_at", options: "created_at", "updated_at", "title")
    - **sort_order**: Sort order (default: "desc", options: "asc", "desc")
    
    Returns:
    - List of conversation objects with message counts and last message previews
    """
    try:
        # Import UUID helper
        from app.utils.uuid_helper import convert_uuid_to_str
        
        # Get conversations with pagination
        conversations = get_user_conversations(db, current_user.id, skip, limit, sort_by, sort_order)
        
        # Add message count to each conversation
        for conv in conversations:
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
        
        # Convert UUID objects to strings
        return convert_uuid_to_str(conversations)
    except Exception as e:
        logger.error(f"Error retrieving conversations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving conversations"
        )


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_new_conversation(
    conversation: ConversationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new conversation.
    
    This endpoint creates a new conversation and optionally sends an initial message.
    
    Parameters:
    - **title**: Optional title for the conversation (default: "New Conversation")
    - **initial_message**: Optional initial message to start the conversation
    - **metadata**: Optional metadata for the conversation (JSON object)
    
    Returns:
    - Newly created conversation object
    """
    from app.services.chat import create_conversation
    from app.utils.uuid_helper import convert_uuid_to_str
    
    try:
        # Create the conversation
        new_conversation = create_conversation(
            db, 
            current_user.id, 
            conversation.title,
            metadata=conversation.metadata
        )
        
        # If initial message is provided, process it asynchronously
        if conversation.initial_message:
            await process_chat_message(
                db,
                current_user,
                conversation.initial_message,
                conversation_id=new_conversation.id
            )
        
        return convert_uuid_to_str(new_conversation)
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while creating the conversation"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=ConversationDetailResponse)
async def get_conversation_messages_endpoint(
    conversation_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get messages for a specific conversation with pagination.
    
    This endpoint retrieves messages for a specific conversation with pagination support.
    
    Parameters:
    - **conversation_id**: ID of the conversation to retrieve messages from
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (default: 50, max: 100)
    
    Returns:
    - Conversation details including paginated messages and total message count
    """
    try:
        from app.utils.uuid_helper import convert_uuid_to_str
        
        conversation = get_conversation(db, conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages for the conversation with pagination
        from app.services.chat import get_conversation_messages
        messages = get_conversation_messages(db, conversation_id, current_user.id, skip, limit)
        
        # Get total message count for pagination
        from sqlalchemy import func
        from app.models.chat import Message
        total_count = db.query(func.count(Message.id)).filter(Message.conversation_id == conversation_id).scalar() or 0
        
        # Construct response
        try:
            response = ConversationDetailResponse.from_orm(conversation)
        except Exception as e:
            # If there's an error converting the conversation to a response,
            # create the response manually without using from_orm
            logger.warning(f"Error converting conversation to response: {str(e)}")
            response = ConversationDetailResponse(
                id=str(conversation.id),  # Convert UUID to string explicitly
                title=conversation.title,
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
                is_active=conversation.is_active,
                messages=[],
                total_messages=0
            )
        
        # Convert messages to response models and ensure UUIDs are strings
        response.messages = [MessageResponse.from_orm(convert_uuid_to_str(msg)) for msg in messages]
        response.total_messages = total_count
        
        # Convert any remaining UUIDs to strings
        return convert_uuid_to_str(response)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation detail: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the conversation"
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse, status_code=status.HTTP_200_OK)
async def update_conversation_details(
    conversation_id: str,
    conversation_update: ConversationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a conversation's details.
    
    This endpoint updates the title and/or active status of a conversation.
    
    Parameters:
    - **conversation_id**: ID of the conversation to update
    - **title**: New title for the conversation (optional)
    - **is_active**: New active status for the conversation (optional)
    
    Returns:
    - Updated conversation object
    """
    try:
        from app.utils.uuid_helper import convert_uuid_to_str
        
        updated_conversation = update_conversation(
            db, 
            conversation_id, 
            current_user.id,
            title=conversation_update.title,
            is_active=conversation_update.is_active
        )
        
        if not updated_conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return convert_uuid_to_str(updated_conversation)
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error updating conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while updating the conversation"
        )


@router.delete("/conversations/{conversation_id}", response_model=dict, status_code=status.HTTP_200_OK)
async def delete_user_conversation(
    conversation_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Delete a conversation (soft delete).
    
    This endpoint marks a conversation as inactive (soft delete).
    The conversation data is not permanently deleted from the database.
    
    Parameters:
    - **conversation_id**: ID of the conversation to delete
    
    Returns:
    - Success message and the ID of the deleted conversation
    """
    try:
        success = delete_conversation(db, conversation_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        return {"success": True, "message": "Conversation deleted successfully", "id": conversation_id}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error deleting conversation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while deleting the conversation"
        )


# Document-based query endpoints
@router.post("/query")
async def query_with_documents_endpoint(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Query the AI with document context.
    
    This endpoint allows querying the AI with context from uploaded documents.
    The AI will use the document content to generate a more informed response.
    
    Parameters:
    - **message**: The user's query
    - **document_ids**: Optional list of document IDs to use as context
    - **options**: Additional options for the query (model, temperature, etc.)
    
    Returns:
    - AI-generated response with citations to relevant document parts
    - Sources used to generate the response
    """
    try:
        # Call the service function
        response = await openai_service.query_with_documents(
            query=request.message,
            user_id=str(current_user.id),
            document_ids=request.document_ids,
            options=request.options
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error querying with documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/search")
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Perform semantic search across documents.
    
    This endpoint searches through the user's documents using semantic similarity
    to find content relevant to the query.
    
    Parameters:
    - **query**: The search query
    - **document_ids**: Optional list of document IDs to restrict the search to
    - **top_k**: Number of results to return (default: 5)
    
    Returns:
    - List of relevant document chunks with similarity scores
    """
    try:
        # Call the service function
        results = await openai_service.search_document_chunks(
            query=request.query,
            user_id=str(current_user.id),
            document_ids=request.document_ids,
            top_k=request.top_k
        )
        
        return {"results": results}
        
    except Exception as e:
        logger.error(f"Error searching documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.post("/conversation/{conversation_id}/context")
async def add_document_context(
    conversation_id: str,
    document_ids: List[str] = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Add document context to a conversation.
    
    This endpoint associates documents with a conversation to provide context
    for future messages in that conversation.
    
    Parameters:
    - **conversation_id**: ID of the conversation
    - **document_ids**: List of document IDs to add as context
    
    Returns:
    - Success message
    """
    try:
        # Check if conversation exists and belongs to user
        conversation = get_conversation(db, conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        # In a real implementation, this would update a conversation record in the database
        # For now, we'll just update the conversation metadata
        
        # Get current metadata or initialize empty dict
        metadata = conversation.metadata or {}
        
        # Add or update document context
        if "document_context" not in metadata:
            metadata["document_context"] = document_ids
        else:
            # Add new document IDs without duplicates
            existing_docs = set(metadata["document_context"])
            existing_docs.update(document_ids)
            metadata["document_context"] = list(existing_docs)
            
        # Update conversation with new metadata
        update_conversation(db, conversation_id, current_user.id, metadata=metadata)
        
        return {
            "conversation_id": conversation_id,
            "document_ids": document_ids,
            "message": "Document context added to conversation"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error adding document context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add document context: {str(e)}"
        )


@router.delete("/conversation/{conversation_id}/context/{document_id}")
async def remove_document_context(
    conversation_id: str,
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Remove document from conversation context.
    
    This endpoint removes a document from a conversation's context.
    
    Parameters:
    - **conversation_id**: ID of the conversation
    - **document_id**: ID of the document to remove
    
    Returns:
    - Success message
    """
    try:
        # Check if conversation exists and belongs to user
        conversation = get_conversation(db, conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
        # Get current metadata
        metadata = conversation.metadata or {}
        
        # Remove document from context if it exists
        if "document_context" in metadata and document_id in metadata["document_context"]:
            metadata["document_context"].remove(document_id)
            
            # Update conversation with new metadata
            update_conversation(db, conversation_id, current_user.id, metadata=metadata)
        
        return {
            "conversation_id": conversation_id,
            "document_id": document_id,
            "message": "Document removed from conversation context"
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error removing document context: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove document context: {str(e)}"
        )
