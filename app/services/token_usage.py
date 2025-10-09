from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, status
from app.models.token_usage import TokenUsage, TokenUsageSummary, RequestType
from app.models.user import User, ModelTier
from app.schemas.token_usage import TokenUsageCreate, TokenUsageTrack


def create_token_usage(db: Session, token_usage_in: TokenUsageCreate) -> TokenUsage:
    """
    Create a new token usage record.
    """
    db_token_usage = TokenUsage(
        user_id=token_usage_in.user_id,
        request_type=token_usage_in.request_type,
        model=token_usage_in.model,
        prompt_tokens=token_usage_in.prompt_tokens,
        completion_tokens=token_usage_in.completion_tokens,
        total_tokens=token_usage_in.total_tokens,
        request_id=token_usage_in.request_id
    )
    db.add(db_token_usage)
    db.commit()
    db.refresh(db_token_usage)
    
    # Update token usage summary
    update_token_usage_summary(db, db_token_usage)
    
    # Update user's usage statistics
    update_user_usage_statistics(db, db_token_usage.user_id, db_token_usage.total_tokens)
    
    return db_token_usage


def update_token_usage_summary(db: Session, token_usage: TokenUsage) -> None:
    """
    Update or create token usage summary for the day.
    """
    today = token_usage.timestamp
    year = today.year
    month = today.month
    day = today.day
    
    # Try to get existing summary for this day
    summary = db.query(TokenUsageSummary).filter(
        TokenUsageSummary.user_id == token_usage.user_id,
        TokenUsageSummary.year == year,
        TokenUsageSummary.month == month,
        TokenUsageSummary.day == day
    ).first()
    
    if not summary:
        # Create new summary
        summary = TokenUsageSummary(
            user_id=token_usage.user_id,
            year=year,
            month=month,
            day=day,
            chat_prompt_tokens=0,
            chat_completion_tokens=0,
            chat_total_tokens=0,
            plagiarism_tokens=0,
            prompt_generation_tokens=0,
            total_tokens=0
        )
        db.add(summary)
    
    # Update the appropriate fields based on request type
    if token_usage.request_type == RequestType.CHAT:
        summary.chat_prompt_tokens += token_usage.prompt_tokens
        summary.chat_completion_tokens += token_usage.completion_tokens
        summary.chat_total_tokens += token_usage.total_tokens
    elif token_usage.request_type == RequestType.PLAGIARISM:
        summary.plagiarism_tokens += token_usage.total_tokens
    elif token_usage.request_type == RequestType.PROMPT:
        summary.prompt_generation_tokens += token_usage.total_tokens
    
    summary.total_tokens += token_usage.total_tokens
    summary.updated_at = datetime.utcnow()
    
    db.commit()


def update_user_usage_statistics(db: Session, user_id: str, tokens: int) -> None:
    """
    Update user's usage statistics with token count.
    """
    from app.models.usage_statistics import UsageStatistics
    
    # Get or create usage statistics for user
    stats = db.query(UsageStatistics).filter(UsageStatistics.user_id == user_id).first()
    if not stats:
        stats = UsageStatistics(user_id=user_id)
        db.add(stats)
    
    # Update tokens used
    if stats.tokens_used is None:
        stats.tokens_used = tokens
    else:
        stats.tokens_used += tokens
    
    stats.updated_at = datetime.utcnow()
    
    db.commit()


def get_token_usage_history(
    db: Session, 
    user_id: str, 
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    page: int = 1,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Get token usage history for a user with pagination.
    """
    query = db.query(TokenUsage).filter(TokenUsage.user_id == user_id)
    
    if start_date:
        query = query.filter(TokenUsage.timestamp >= start_date)
    
    if end_date:
        query = query.filter(TokenUsage.timestamp <= end_date)
    
    # Count total records for pagination
    total_records = query.count()
    total_pages = (total_records + limit - 1) // limit if total_records > 0 else 1
    
    # Apply pagination
    records = query.order_by(TokenUsage.timestamp.desc()).offset((page - 1) * limit).limit(limit).all()
    
    return {
        "total_records": total_records,
        "total_pages": total_pages,
        "current_page": page,
        "records_per_page": limit,
        "history": records
    }


def get_token_usage_statistics(db: Session, user_id: str) -> Dict[str, Any]:
    """
    Get token usage statistics for a user.
    """
    from sqlalchemy import func
    
    # Get user subscription to determine token limit
    user = db.query(User).filter(User.id == user_id).first()
    token_limit = user.subscription.token_limit if user and user.subscription else None
    
    # Get current billing period (assume monthly for now)
    today = datetime.utcnow()
    start_of_month = datetime(today.year, today.month, 1)
    if today.month == 12:
        end_of_month = datetime(today.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(days=1)
    
    # Get total tokens used in current period
    current_period_usage = db.query(TokenUsageSummary).filter(
        TokenUsageSummary.user_id == user_id,
        TokenUsageSummary.year == today.year,
        TokenUsageSummary.month == today.month
    ).all()
    
    tokens_used = sum(summary.total_tokens for summary in current_period_usage) if current_period_usage else 0
    
    # Calculate breakdown by type
    chat_tokens = sum(summary.chat_total_tokens for summary in current_period_usage) if current_period_usage else 0
    chat_prompt_tokens = sum(summary.chat_prompt_tokens for summary in current_period_usage) if current_period_usage else 0
    chat_completion_tokens = sum(summary.chat_completion_tokens for summary in current_period_usage) if current_period_usage else 0
    plagiarism_tokens = sum(summary.plagiarism_tokens for summary in current_period_usage) if current_period_usage else 0
    prompt_generation_tokens = sum(summary.prompt_generation_tokens for summary in current_period_usage) if current_period_usage else 0
    
    # Get breakdown by model
    model_breakdown = {}
    model_usage = db.query(TokenUsage.model, func.sum(TokenUsage.total_tokens).label('total')).filter(
        TokenUsage.user_id == user_id,
        TokenUsage.timestamp >= start_of_month,
        TokenUsage.timestamp <= end_of_month
    ).group_by(TokenUsage.model).all()
    
    for model, total in model_usage:
        model_breakdown[model] = total
    
    # Get daily usage for the last 30 days
    daily_usage = []
    end_date = today
    start_date = end_date - timedelta(days=30)
    
    # Simplified approach for SQLite
    # Just get all summaries and filter in Python
    summaries = db.query(TokenUsageSummary).filter(
        TokenUsageSummary.user_id == user_id
    ).all()
    
    # Group by date in Python
    date_totals = {}
    for summary in summaries:
        date_str = f"{summary.year:04d}-{summary.month:02d}-{summary.day:02d}"
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        if start_date.date() <= date_obj <= end_date.date():
            if date_str not in date_totals:
                date_totals[date_str] = 0
            date_totals[date_str] += summary.total_tokens
    
    # Convert to list format for daily usage
    for date_str, total in date_totals.items():
        daily_usage.append({"date": date_str, "total_tokens": total})
    
    # Sort daily usage by date
    daily_usage.sort(key=lambda x: x["date"])
    
    return {
        "current_period": {
            "start_date": start_of_month.isoformat(),
            "end_date": end_of_month.isoformat(),
            "tokens_used": tokens_used,
            "tokens_limit": token_limit,
            "percentage_used": (tokens_used / token_limit * 100) if token_limit else None
        },
        "breakdown": {
            "chat": {
                "prompt_tokens": chat_prompt_tokens,
                "completion_tokens": chat_completion_tokens,
                "total_tokens": chat_tokens
            },
            "plagiarism": {
                "total_tokens": plagiarism_tokens
            },
            "prompt_generation": {
                "total_tokens": prompt_generation_tokens
            }
        },
        "models": model_breakdown,
        "daily_usage": daily_usage
    }


def record_token_usage(db: Session, user_id: str, token_usage_in: TokenUsageTrack) -> TokenUsage:
    """
    Record token usage for a user. Alias for track_token_usage.
    """
    return track_token_usage(db, user_id, token_usage_in)


def track_token_usage(db: Session, user_id: str, token_usage_in: TokenUsageTrack) -> TokenUsage:
    """
    Track token usage for a user.
    """
    # Convert UUID to string if it's a UUID object
    if hasattr(user_id, 'hex'):
        user_id = str(user_id)
    
    token_usage_create = TokenUsageCreate(
        user_id=user_id,
        request_type=token_usage_in.request_type,
        model=token_usage_in.model,
        prompt_tokens=token_usage_in.prompt_tokens,
        completion_tokens=token_usage_in.completion_tokens,
        total_tokens=token_usage_in.total_tokens,
        request_id=token_usage_in.request_id
    )
    
    return create_token_usage(db, token_usage_create)


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
