from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.models.user import User
from app.schemas.user_preferences import UserPreferences, UserPreferencesUpdate
from app.services.user_preferences import get_user_preferences, update_user_preferences
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=UserPreferences)
def read_user_preferences(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user's preferences.
    """
    preferences = get_user_preferences(db, current_user.id)
    if not preferences:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferences not found"
        )
    return preferences


@router.put("/me", response_model=UserPreferences)
def update_current_user_preferences(
    preferences_in: UserPreferencesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Update current user's preferences.
    """
    # Check if user has access to the specified model based on subscription
    if preferences_in.default_model and current_user.subscription:
        allowed_model = current_user.subscription.max_model_tier
        requested_model = preferences_in.default_model
        
        # Simple model tier check (this could be more sophisticated)
        if requested_model != allowed_model and requested_model == "gpt-4-turbo" and allowed_model != "gpt-4-turbo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your subscription does not allow access to {requested_model}. Please upgrade your plan."
            )
    
    preferences = update_user_preferences(db, current_user.id, preferences_in)
    return preferences
