from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import uuid
import logging

# Configure logging
logger = logging.getLogger(__name__)

from app.models.user import User, Subscription, SubscriptionPlan, SubscriptionStatus, ModelTier, UserRole
from app.models.user_preferences import UserPreferences
from app.models.usage_statistics import UsageStatistics
from app.schemas.user import UserCreate, UserUpdate
from app.services.auth import get_password_hash, verify_password


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session, skip: int = 0, limit: int = 100, 
              filter_by: Optional[str] = None, filter_value: Optional[str] = None,
              sort_by: str = "created_at", sort_desc: bool = True) -> List[User]:
    """Get a list of users with filtering and sorting options.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        filter_by: Field to filter by (email, role, is_active, is_verified, subscription.plan)
        filter_value: Value to filter by
        sort_by: Field to sort by (id, email, name, created_at, updated_at)
        sort_desc: Sort in descending order if True, ascending if False
    
    Returns:
        List of User objects
    """
    query = db.query(User)
    
    # Apply filtering if specified
    if filter_by and filter_value:
        if filter_by == "email":
            query = query.filter(User.email.ilike(f"%{filter_value}%"))
        elif filter_by == "name":
            query = query.filter(User.name.ilike(f"%{filter_value}%"))
        elif filter_by == "role":
            query = query.filter(User.role == filter_value)
        elif filter_by == "is_active":
            is_active = filter_value.lower() == "true"
            query = query.filter(User.is_active == is_active)
        elif filter_by == "is_verified":
            is_verified = filter_value.lower() == "true"
            query = query.filter(User.is_verified == is_verified)
        elif filter_by == "subscription.plan":
            query = query.join(User.subscription).filter(Subscription.plan == filter_value)
    
    # Apply sorting
    if sort_by == "email":
        query = query.order_by(User.email.desc() if sort_desc else User.email.asc())
    elif sort_by == "name":
        query = query.order_by(User.name.desc() if sort_desc else User.name.asc())
    elif sort_by == "created_at":
        query = query.order_by(User.created_at.desc() if sort_desc else User.created_at.asc())
    elif sort_by == "updated_at":
        query = query.order_by(User.updated_at.desc() if sort_desc else User.updated_at.asc())
    else:  # Default to id
        query = query.order_by(User.id.desc() if sort_desc else User.id.asc())
    
    # Apply pagination
    return query.offset(skip).limit(limit).all()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Create a new user."""
    # Check if user with this email already exists
    db_user = get_user_by_email(db, email=user_in.email)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user_id = str(uuid.uuid4())
    db_user = User(
        id=user_id,
        email=user_in.email,
        name=user_in.name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(db_user)
    
    # Process subscription information
    subscription_data = user_in.subscription if user_in.subscription else {}
    plan = subscription_data.get('plan', SubscriptionPlan.FREE)
    payment_method_id = subscription_data.get('payment_method_id')
    
    # Set token limit and model tier based on plan
    token_limit = None
    max_model_tier = ModelTier.GPT_3_5_TURBO
    
    if plan == SubscriptionPlan.FREE:
        token_limit = 100000
        max_model_tier = ModelTier.GPT_3_5_TURBO
    elif plan == SubscriptionPlan.BASIC:
        token_limit = 500000
        max_model_tier = ModelTier.GPT_4
    elif plan == SubscriptionPlan.PROFESSIONAL:
        token_limit = None  # Unlimited
        max_model_tier = ModelTier.GPT_4_TURBO
    
    # Create subscription for the user
    db_subscription = Subscription(
        user_id=user_id,
        plan=plan,
        status=SubscriptionStatus.ACTIVE,
        is_active=True,
        auto_renew=plan != SubscriptionPlan.FREE,
        payment_method_id=payment_method_id,
        token_limit=token_limit,
        max_model_tier=max_model_tier
    )
    db.add(db_subscription)
    
    # Create user preferences
    db_preferences = UserPreferences(
        user_id=user_id,
        theme="light",
        notifications=True,
        default_model=max_model_tier
    )
    db.add(db_preferences)
    
    # Create usage statistics
    db_usage = UsageStatistics(
        user_id=user_id,
        tokens_limit=token_limit
    )
    db.add(db_usage)
    
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user: User, user_in: UserUpdate) -> User:
    """Update a user."""
    # Update user fields if provided
    if user_in.email is not None:
        # Check if email is already taken by another user
        existing_user = get_user_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
        user.email = user_in.email
    
    if user_in.name is not None:
        user.name = user_in.name
    
    if user_in.password is not None:
        user.hashed_password = get_password_hash(user_in.password)
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def update_user_status(db: Session, user: User, is_active: Optional[bool] = None, 
                      is_verified: Optional[bool] = None, role: Optional[str] = None) -> User:
    """Update a user's status.
    
    Args:
        db: Database session
        user: User to update
        is_active: Whether the user is active
        is_verified: Whether the user is verified
        role: User role
        
    Returns:
        Updated User object
    """
    # Update user fields if provided
    if is_active is not None:
        user.is_active = is_active
    
    if is_verified is not None:
        user.is_verified = is_verified
    
    if role is not None:
        # Validate role
        if role not in [r.value for r in UserRole]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role: {role}. Must be one of: {', '.join([r.value for r in UserRole])}",
            )
        user.role = role
    
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def verify_user_email(db: Session, user: User) -> User:
    """Mark a user's email as verified."""
    user.is_verified = True
    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user: User) -> bool:
    """Delete a user.
    
    Args:
        db: Database session
        user: User to delete
        
    Returns:
        True if the user was deleted, False otherwise
    """
    try:
        db.delete(user)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user: {e}")
        return False


def update_subscription(
    db: Session, 
    user: User, 
    plan: SubscriptionPlan, 
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE,
    expires_at: Optional[datetime] = None,
    is_active: bool = True,
    auto_renew: bool = False,
    payment_method_id: Optional[str] = None,
    stripe_customer_id: Optional[str] = None,
    stripe_subscription_id: Optional[str] = None
) -> User:
    """Update a user's subscription."""
    # Set token limit and model tier based on plan
    token_limit = None
    max_model_tier = ModelTier.GPT_3_5_TURBO
    
    if plan == SubscriptionPlan.FREE:
        token_limit = 100000
        max_model_tier = ModelTier.GPT_3_5_TURBO
    elif plan == SubscriptionPlan.BASIC:
        token_limit = 500000
        max_model_tier = ModelTier.GPT_4
    elif plan == SubscriptionPlan.PROFESSIONAL:
        token_limit = None  # Unlimited
        max_model_tier = ModelTier.GPT_4_TURBO
    
    if user.subscription:
        # Update existing subscription
        user.subscription.plan = plan
        user.subscription.status = status
        user.subscription.expires_at = expires_at
        user.subscription.is_active = is_active
        user.subscription.auto_renew = auto_renew
        user.subscription.token_limit = token_limit
        user.subscription.max_model_tier = max_model_tier
        user.subscription.updated_at = datetime.utcnow()
        
        # Update payment information if provided
        if payment_method_id:
            user.subscription.payment_method_id = payment_method_id
        if stripe_customer_id:
            user.subscription.stripe_customer_id = stripe_customer_id
        if stripe_subscription_id:
            user.subscription.stripe_subscription_id = stripe_subscription_id
    else:
        # Create new subscription
        db_subscription = Subscription(
            user_id=user.id,
            plan=plan,
            status=status,
            expires_at=expires_at,
            is_active=is_active,
            auto_renew=auto_renew,
            payment_method_id=payment_method_id,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            token_limit=token_limit,
            max_model_tier=max_model_tier
        )
        db.add(db_subscription)
    
    # Update user's usage statistics token limit
    if user.usage_statistics:
        user.usage_statistics.tokens_limit = token_limit
        user.usage_statistics.updated_at = datetime.utcnow()
    else:
        # Create usage statistics if it doesn't exist
        db_usage = UsageStatistics(
            user_id=user.id,
            tokens_limit=token_limit
        )
        db.add(db_usage)
    
    # Update user's default model in preferences if needed
    if user.user_preferences:
        if plan != SubscriptionPlan.FREE:
            user.user_preferences.default_model = max_model_tier
            user.user_preferences.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(user)
    return user
