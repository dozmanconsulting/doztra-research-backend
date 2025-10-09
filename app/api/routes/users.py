from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Any, List, Dict, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.schemas.user import User as UserSchema, UserUpdate, Subscription, SubscriptionUpdate
from app.schemas.usage_statistics import UsageResponse
from app.services.auth import get_current_user, get_current_active_verified_user
from app.services.user import get_user_by_id, update_user, update_subscription, get_users
from app.services.usage_statistics import get_usage_response
from app.utils.uuid_helper import convert_uuid_to_str

router = APIRouter()


@router.get("/me", response_model=UserSchema)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user.
    """
    # Convert UUID objects to strings
    user_dict = convert_uuid_to_str(current_user)
    return user_dict


@router.put("/me", response_model=UserSchema)
def update_current_user(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update current user.
    """
    user = update_user(db, current_user, user_in)
    # Convert UUID objects to strings
    user_dict = convert_uuid_to_str(user)
    return user_dict


@router.get("/{user_id}", response_model=UserSchema)
def read_user_by_id(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_verified_user),
) -> Any:
    """
    Get a specific user by id.
    """
    # Only allow users to access their own data unless they're an admin (to be implemented)
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions to access this user",
        )
    
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    # Convert UUID objects to strings
    user_dict = convert_uuid_to_str(user)
    return user_dict


@router.put("/me/subscription", response_model=UserSchema)
def update_user_subscription(
    subscription_in: SubscriptionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Update current user's subscription.
    """
    # Extract subscription data
    plan = subscription_in.plan or current_user.subscription.plan if current_user.subscription else SubscriptionPlan.FREE
    status = subscription_in.status or SubscriptionStatus.ACTIVE
    is_active = subscription_in.is_active if subscription_in.is_active is not None else True
    auto_renew = subscription_in.auto_renew if subscription_in.auto_renew is not None else (plan != SubscriptionPlan.FREE)
    
    # Set expiration date based on plan if not provided
    expires_at = subscription_in.expires_at
    if not expires_at and plan != SubscriptionPlan.FREE:
        # Default to 1 month from now for paid plans
        expires_at = datetime.utcnow() + timedelta(days=30)
    
    # Update payment information if provided
    payment_method_id = subscription_in.payment_method_id
    stripe_customer_id = subscription_in.stripe_customer_id
    stripe_subscription_id = subscription_in.stripe_subscription_id
    
    # Update subscription
    user = update_subscription(
        db, 
        current_user, 
        plan=plan,
        status=status,
        expires_at=expires_at,
        is_active=is_active,
        auto_renew=auto_renew,
        payment_method_id=payment_method_id,
        stripe_customer_id=stripe_customer_id,
        stripe_subscription_id=stripe_subscription_id
    )
    # Convert UUID objects to strings
    user_dict = convert_uuid_to_str(user)
    return user_dict


@router.get("/me/subscription", response_model=Subscription)
def get_user_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's subscription.
    """
    if not current_user.subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription not found"
        )
    # Convert UUID objects to strings
    subscription_dict = convert_uuid_to_str(current_user.subscription)
    return subscription_dict


@router.get("/me/usage", response_model=UsageResponse)
def get_user_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Get current user's usage statistics.
    """
    return get_usage_response(db, current_user.id)


# Admin endpoints moved to admin.py
