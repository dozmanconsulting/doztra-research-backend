"""
AI Service for handling interactions with AI models.
"""

from typing import List, Dict, Any, Tuple
import logging
import httpx
import json
import os
from fastapi import HTTPException, status

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)


async def get_ai_response(
    messages: List[Dict[str, str]],
    model: str = "gpt-3.5-turbo",
    temperature: float = 0.7,
    max_tokens: int = 1000
) -> Tuple[str, Dict[str, int]]:
    """
    Get a response from the AI model.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        model: The AI model to use
        temperature: Controls randomness (0-1)
        max_tokens: Maximum tokens in the response
        
    Returns:
        Tuple of (response_text, usage_stats)
    """
    # Add system message if not present
    if not any(msg.get("role") == "system" for msg in messages):
        messages.insert(0, {
            "role": "system",
            "content": "You are Doztra AI, a helpful and knowledgeable assistant."
        })
    
    # Log the API key (first 5 chars only for security)
    if settings.OPENAI_API_KEY:
        api_key_preview = settings.OPENAI_API_KEY[:5] + "..." if len(settings.OPENAI_API_KEY) > 5 else "not set"
        api_key_length = len(settings.OPENAI_API_KEY)
        logger.info(f"Using OpenAI API key starting with: {api_key_preview}, length: {api_key_length}")
        
        # Check if the API key starts with 'sk-'
        if not settings.OPENAI_API_KEY.startswith('sk-'):
            logger.warning(f"OpenAI API key does not start with 'sk-', it starts with: {settings.OPENAI_API_KEY[:3]}")
    else:
        logger.error("OpenAI API key is not set!")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OpenAI API key is not configured"
        )
    
    # Log the request details
    logger.info(f"Sending request to OpenAI API with model: {model}")
    logger.info(f"API URL: {settings.OPENAI_API_URL}/chat/completions")
    logger.info(f"Number of messages: {len(messages)}")
    
    try:
        # Use httpx for async HTTP requests
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info("Making API request to OpenAI...")
            response = await client.post(
                f"{settings.OPENAI_API_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }
            )
            logger.info(f"Received response with status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Error communicating with AI service"
                )
            
            response_data = response.json()
            response_text = response_data["choices"][0]["message"]["content"].strip()
            usage = {
                "prompt_tokens": response_data["usage"]["prompt_tokens"],
                "completion_tokens": response_data["usage"]["completion_tokens"],
                "total_tokens": response_data["usage"]["total_tokens"]
            }
            
            return response_text, usage
            
    except httpx.TimeoutException:
        logger.error("Timeout when calling OpenAI API")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI service request timed out"
        )
    except Exception as e:
        logger.error(f"Error getting AI response: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error when processing AI request"
        )


async def moderate_content(content: str) -> bool:
    """
    Check if content violates OpenAI's content policy.
    
    Args:
        content: Text content to moderate
        
    Returns:
        True if content is flagged, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{settings.OPENAI_API_URL}/moderations",
                headers={
                    "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": content
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"Moderation API error: {response.status_code} - {response.text}")
                return False
            
            result = response.json()
            return result["results"][0]["flagged"]
            
    except Exception as e:
        logger.error(f"Error in content moderation: {str(e)}")
        return False
