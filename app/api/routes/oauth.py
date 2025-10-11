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


@router.get("/google/callback", response_model=UserWithToken)
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
        token_response, user = await handle_oauth_callback("google", code, db)
        
        # Create response with user data and tokens
        user_data = {
            "id": str(user.id),
            "email": user.email,
            "name": user.name,
            "role": user.role.value if hasattr(user.role, "value") else user.role,
            "is_active": user.is_active,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "oauth_provider": user.oauth_provider
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
            **token_response
        }
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
