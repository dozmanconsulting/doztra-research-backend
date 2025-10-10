"""
Fixed API routes for document-based queries and interactions with LLM.
This module contains the fixed query_with_documents_endpoint function.
"""

from fastapi import APIRouter, Depends, HTTPException, Body, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from app.db.session import get_db
from app.services.auth import get_current_active_user
from app.models.user import User
from app.services import openai_service
from app.services.openai_service_fix import query_with_documents_fixed


router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for document-based queries."""
    message: str = Field(..., description="The user's query")
    document_ids: Optional[List[str]] = Field(None, description="Optional list of document IDs to use as context")
    options: Optional[Dict[str, Any]] = Field(None, description="Additional options for the query")


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
        # Call the fixed service function
        response = await query_with_documents_fixed(
            query=request.message,
            user_id=str(current_user.id),
            document_ids=request.document_ids,
            options=request.options
        )
        
        # Check for specific error conditions
        if "error" in response and response["error"] == "document_not_found":
            # Return a 404 status for missing documents
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=response["answer"]
            )
        
        # Track token usage (in a real implementation)
        # await track_token_usage(db, current_user.id, response.get("usage", {}))
        
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Query failed: {str(e)}"
        )
