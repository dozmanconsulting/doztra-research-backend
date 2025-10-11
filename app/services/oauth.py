"""
OAuth service for handling authentication with various providers.
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
import httpx
import json
from sqlalchemy.orm import Session
from urllib.parse import urlencode

from app.core.config import settings
from app.core.oauth_config import oauth_configs
from app.models.user import User
from app.services.auth import create_access_token, create_refresh_token
from app.services.user import get_user_by_email, create_user
from app.schemas.user import UserCreate


async def get_oauth_login_url(provider: str) -> str:
    """
    Generate the OAuth login URL for the specified provider.
    
    Args:
        provider: The OAuth provider (e.g., 'google')
        
    Returns:
        str: The URL to redirect the user to for OAuth login
        
    Raises:
        ValueError: If the provider is not supported
    """
    if provider not in oauth_configs:
        raise ValueError(f"Unsupported OAuth provider: {provider}")
    
    config = oauth_configs[provider]
    
    params = {
        'client_id': config.client_id,
        'redirect_uri': config.redirect_uri,
        'response_type': 'code',
        'scope': ' '.join(config.scope),
        'access_type': 'offline',  # For refresh token
        'prompt': 'consent'  # Force to show the consent screen
    }
    
    return f"{config.authorize_url}?{urlencode(params)}"


async def handle_oauth_callback(provider: str, code: str, db: Session) -> Tuple[Dict[str, Any], User]:
    """
    Handle the OAuth callback and authenticate/register the user.
    
    Args:
        provider: The OAuth provider (e.g., 'google')
        code: The authorization code from the callback
        db: Database session
        
    Returns:
        Tuple[Dict[str, Any], User]: Token response and user object
        
    Raises:
        ValueError: If the provider is not supported or authentication fails
    """
    if provider not in oauth_configs:
        raise ValueError(f"Unsupported OAuth provider: {provider}")
    
    config = oauth_configs[provider]
    
    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            config.token_url,
            data={
                'client_id': config.client_id,
                'client_secret': config.client_secret,
                'code': code,
                'grant_type': 'authorization_code',
                'redirect_uri': config.redirect_uri
            }
        )
        
        if token_response.status_code != 200:
            raise ValueError(f"Failed to get token: {token_response.text}")
        
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        
        # Get user info from provider
        userinfo_response = await client.get(
            config.userinfo_url,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        
        if userinfo_response.status_code != 200:
            raise ValueError(f"Failed to get user info: {userinfo_response.text}")
        
        userinfo = userinfo_response.json()
    
    # Process user info based on provider
    if provider == 'google':
        email = userinfo.get('email')
        if not email:
            raise ValueError("Email not provided by Google")
        
        name = userinfo.get('name') or f"{userinfo.get('given_name', '')} {userinfo.get('family_name', '')}".strip()
        oauth_user_id = userinfo.get('sub')
        
        # Check if user exists by OAuth ID
        user = db.query(User).filter(
            User.oauth_provider == provider,
            User.oauth_user_id == oauth_user_id
        ).first()
        
        if not user:
            # Check if user exists by email
            user = get_user_by_email(db, email)
            
            if user:
                # Update existing user with OAuth info
                user.oauth_provider = provider
                user.oauth_user_id = oauth_user_id
                user.is_verified = True  # OAuth emails are verified
            else:
                # Create new user
                user_data = UserCreate(
                    email=email,
                    name=name,
                    password=None  # No password for OAuth users
                )
                user = create_user(db, user_data)
                user.oauth_provider = provider
                user.oauth_user_id = oauth_user_id
                user.is_verified = True
        
        # Update OAuth tokens
        user.oauth_access_token = access_token
        user.oauth_refresh_token = token_data.get('refresh_token')
        
        if 'expires_in' in token_data:
            user.oauth_token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()
        
        # Generate JWT tokens for our system
        access_token = create_access_token(data={"sub": user.id})
        refresh_token = create_refresh_token(db, user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "success": True
        }, user
    
    raise ValueError(f"Unsupported provider implementation: {provider}")


async def refresh_oauth_token(user: User, db: Session) -> bool:
    """
    Refresh the OAuth token if it's expired.
    
    Args:
        user: User object
        db: Database session
        
    Returns:
        bool: True if token was refreshed successfully, False otherwise
    """
    if not user.oauth_provider or not user.oauth_refresh_token:
        return False
    
    if user.oauth_provider not in oauth_configs:
        return False
    
    # Check if token needs refreshing
    if user.oauth_token_expires_at and user.oauth_token_expires_at > datetime.utcnow():
        return True  # Token still valid
    
    config = oauth_configs[user.oauth_provider]
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                config.token_url,
                data={
                    'client_id': config.client_id,
                    'client_secret': config.client_secret,
                    'refresh_token': user.oauth_refresh_token,
                    'grant_type': 'refresh_token'
                }
            )
            
            if response.status_code != 200:
                return False
            
            token_data = response.json()
            user.oauth_access_token = token_data.get('access_token')
            
            if 'refresh_token' in token_data:
                user.oauth_refresh_token = token_data['refresh_token']
                
            if 'expires_in' in token_data:
                user.oauth_token_expires_at = datetime.utcnow() + timedelta(seconds=token_data['expires_in'])
            
            db.commit()
            return True
    except Exception:
        return False
