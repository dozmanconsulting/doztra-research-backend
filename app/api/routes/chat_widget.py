"""
API routes for ChatWidget functionality.
Dedicated endpoints for the landing page chat widget.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
from pydantic import BaseModel, Field

from app.services.chat_widget import chat_widget_service

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models for ChatWidget API
class ChatWidgetMessage(BaseModel):
    """Request model for chat widget messages."""
    message: str = Field(..., description="The user's message")
    conversation_history: Optional[List[Dict[str, str]]] = Field(None, description="Previous conversation messages")
    selected_option: Optional[str] = Field(None, description="Selected chat option ID")
    user_id: Optional[str] = Field(None, description="Optional user ID for tracking")

class ChatWidgetResponse(BaseModel):
    """Response model for chat widget messages."""
    response: str
    conversation_id: str
    message_id: str
    tool_recommendation: Optional[str] = None
    usage: Dict[str, Any] = {}
    timestamp: str
    selected_option: Optional[str] = None

class ChatOptionResponse(BaseModel):
    """Response model for chat option selection."""
    response: str
    conversation_id: str
    message_id: str
    tool_recommendation: Optional[str] = None
    usage: Dict[str, Any] = {}
    timestamp: str
    selected_option: str

class InitialMessageResponse(BaseModel):
    """Response model for initial chat widget message."""
    id: str
    text: str
    isBot: bool
    timestamp: str
    options: List[Dict[str, str]]

@router.post("/message", response_model=ChatWidgetResponse, status_code=status.HTTP_200_OK)
async def send_widget_message(request: ChatWidgetMessage):
    """
    Send a message to the chat widget and get an AI response.
    
    This endpoint processes user messages in the chat widget and returns
    AI-generated responses with tool recommendations.
    
    Parameters:
    - **message**: The user's message content
    - **conversation_history**: Optional previous messages in the conversation
    - **selected_option**: Optional selected chat option for context
    - **user_id**: Optional user ID for analytics
    
    Returns:
    - **response**: AI-generated response text
    - **conversation_id**: Session ID for the conversation
    - **message_id**: Unique ID for this response
    - **tool_recommendation**: Recommended tool/feature based on the message
    - **usage**: Token usage information
    - **timestamp**: When the response was generated
    """
    try:
        logger.info(f"Processing chat widget message: {request.message[:50]}...")
        
        result = await chat_widget_service.process_widget_message(
            message=request.message,
            conversation_history=request.conversation_history,
            selected_option=request.selected_option,
            user_id=request.user_id
        )
        
        return ChatWidgetResponse(**result)
        
    except Exception as e:
        logger.error(f"Error processing chat widget message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your message"
        )

@router.post("/option/{option_id}", response_model=ChatOptionResponse, status_code=status.HTTP_200_OK)
async def select_chat_option(option_id: str):
    """
    Handle selection of a predefined chat option.
    
    This endpoint processes when a user clicks on one of the predefined
    chat option buttons (e.g., "Find Academic Sources").
    
    Parameters:
    - **option_id**: ID of the selected chat option
    
    Returns:
    - **response**: Predefined response for the selected option
    - **conversation_id**: Session ID for the conversation
    - **message_id**: Unique ID for this response
    - **tool_recommendation**: The selected option ID
    - **usage**: Token usage information (empty for predefined responses)
    - **timestamp**: When the response was generated
    - **selected_option**: The selected option ID
    """
    try:
        logger.info(f"Processing chat option selection: {option_id}")
        
        # Validate option ID
        valid_options = [opt["id"] for opt in chat_widget_service.get_chat_options()]
        if option_id not in valid_options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid option ID: {option_id}"
            )
        
        result = await chat_widget_service.get_option_response(option_id)
        
        return ChatOptionResponse(**result)
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error processing chat option selection: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your selection"
        )

@router.get("/options", response_model=List[Dict[str, str]], status_code=status.HTTP_200_OK)
async def get_chat_options():
    """
    Get available chat options for the widget.
    
    This endpoint returns the list of predefined chat options that users
    can select from in the chat widget.
    
    Returns:
    - List of chat options with IDs and labels
    """
    try:
        options = chat_widget_service.get_chat_options()
        return options
        
    except Exception as e:
        logger.error(f"Error retrieving chat options: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving chat options"
        )

@router.get("/initial", response_model=InitialMessageResponse, status_code=status.HTTP_200_OK)
async def get_initial_message():
    """
    Get the initial welcome message for the chat widget.
    
    This endpoint returns the initial message that appears when the
    chat widget first opens, along with the available options.
    
    Returns:
    - **id**: Unique ID for the message
    - **text**: Welcome message text
    - **isBot**: Always true for initial message
    - **timestamp**: When the message was generated
    - **options**: Available chat options
    """
    try:
        initial_message = chat_widget_service.get_initial_message()
        return InitialMessageResponse(**initial_message)
        
    except Exception as e:
        logger.error(f"Error retrieving initial message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while retrieving the initial message"
        )

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    Health check endpoint for the chat widget service.
    
    Returns:
    - Service status and timestamp
    """
    return {
        "status": "healthy",
        "service": "chat_widget",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }
