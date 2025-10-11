"""
Extended authentication service with OAuth support.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import TokenData
from app.services.auth import create_access_token, create_refresh_token
from app.services.user import get_user_by_oauth, get_user_by_email


async def authenticate_oauth_user(
    db: Session,
    provider: str,
    oauth_user_id: str,
    email: str,
    name: str,
    oauth_data: Dict[str, Any]
) -> Tuple[User, Dict[str, Any]]:
    """
    Authenticate a user via OAuth. If the user doesn't exist, create them.
    
    Args:
        db: Database session
        provider: OAuth provider (e.g., 'google')
        oauth_user_id: User ID from the OAuth provider
        email: User's email
        name: User's name
        oauth_data: Additional OAuth data
        
    Returns:
        Tuple[User, Dict[str, Any]]: User object and token response
    """
    # Check if user exists by OAuth credentials
    user = get_user_by_oauth(db, provider, oauth_user_id)
    
    if not user:
        # Check if user exists by email
        user = get_user_by_email(db, email)
        
        if user:
            # Update existing user with OAuth info
            user.oauth_provider = provider
            user.oauth_user_id = oauth_user_id
            user.is_verified = True
            user.oauth_access_token = oauth_data.get('access_token')
            user.oauth_refresh_token = oauth_data.get('refresh_token')
            
            if 'expires_in' in oauth_data:
                user.oauth_token_expires_at = datetime.utcnow() + timedelta(seconds=oauth_data['expires_in'])
                
            db.commit()
        else:
            # Create new user with OAuth info
            from app.schemas.user import UserCreate
            from app.services.user import create_user
            
            user_data = UserCreate(
                email=email,
                name=name,
                password=None,
                oauth_provider=provider,
                oauth_user_id=oauth_user_id
            )
            
            user = create_user(db, user_data)
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Generate JWT tokens for our system
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(db, user.id)
    
    return user, {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "success": True
    }
