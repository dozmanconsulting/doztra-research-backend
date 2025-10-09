"""
Mock authentication utilities for testing.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User


# Password hashing context (for tests)
def get_password_hash(password: str) -> str:
    """Hash a password for storing."""
    return f"hashed_{password}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return hashed_password == f"hashed_{plain_password}"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, "test_secret_key", algorithm="HS256")
    
    return encoded_jwt


def get_test_token(user: User) -> str:
    """Generate a test JWT token for the given user."""
    expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode = {
        "sub": user.id,
        "exp": expire,
        "email": user.email,
        "role": user.role
    }
    
    encoded_jwt = jwt.encode(to_encode, "test_secret_key", algorithm="HS256")
    return encoded_jwt
