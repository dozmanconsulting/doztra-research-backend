from sqlalchemy import func, extract, and_, or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.user import User, Subscription, SubscriptionPlan
from app.models.token_usage import TokenUsage, TokenUsageSummary
from app.schemas.admin import UserStatistics, AdminDashboardStats


def get_user_statistics(db: Session) -> UserStatistics:
    """
    Get user statistics.
    
    Args:
        db: Database session
        
    Returns:
        UserStatistics object with user statistics
    """
    # Get total users
    total_users = db.query(func.count(User.id)).scalar()
    
    # Get active users
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # Get verified users
    verified_users = db.query(func.count(User.id)).filter(User.is_verified == True).scalar()
    
    # Get subscription distribution
    subscription_distribution = {}
    for plan in SubscriptionPlan:
        count = db.query(func.count(Subscription.id)).filter(
            Subscription.plan == plan,
            Subscription.is_active == True
        ).scalar()
        subscription_distribution[plan.value] = count
    
    # Get registration by month for the last 12 months
    now = datetime.utcnow()
    registration_by_month = {}
    
    for i in range(12):
        month_date = now - timedelta(days=30 * i)
        month_key = month_date.strftime("%Y-%m")
        
        count = db.query(func.count(User.id)).filter(
            extract('year', User.created_at) == month_date.year,
            extract('month', User.created_at) == month_date.month
        ).scalar()
        
        registration_by_month[month_key] = count
    
    # Get active users in the last 30 days (users who have logged in)
    thirty_days_ago = now - timedelta(days=30)
    active_users_last_30_days = db.query(func.count(User.id)).filter(
        User.updated_at >= thirty_days_ago
    ).scalar()
    
    # Calculate user growth rate (compared to previous month)
    current_month = now.month
    current_year = now.year
    
    previous_month = current_month - 1 if current_month > 1 else 12
    previous_year = current_year if current_month > 1 else current_year - 1
    
    users_current_month = db.query(func.count(User.id)).filter(
        extract('year', User.created_at) == current_year,
        extract('month', User.created_at) == current_month
    ).scalar()
    
    users_previous_month = db.query(func.count(User.id)).filter(
        extract('year', User.created_at) == previous_year,
        extract('month', User.created_at) == previous_month
    ).scalar()
    
    # Calculate growth rate
    user_growth_rate = None
    if users_previous_month > 0:
        user_growth_rate = (users_current_month - users_previous_month) / users_previous_month * 100
    
    return UserStatistics(
        total_users=total_users,
        active_users=active_users,
        verified_users=verified_users,
        subscription_distribution=subscription_distribution,
        registration_by_month=registration_by_month,
        active_users_last_30_days=active_users_last_30_days,
        user_growth_rate=user_growth_rate
    )


def get_token_usage_statistics(db: Session) -> Dict:
    """
    Get token usage statistics.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with token usage statistics
    """
    # Get total token usage
    token_usage_total = db.query(func.sum(TokenUsage.total_tokens)).scalar() or 0
    
    # Get token usage by plan
    token_usage_by_plan = {}
    for plan in SubscriptionPlan:
        usage = db.query(func.sum(TokenUsage.total_tokens)).join(
            User, User.id == TokenUsage.user_id
        ).join(
            Subscription, Subscription.user_id == User.id
        ).filter(
            Subscription.plan == plan
        ).scalar() or 0
        
        token_usage_by_plan[plan.value] = usage
    
    # Get token usage by model
    token_usage_by_model_query = db.query(
        TokenUsage.model,
        func.sum(TokenUsage.total_tokens).label('total')
    ).group_by(TokenUsage.model).all()
    
    token_usage_by_model = {model: total for model, total in token_usage_by_model_query}
    
    # Get token usage by day for the last 30 days
    now = datetime.utcnow()
    token_usage_by_day = {}
    
    for i in range(30):
        day_date = now - timedelta(days=i)
        day_key = day_date.strftime("%Y-%m-%d")
        
        usage = db.query(func.sum(TokenUsage.total_tokens)).filter(
            func.date(TokenUsage.timestamp) == day_date.date()
        ).scalar() or 0
        
        token_usage_by_day[day_key] = usage
    
    return {
        "token_usage_total": token_usage_total,
        "token_usage_by_plan": token_usage_by_plan,
        "token_usage_by_model": token_usage_by_model,
        "token_usage_by_day": token_usage_by_day
    }


def get_admin_dashboard_stats(db: Session) -> AdminDashboardStats:
    """
    Get admin dashboard statistics.
    
    Args:
        db: Database session
        
    Returns:
        AdminDashboardStats object with admin dashboard statistics
    """
    user_statistics = get_user_statistics(db)
    token_usage_statistics = get_token_usage_statistics(db)
    
    return AdminDashboardStats(
        user_statistics=user_statistics,
        **token_usage_statistics
    )
