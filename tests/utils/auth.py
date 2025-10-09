"""
Authentication utilities for tests.
"""

import jwt
from datetime import datetime, timedelta

from app.core.config import settings
from app.models.user import User


def get_test_token(user: User) -> str:
    """
    Generate a test JWT token for the given user.
    
    Args:
        user: User object to generate token for
        
    Returns:
        JWT token string
    """
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "sub": user.id,
        "exp": expire,
        "email": user.email,
        "role": user.role
    }
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
