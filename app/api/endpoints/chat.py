"""
API endpoints for chat functionality with document context.
"""
from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.models.user import User
from app.services import openai_service

router = APIRouter(prefix="/chat", tags=["chat"])


class QueryRequest(BaseModel):
    """
    Request model for document-based queries.
    """
    message: str = Field(..., description="The user's query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to use as context")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options for the query")


class QueryResponse(BaseModel):
    """
    Response model for document-based queries.
    """
    answer: str = Field(..., description="The AI's response to the query")
    sources: List[Dict[str, Any]] = Field(..., description="Sources used to generate the response")
    query: str = Field(..., description="The original query")
    model: str = Field(..., description="The model used to generate the response")


@router.post("/query", response_model=QueryResponse)
async def query_with_documents_endpoint(
    request: QueryRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Query the AI with document context.
    """
    try:
        # Call the service function
        response = await openai_service.query_with_documents(
            query=request.message,
            user_id=current_user.id,
            document_ids=request.document_ids,
            options=request.options
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


class MessageRequest(BaseModel):
    """
    Request model for standard chat messages.
    """
    messages: List[Dict[str, Any]] = Field(..., description="List of message dictionaries with 'role' and 'content'")


@router.post("/message")
async def chat_message(
    request: MessageRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Send a standard chat message without document context.
    """
    try:
        # Validate messages format
        for msg in request.messages:
            if "role" not in msg or "content" not in msg:
                raise HTTPException(status_code=400, detail="Each message must have 'role' and 'content' fields")
                
            if msg["role"] not in ["system", "user", "assistant"]:
                raise HTTPException(status_code=400, detail="Message role must be 'system', 'user', or 'assistant'")
        
        # Call the service function
        response = await openai_service.generate_chat_response(request.messages)
        
        return {"response": response}
        
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


class DocumentSearchRequest(BaseModel):
    """
    Request model for semantic search across documents.
    """
    query: str = Field(..., description="The search query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to restrict the search to")
    top_k: int = Field(5, description="Number of results to return")


@router.post("/search")
async def search_documents(
    request: DocumentSearchRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Perform semantic search across documents.
    """
    try:
        # Call the service function
        results = await openai_service.search_document_chunks(
            query=request.query,
            user_id=current_user.id,
            document_ids=request.document_ids,
            top_k=request.top_k
        )
        
        return {"results": results}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.post("/conversation/{conversation_id}/context")
async def add_document_context(
    conversation_id: str,
    document_ids: List[str] = Body(...),
    current_user: User = Depends(get_current_user)
):
    """
    Add document context to a conversation.
    """
    try:
        # In a real implementation, this would update a conversation record in the database
        # For now, we'll just return success
        return {
            "conversation_id": conversation_id,
            "document_ids": document_ids,
            "message": "Document context added to conversation"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document context: {str(e)}")


@router.delete("/conversation/{conversation_id}/context/{document_id}")
async def remove_document_context(
    conversation_id: str,
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Remove document from conversation context.
    """
    try:
        # In a real implementation, this would update a conversation record in the database
        # For now, we'll just return success
        return {
            "conversation_id": conversation_id,
            "document_id": document_id,
            "message": "Document removed from conversation context"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove document context: {str(e)}")
