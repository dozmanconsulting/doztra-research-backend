"""
API routes for document-based queries and interactions with LLM.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services.auth import get_current_active_user
from app.models.user import User
from app.services import openai_service


router = APIRouter()


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


@router.post("/query")
async def query_with_documents_endpoint(
    request: QueryRequest,
    db: Session = Depends(get_db),
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
        
        # Track token usage (in a real implementation)
        # await track_token_usage(db, current_user.id, response.get("usage", {}))
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )


@router.post("/search")
async def search_documents(
    request: DocumentSearchRequest,
    db: Session = Depends(get_db),
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
        from app.services.chat import get_conversation
        conversation = get_conversation(db, conversation_id, current_user.id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
            
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
        from app.services.chat import update_conversation
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
        from app.services.chat import get_conversation
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
            from app.services.chat import update_conversation
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove document context: {str(e)}"
        )
