import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from jose import jwt

from app.core.config import settings


def generate_verification_token(email: str) -> str:
    """Generate a secure token for email verification."""
    # Create a random token
    token = secrets.token_urlsafe(32)
    
    # Create a hash of the token with the email
    token_hash = hashlib.sha256(f"{token}:{email}".encode()).hexdigest()
    
    # Create a JWT with the token hash and expiration
    expires = datetime.utcnow() + timedelta(hours=settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS)
    
    jwt_payload = {
        "sub": email,
        "exp": expires,
        "type": "email_verification",
        "jti": token_hash
    }
    
    return jwt.encode(jwt_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_verification_token(token: str) -> Optional[str]:
    """Verify an email verification token and return the email if valid."""
    try:
        # Decode the JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != "email_verification":
            return None
        
        # Check if token is expired
        if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp")):
            return None
        
        # Return the email
        return payload.get("sub")
    except jwt.JWTError:
        return None


def generate_password_reset_token(email: str) -> str:
    """Generate a secure token for password reset."""
    # Create a random token
    token = secrets.token_urlsafe(32)
    
    # Create a hash of the token with the email
    token_hash = hashlib.sha256(f"{token}:{email}".encode()).hexdigest()
    
    # Create a JWT with the token hash and expiration
    expires = datetime.utcnow() + timedelta(hours=settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
    
    jwt_payload = {
        "sub": email,
        "exp": expires,
        "type": "password_reset",
        "jti": token_hash
    }
    
    return jwt.encode(jwt_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the email if valid."""
    try:
        # Decode the JWT
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != "password_reset":
            return None
        
        # Check if token is expired
        if datetime.utcnow() > datetime.fromtimestamp(payload.get("exp")):
            return None
        
        # Return the email
        return payload.get("sub")
    except jwt.JWTError:
        return None
