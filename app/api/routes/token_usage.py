from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Any, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.token_usage import TokenUsageTrack, TokenUsageHistory, TokenUsageStatistics
from app.services.token_usage import track_token_usage, get_token_usage_history, get_token_usage_statistics
from app.services.auth import get_current_user, get_current_active_verified_user
from app.services.admin import verify_admin_token

router = APIRouter()


@router.get("/me", response_model=TokenUsageStatistics)
def read_token_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user's token usage statistics.
    """
    return get_token_usage_statistics(db, current_user.id)


@router.get("/me/summary", response_model=TokenUsageStatistics)
def read_token_usage_summary(
    period: Optional[str] = Query(None, description="Aggregate period: week|month|quarter (currently defaults to month)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Phase 2 stub: Get current user's token usage summary for a period.
    Currently returns the same structure as /me (monthly), while preserving
    the API contract to expand later without breaking the client.
    """
    # Honor period in services (week/month/quarter)
    return get_token_usage_statistics(db, current_user.id, period)


@router.get("/me/by-conversation")
def read_token_usage_by_conversation(
    conversation_id: str = Query(..., description="Conversation ID to fetch usage for"),
    limit: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Per-conversation usage (Phase 2). Returns totals and recent events.
    """
    from app.services.token_usage import get_token_usage_by_conversation
    return get_token_usage_by_conversation(db, current_user.id, conversation_id, limit)


@router.get("/me/history", response_model=TokenUsageHistory)
def read_token_usage_history(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user's token usage history with pagination.
    """
    # Parse dates if provided
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DD)."
            )
    
    if end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date)
            # Set end_date to end of day
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DD)."
            )
    
    return get_token_usage_history(
        db, 
        current_user.id, 
        start_date=start_date_obj, 
        end_date=end_date_obj,
        page=page,
        limit=limit
    )


@router.post("/me/track")
def track_user_token_usage(
    token_usage_in: TokenUsageTrack,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Track token usage for current user.
    """
    # Check if user has access to the specified model based on subscription
    if current_user.subscription and current_user.subscription.max_model_tier:
        requested_model = token_usage_in.model
        allowed_model = current_user.subscription.max_model_tier
        
        # Simple model tier check (this could be more sophisticated)
        if requested_model != allowed_model and requested_model == "gpt-4-turbo" and allowed_model != "gpt-4-turbo":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Your subscription does not allow access to {requested_model}. Please upgrade your plan."
            )
    
    # Check if user has exceeded their token limit
    if current_user.subscription and current_user.subscription.token_limit:
        if current_user.usage_statistics and current_user.usage_statistics.tokens_used >= current_user.subscription.token_limit:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You have reached your token usage limit for this billing period. Please upgrade your plan."
            )
    
    # Track token usage
    token_usage = track_token_usage(db, current_user.id, token_usage_in)
    
    return {
        "success": True,
        "message": "Token usage tracked successfully",
        "id": token_usage.id
    }


@router.get("/admin/usage", dependencies=[Depends(verify_admin_token)])
def admin_token_usage(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    group_by: str = Query("day", regex="^(user|day|model|request_type)$"),
    db: Session = Depends(get_db)
) -> Any:
    """
    Admin endpoint to retrieve token usage across all users.
    """
    # Parse dates if provided
    start_date_obj = None
    end_date_obj = None
    
    if start_date:
        try:
            start_date_obj = datetime.fromisoformat(start_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_date format. Use ISO format (YYYY-MM-DD)."
            )
    else:
        # Default to last 30 days
        start_date_obj = datetime.utcnow() - timedelta(days=30)
    
    if end_date:
        try:
            end_date_obj = datetime.fromisoformat(end_date)
            # Set end_date to end of day
            end_date_obj = end_date_obj.replace(hour=23, minute=59, second=59)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_date format. Use ISO format (YYYY-MM-DD)."
            )
    else:
        # Default to today
        end_date_obj = datetime.utcnow()
    
    # Get token usage statistics grouped by the specified dimension
    from app.models.token_usage import TokenUsage, TokenUsageSummary
    from sqlalchemy import func
    
    # Base query for total tokens
    total_tokens_query = db.query(
        func.sum(TokenUsage.total_tokens).label("total_tokens"),
        func.sum(TokenUsage.prompt_tokens).label("prompt_tokens"),
        func.sum(TokenUsage.completion_tokens).label("completion_tokens")
    ).filter(
        TokenUsage.timestamp >= start_date_obj,
        TokenUsage.timestamp <= end_date_obj
    )
    
    totals = total_tokens_query.first()
    
    # Group by the specified dimension
    if group_by == "day":
        # Group by day
        daily_data = db.query(
            func.date(TokenUsage.timestamp).label("date"),
            func.sum(TokenUsage.total_tokens).label("total_tokens")
        ).filter(
            TokenUsage.timestamp >= start_date_obj,
            TokenUsage.timestamp <= end_date_obj
        ).group_by(
            func.date(TokenUsage.timestamp)
        ).order_by(
            func.date(TokenUsage.timestamp)
        ).all()
        
        breakdown_by_day = [
            {"date": str(date), "total_tokens": total_tokens}
            for date, total_tokens in daily_data
        ]
        
        # Group by model
        model_data = db.query(
            TokenUsage.model,
            func.sum(TokenUsage.total_tokens).label("total_tokens")
        ).filter(
            TokenUsage.timestamp >= start_date_obj,
            TokenUsage.timestamp <= end_date_obj
        ).group_by(
            TokenUsage.model
        ).all()
        
        breakdown_by_model = {
            model: total_tokens
            for model, total_tokens in model_data
        }
        
        # Group by request type
        request_type_data = db.query(
            TokenUsage.request_type,
            func.sum(TokenUsage.total_tokens).label("total_tokens")
        ).filter(
            TokenUsage.timestamp >= start_date_obj,
            TokenUsage.timestamp <= end_date_obj
        ).group_by(
            TokenUsage.request_type
        ).all()
        
        breakdown_by_request_type = {
            str(request_type): total_tokens
            for request_type, total_tokens in request_type_data
        }
        
        # Count active users
        active_users = db.query(TokenUsage.user_id).filter(
            TokenUsage.timestamp >= start_date_obj,
            TokenUsage.timestamp <= end_date_obj
        ).distinct().count()
        
        # Calculate average tokens per user
        avg_tokens_per_user = totals.total_tokens / active_users if active_users > 0 else 0
        
        return {
            "total_tokens": totals.total_tokens or 0,
            "prompt_tokens": totals.prompt_tokens or 0,
            "completion_tokens": totals.completion_tokens or 0,
            "breakdown_by_day": breakdown_by_day,
            "breakdown_by_model": breakdown_by_model,
            "breakdown_by_request_type": breakdown_by_request_type,
            "active_users": active_users,
            "average_tokens_per_user": avg_tokens_per_user
        }
    
    elif group_by == "user":
        # Group by user
        user_data = db.query(
            TokenUsage.user_id,
            User.email,
            User.name,
            func.sum(TokenUsage.total_tokens).label("total_tokens")
        ).join(
            User, User.id == TokenUsage.user_id
        ).filter(
            TokenUsage.timestamp >= start_date_obj,
            TokenUsage.timestamp <= end_date_obj
        ).group_by(
            TokenUsage.user_id,
            User.email,
            User.name
        ).order_by(
            func.sum(TokenUsage.total_tokens).desc()
        ).all()
        
        breakdown_by_user = [
            {
                "user_id": user_id,
                "email": email,
                "name": name,
                "total_tokens": total_tokens
            }
            for user_id, email, name, total_tokens in user_data
        ]
        
        return {
            "total_tokens": totals.total_tokens or 0,
            "prompt_tokens": totals.prompt_tokens or 0,
            "completion_tokens": totals.completion_tokens or 0,
            "breakdown_by_user": breakdown_by_user,
            "active_users": len(breakdown_by_user)
        }
    
    elif group_by == "model":
        # Group by model
        model_data = db.query(
            TokenUsage.model,
            func.sum(TokenUsage.total_tokens).label("total_tokens"),
            func.sum(TokenUsage.prompt_tokens).label("prompt_tokens"),
            func.sum(TokenUsage.completion_tokens).label("completion_tokens"),
            func.count(TokenUsage.id).label("request_count")
        ).filter(
            TokenUsage.timestamp >= start_date_obj,
            TokenUsage.timestamp <= end_date_obj
        ).group_by(
            TokenUsage.model
        ).order_by(
            func.sum(TokenUsage.total_tokens).desc()
        ).all()
        
        breakdown_by_model = [
            {
                "model": model,
                "total_tokens": total_tokens,
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "request_count": request_count
            }
            for model, total_tokens, prompt_tokens, completion_tokens, request_count in model_data
        ]
        
        return {
            "total_tokens": totals.total_tokens or 0,
            "prompt_tokens": totals.prompt_tokens or 0,
            "completion_tokens": totals.completion_tokens or 0,
            "breakdown_by_model": breakdown_by_model
        }
    
    elif group_by == "request_type":
        # Group by request type
        request_type_data = db.query(
            TokenUsage.request_type,
            func.sum(TokenUsage.total_tokens).label("total_tokens"),
            func.count(TokenUsage.id).label("request_count")
        ).filter(
            TokenUsage.timestamp >= start_date_obj,
            TokenUsage.timestamp <= end_date_obj
        ).group_by(
            TokenUsage.request_type
        ).order_by(
            func.sum(TokenUsage.total_tokens).desc()
        ).all()
        
        breakdown_by_request_type = [
            {
                "request_type": str(request_type),
                "total_tokens": total_tokens,
                "request_count": request_count
            }
            for request_type, total_tokens, request_count in request_type_data
        ]
        
        return {
            "total_tokens": totals.total_tokens or 0,
            "prompt_tokens": totals.prompt_tokens or 0,
            "completion_tokens": totals.completion_tokens or 0,
            "breakdown_by_request_type": breakdown_by_request_type
        }
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid group_by parameter. Must be one of: user, day, model, request_type"
        )
