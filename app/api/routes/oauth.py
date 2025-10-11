"""
OAuth routes for authentication with external providers.
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.db.session import get_db
from app.schemas.oauth import OAuthCallback
from app.schemas.user import UserWithToken
from app.services.oauth import get_oauth_login_url, handle_oauth_callback


router = APIRouter()


@router.get("/login/{provider}")
async def oauth_login(provider: str, redirect_uri: str = None):
    """
    Initiate OAuth login flow with the specified provider.
    
    Args:
        provider: OAuth provider (e.g., 'google')
        redirect_uri: Optional override for the redirect URI
        
    Returns:
        RedirectResponse: Redirect to the OAuth provider's authorization URL
    """
    try:
        login_url = await get_oauth_login_url(provider)
        return RedirectResponse(url=login_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


import logging
from urllib.parse import urlencode
logger = logging.getLogger(__name__)

@router.get("/google/callback")
async def google_oauth_callback(
    request: Request,
    db: Session = Depends(get_db),
    code: str = Query(...),
    state: str = Query(None)
):
    """
    Handle the callback from Google OAuth.
    
    Args:
        request: The request object
        db: Database session
        code: Authorization code from Google
        state: State parameter for CSRF protection
        
    Returns:
        UserWithToken: User data with access and refresh tokens
    """
    try:
        logger.info(f"Google OAuth callback received with code: {code[:10]}...")
        logger.info(f"Request URL: {request.url}")
        logger.info(f"Request headers: {request.headers}")
        token_response, user = await handle_oauth_callback("google", code, db)
        logger.info(f"OAuth callback successful for user: {user.email}")
        
        # Get the frontend URL - use state parameter if provided, otherwise default to home
        frontend_url = state if state else '/'
        
        # If frontend_url doesn't start with http, assume it's a relative path
        if not frontend_url.startswith('http'):
            frontend_url = 'https://doztra.ai' + ('' if frontend_url.startswith('/') else '/') + frontend_url
        
        # Add tokens as query parameters
        params = {
            'access_token': token_response['access_token'],
            'token_type': token_response['token_type'],
            'user_email': user.email,
            'user_name': user.name,
            'success': 'true'
        }
        
        # Add refresh token if available
        if 'refresh_token' in token_response:
            params['refresh_token'] = token_response['refresh_token']
        
        # Create the redirect URL with query parameters
        redirect_url = f"{frontend_url}?{urlencode(params)}"
        logger.info(f"Redirecting to frontend: {frontend_url}")
        
        # Redirect to the frontend
        return RedirectResponse(url=redirect_url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"OAuth callback error: {str(e)}"
        )
