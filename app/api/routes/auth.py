from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
import uuid
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# App imports
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

# Service imports
from app.services.user import get_user_by_email, create_user, authenticate_user
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_password
)

# Utility imports
from app.utils.email import send_welcome_email, send_verification_email, send_password_reset_email
from app.utils.security import generate_verification_token, verify_verification_token, generate_password_reset_token, verify_password_reset_token
from app.utils.uuid_helper import convert_uuid_to_str
from app.services.klaviyo import send_user_signed_up_event

router = APIRouter()

@router.get("/test")
def test_endpoint():
    """Simple test endpoint to check if the server is responding."""
    logger.info("Test endpoint called")
    return {"status": "ok", "message": "Server is running"}

@router.post("/debug-auth")
def debug_auth(request: dict = Body(...), db: Session = Depends(get_db)):
    """Debug endpoint to test authentication directly."""
    email = request.get("email")
    password = request.get("password")
    
    if not email or not password:
        return {"status": "error", "message": "Email and password are required"}
    
    logger.info(f"Debug auth attempt for email: {email}")
    
    try:
        # Try to get user by email first
        user = get_user_by_email(db, email=email)
        logger.info(f"User found: {user is not None}")
        
        if user:
            # Check password
            is_password_valid = verify_password(password, user.hashed_password)
            logger.info(f"Password valid: {is_password_valid}")
            
            if is_password_valid:
                return {"status": "success", "message": "Authentication successful", "user_id": str(user.id)}
            else:
                return {"status": "error", "message": "Invalid password"}
        else:
            return {"status": "error", "message": "User not found"}
    except Exception as e:
        logger.error(f"Debug auth error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {"status": "error", "message": f"Authentication error: {str(e)}"}

@router.post("/register", response_model=UserWithToken, status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
    background: BackgroundTasks = None
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
    
    # Send internal welcome email only if Klaviyo is not configured
    try:
        if not settings.KLAVIYO_API_KEY:
            send_welcome_email(user.email, user.name)
    except Exception:
        # Never break signup if email sending fails
        pass

    # Fire Klaviyo signup event in the background (non-blocking)
    try:
        if background is not None:
            plan_value = None
            try:
                plan_value = (
                    user.subscription.plan.value
                    if hasattr(user, "subscription") and user.subscription and hasattr(user.subscription.plan, "value")
                    else (user.subscription.plan if hasattr(user, "subscription") and user.subscription else None)
                )
            except Exception:
                plan_value = None
            background.add_task(send_user_signed_up_event, email=user.email, first_name=user.name, plan=plan_value)
    except Exception:
        # Never break signup if analytics fails
        pass
    
    # Create a clean dictionary for the response
    user_data = {
        "id": str(user.id),
        "email": user.email,
        "name": user.name,
        "role": user.role.value if hasattr(user.role, "value") else user.role,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        "last_login": user.last_login.isoformat() if user.last_login else None
    }
    
    # Add subscription data if available
    if hasattr(user, "subscription") and user.subscription:
        user_data["subscription"] = {
            "id": str(user.subscription.id),
            "user_id": str(user.subscription.user_id),
            "plan": user.subscription.plan.value if hasattr(user.subscription.plan, "value") else user.subscription.plan,
            "status": user.subscription.status.value if hasattr(user.subscription.status, "value") else user.subscription.status,
            "is_active": user.subscription.is_active,
            "created_at": user.subscription.created_at.isoformat() if user.subscription.created_at else None,
            "updated_at": user.subscription.updated_at.isoformat() if user.subscription.updated_at else None,
            "expires_at": user.subscription.expires_at.isoformat() if user.subscription.expires_at else None
        }
    
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
    logger.info(f"Login attempt for user: {form_data.username}")
    logger.info(f"Form data: {form_data.__dict__}")
    
    try:
        user = authenticate_user(db, form_data.username, form_data.password)
        logger.info(f"Authentication result: {'Success' if user else 'Failed'}")
        
        if not user:
            logger.warning(f"Login failed for user: {form_data.username} - Invalid credentials")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}",
        )
    
    try:
        # Create access token
        logger.info(f"Creating access token for user ID: {user.id}")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        logger.info("Access token created successfully")
        
        # Create refresh token
        logger.info(f"Creating refresh token for user ID: {user.id}")
        refresh_token_value = create_refresh_token(db, user.id)
        logger.info("Refresh token created successfully")
        
        # Update last login time
        logger.info(f"Updating last login time for user ID: {user.id}")
        user.last_login = datetime.utcnow()
        db.commit()
        logger.info("Last login time updated successfully")
    except Exception as e:
        logger.error(f"Error during token creation: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token creation error: {str(e)}",
        )
    
    # Create a clean dictionary for the response
    logger.info("Creating user data dictionary for response")
    try:
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None
        }
        logger.info("Basic user data created successfully")
    except Exception as e:
        logger.error(f"Error creating user data dictionary: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating response data: {str(e)}",
        )
    
    # Add subscription data if available
    try:
        if hasattr(user, "subscription") and user.subscription:
            logger.info(f"Adding subscription data for user ID: {user.id}")
            user_data["subscription"] = {
                "id": str(user.subscription.id),
                "user_id": str(user.subscription.user_id),
                "plan": user.subscription.plan.value if hasattr(user.subscription.plan, "value") else user.subscription.plan,
                "status": user.subscription.status.value if hasattr(user.subscription.status, "value") else user.subscription.status,
                "is_active": user.subscription.is_active,
                "created_at": user.subscription.created_at.isoformat() if user.subscription.created_at else None,
                "updated_at": user.subscription.updated_at.isoformat() if user.subscription.updated_at else None,
                "expires_at": user.subscription.expires_at.isoformat() if user.subscription.expires_at else None
            }
            logger.info("Subscription data added successfully")
        else:
            logger.info(f"No subscription data found for user ID: {user.id}")
    except Exception as e:
        logger.error(f"Error adding subscription data: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Continue without subscription data rather than failing the request
    
    # Create final response
    try:
        logger.info("Creating final response with tokens")
        response_data = {
            **user_data,
            "access_token": access_token,
            "refresh_token": refresh_token_value,
            "token_type": "bearer",
            "success": True
        }
        logger.info("Login successful, returning response")
        return response_data
    except Exception as e:
        logger.error(f"Error creating final response: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating final response: {str(e)}",
        )


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
