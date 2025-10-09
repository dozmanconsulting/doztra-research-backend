from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any
import uuid

from app.core.config import settings
from app.db.session import get_db
from app.models.user import User, RefreshToken
from app.schemas.token import Token
from app.schemas.user import UserCreate, User as UserSchema, UserWithToken
from app.schemas.email import (
    EmailVerificationRequest,
    EmailVerificationResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm
)
from app.schemas.message import Message
from app.services.auth import (
    authenticate_user, 
    create_access_token, 
    create_refresh_token,
    get_current_user,
    get_password_hash
)
from app.services.user import create_user, get_user_by_email, verify_user_email
from app.utils.security import (
    generate_verification_token,
    verify_verification_token,
    generate_password_reset_token,
    verify_password_reset_token
)
from app.utils.email import send_verification_email, send_password_reset_email, send_welcome_email

router = APIRouter()


@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> Any:
    """
    Register a new user with optional subscription information.
    """
    # Check if user with this email already exists
    user = get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user with subscription information
    user = create_user(db, user_in)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_value = create_refresh_token(db, user.id)
    
    # Generate verification token and send email
    verification_token = generate_verification_token(user.email)
    send_verification_email(user.email, verification_token)
    
    # Send welcome email
    send_welcome_email(user.email, user.name)
    
    # Create response
    user_data = UserSchema.model_validate(user).model_dump()
    
    # Convert UUID objects to strings
    if "id" in user_data and isinstance(user_data["id"], uuid.UUID):
        user_data["id"] = str(user_data["id"])
    
    if "subscription" in user_data and user_data["subscription"]:
        if "id" in user_data["subscription"] and isinstance(user_data["subscription"]["id"], uuid.UUID):
            user_data["subscription"]["id"] = str(user_data["subscription"]["id"])
        if "user_id" in user_data["subscription"] and isinstance(user_data["subscription"]["user_id"], uuid.UUID):
            user_data["subscription"]["user_id"] = str(user_data["subscription"]["user_id"])
    
    return {
        **user_data,
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer",
        "success": True
    }


@router.post("/login", response_model=UserWithToken)
def login(
    db: Session = Depends(get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token_value = create_refresh_token(db, user.id)
    
    # Update last login time
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create response with user data
    user_data = UserSchema.model_validate(user).model_dump()
    
    # Convert UUID objects to strings
    if "id" in user_data and isinstance(user_data["id"], uuid.UUID):
        user_data["id"] = str(user_data["id"])
    
    if "subscription" in user_data and user_data["subscription"]:
        if "id" in user_data["subscription"] and isinstance(user_data["subscription"]["id"], uuid.UUID):
            user_data["subscription"]["id"] = str(user_data["subscription"]["id"])
        if "user_id" in user_data["subscription"] and isinstance(user_data["subscription"]["user_id"], uuid.UUID):
            user_data["subscription"]["user_id"] = str(user_data["subscription"]["user_id"])
    
    return {
        **user_data,
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer",
        "success": True
    }


@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token_data: dict = Body(...),
    db: Session = Depends(get_db)
) -> Any:
    """
    Refresh access token.
    """
    # Extract refresh token from request data
    refresh_token = refresh_token_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Refresh token is required"
        )
        
    # Find the refresh token in the database
    db_token = db.query(RefreshToken).filter(RefreshToken.token == refresh_token).first()
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Check if token is expired
    if db_token.expires_at < datetime.utcnow():
        # Delete expired token
        db.delete(db_token)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )
    
    # Create new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_token.user_id}, expires_delta=access_token_expires
    )
    
    # Create new refresh token
    new_refresh_token = create_refresh_token(db, db_token.user_id)
    
    # Delete old refresh token
    db.delete(db_token)
    db.commit()
    
    return {
        "success": True,
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }


@router.post("/logout")
def logout(
    refresh_token_data: dict = Body(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Logout user by invalidating refresh token.
    """
    # Extract refresh token from request data
    refresh_token = refresh_token_data.get("refresh_token")
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Refresh token is required"
        )
    
    # Find and delete the refresh token
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.user_id == current_user.id
    ).first()
    
    if db_token:
        db.delete(db_token)
        db.commit()
    
    return {
        "success": True,
        "message": "Successfully logged out"
    }


@router.post("/verify-email/{token}", response_model=EmailVerificationResponse)
def verify_email(
    token: str,
    db: Session = Depends(get_db)
) -> Any:
    """
    Verify user's email address using the token sent via email.
    """
    email = verify_verification_token(token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )
    
    user = get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user.is_verified:
        return {"message": "Email already verified"}
    
    # Mark user as verified
    verify_user_email(db, user)
    
    return {"message": "Email verified successfully"}


@router.post("/password-reset", response_model=Message)
async def request_password_reset(request: dict = Body(...), db: Session = Depends(get_db)):
    """Request a password reset."""
    import logging
    logger = logging.getLogger(__name__)
    
    email = request.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")
        
    user = get_user_by_email(db, email=email)
    if user:
        token = create_access_token(
            data={"sub": user.email, "type": "password_reset", "jti": str(uuid.uuid4())},
            expires_delta=timedelta(hours=24)
        )
        # Log the token for debugging purposes
        logger.info(f"Password reset token for {email}: {token}")
        logger.info(f"Reset URL: https://doztra.ai/reset-password?token={token}")
        send_password_reset_email(email_to=email, token=token)
    
    return {"message": "If your email is registered, you will receive a password reset link"}


@router.post("/reset-password", response_model=PasswordResetResponse)
def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(get_db)
) -> Any:
    """
    Reset user's password using the token received via email.
    """
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token",
        )
    
    user = get_user_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update password
    user.hashed_password = get_password_hash(request.new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Invalidate all refresh tokens for this user (optional security measure)
    db.query(RefreshToken).filter(RefreshToken.user_id == user.id).delete()
    db.commit()
    
    return {"message": "Password reset successfully"}
