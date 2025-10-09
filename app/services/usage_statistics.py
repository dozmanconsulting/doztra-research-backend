from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.usage_statistics import UsageStatistics
from app.schemas.usage_statistics import UsageStatisticsCreate, UsageStatisticsUpdate


def get_usage_statistics(db: Session, user_id: str) -> Optional[UsageStatistics]:
    """
    Get user usage statistics.
    """
    return db.query(UsageStatistics).filter(UsageStatistics.user_id == user_id).first()


def create_usage_statistics(db: Session, stats_in: UsageStatisticsCreate) -> UsageStatistics:
    """
    Create new usage statistics.
    """
    db_stats = UsageStatistics(
        user_id=stats_in.user_id,
        chat_messages=stats_in.chat_messages,
        plagiarism_checks=stats_in.plagiarism_checks,
        prompts_generated=stats_in.prompts_generated,
        tokens_used=stats_in.tokens_used,
        tokens_limit=stats_in.tokens_limit
    )
    db.add(db_stats)
    db.commit()
    db.refresh(db_stats)
    return db_stats


def update_usage_statistics(db: Session, user_id: str, stats_in: UsageStatisticsUpdate) -> Optional[UsageStatistics]:
    """
    Update usage statistics.
    """
    db_stats = get_usage_statistics(db, user_id)
    if not db_stats:
        # Create stats if they don't exist
        return create_usage_statistics(db, UsageStatisticsCreate(
            user_id=user_id,
            **stats_in.dict(exclude_unset=True)
        ))
    
    # Update stats
    update_data = stats_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            current_value = getattr(db_stats, field)
            if field in ['chat_messages', 'plagiarism_checks', 'prompts_generated', 'tokens_used']:
                # Increment these fields
                setattr(db_stats, field, current_value + value)
            else:
                # Set other fields directly
                setattr(db_stats, field, value)
    
    db_stats.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_stats)
    return db_stats


def get_usage_response(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get formatted usage statistics response.
    """
    # Get user's usage statistics
    stats = get_usage_statistics(db, user_id)
    if not stats:
        stats = create_usage_statistics(db, UsageStatisticsCreate(user_id=user_id))
    
    # Get user's subscription for limits
    from app.models.user import User
    user = db.query(User).filter(User.id == user_id).first()
    
    # Determine limits based on subscription plan
    chat_limit = None
    plagiarism_limit = None
    prompts_limit = None
    tokens_limit = None
    
    if user and user.subscription:
        # These would typically come from a plan configuration
        if user.subscription.plan == "free":
            chat_limit = 150
            plagiarism_limit = 5
            prompts_limit = 5
            tokens_limit = 100000
        elif user.subscription.plan == "basic":
            chat_limit = 1500
            plagiarism_limit = 50
            prompts_limit = 50
            tokens_limit = 500000
        elif user.subscription.plan == "professional":
            chat_limit = None  # Unlimited
            plagiarism_limit = None  # Unlimited
            prompts_limit = None  # Unlimited
            tokens_limit = None  # Unlimited
    
    # Calculate next reset date (first day of next month)
    today = datetime.utcnow()
    if today.month == 12:
        reset_date = datetime(today.year + 1, 1, 1)
    else:
        reset_date = datetime(today.year, today.month + 1, 1)
    
    return {
        "chat_messages": {
            "used": stats.chat_messages,
            "limit": chat_limit,
            "reset_date": reset_date.isoformat()
        },
        "plagiarism_checks": {
            "used": stats.plagiarism_checks,
            "limit": plagiarism_limit,
            "reset_date": reset_date.isoformat()
        },
        "prompts_generated": {
            "used": stats.prompts_generated,
            "limit": prompts_limit,
            "reset_date": reset_date.isoformat()
        },
        "tokens": {
            "used": stats.tokens_used,
            "limit": tokens_limit,
            "reset_date": reset_date.isoformat()
        }
    }
