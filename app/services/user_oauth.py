"""
Extended user service with OAuth support.
"""
from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate


def get_user_by_oauth_id(db: Session, provider: str, oauth_user_id: str) -> Optional[User]:
    """
    Get a user by their OAuth provider and ID.
    
    Args:
        db: Database session
        provider: OAuth provider name (e.g., 'google')
        oauth_user_id: User ID from the OAuth provider
        
    Returns:
        Optional[User]: User object if found, None otherwise
    """
    return db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_user_id == oauth_user_id
    ).first()


def create_oauth_user(
    db: Session, 
    email: str, 
    name: str, 
    provider: str, 
    oauth_user_id: str,
    oauth_access_token: str,
    oauth_refresh_token: Optional[str] = None
) -> User:
    """
    Create a new user from OAuth data.
    
    Args:
        db: Database session
        email: User's email
        name: User's name
        provider: OAuth provider name
        oauth_user_id: User ID from the OAuth provider
        oauth_access_token: OAuth access token
        oauth_refresh_token: OAuth refresh token (optional)
        
    Returns:
        User: Created user object
    """
    user_data = UserCreate(
        email=email,
        name=name,
        password=None  # No password for OAuth users
    )
    
    # Create user with basic info
    from app.services.user import create_user
    user = create_user(db, user_data)
    
    # Add OAuth info
    user.oauth_provider = provider
    user.oauth_user_id = oauth_user_id
    user.oauth_access_token = oauth_access_token
    user.oauth_refresh_token = oauth_refresh_token
    user.is_verified = True  # OAuth emails are verified
    
    db.commit()
    db.refresh(user)
    
    return user
