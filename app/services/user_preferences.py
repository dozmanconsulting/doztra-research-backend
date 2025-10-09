from sqlalchemy.orm import Session
from typing import Optional
from fastapi import HTTPException, status
from app.models.user_preferences import UserPreferences
from app.schemas.user_preferences import UserPreferencesCreate, UserPreferencesUpdate
from app.models.user import User, ModelTier


def get_user_preferences(db: Session, user_id: str) -> Optional[UserPreferences]:
    """
    Get user preferences.
    """
    return db.query(UserPreferences).filter(UserPreferences.user_id == user_id).first()


def create_user_preferences(db: Session, preferences_in: UserPreferencesCreate) -> UserPreferences:
    """
    Create new user preferences.
    """
    db_preferences = UserPreferences(
        user_id=preferences_in.user_id,
        theme=preferences_in.theme,
        notifications=preferences_in.notifications,
        default_model=preferences_in.default_model
    )
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences


def update_user_preferences(db: Session, user_id: str, preferences_in: UserPreferencesUpdate) -> Optional[UserPreferences]:
    """
    Update user preferences.
    """
    db_preferences = get_user_preferences(db, user_id)
    if not db_preferences:
        # Create preferences if they don't exist
        return create_user_preferences(db, UserPreferencesCreate(
            user_id=user_id,
            **preferences_in.dict(exclude_unset=True)
        ))
    
    # Update preferences
    update_data = preferences_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_preferences, field, value)
    
    db.commit()
    db.refresh(db_preferences)
    return db_preferences


def check_model_access(db: Session, user_id: str, model: str) -> bool:
    """
    Check if a user has access to a specific model based on their subscription.
    """
    # Get the user and their subscription
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.subscription:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no active subscription"
        )
    
    # Get the user's max model tier
    max_model_tier = user.subscription.max_model_tier
    
    # Check if the requested model is allowed for the user's tier
    model_tiers = {
        ModelTier.GPT_3_5_TURBO: 1,
        ModelTier.GPT_4: 2,
        ModelTier.GPT_4_TURBO: 3,
        ModelTier.GPT_4_32K: 4,
        ModelTier.CLAUDE_3_OPUS: 5
    }
    
    requested_tier = model_tiers.get(model, 0)
    max_allowed_tier = model_tiers.get(max_model_tier, 0)
    
    if requested_tier > max_allowed_tier:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your subscription does not allow access to {model}"
        )
    
    return True
