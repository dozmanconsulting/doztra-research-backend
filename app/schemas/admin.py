from pydantic import BaseModel
from typing import Dict, List, Optional


class UserStatistics(BaseModel):
    """Schema for user statistics."""
    total_users: int
    active_users: int
    verified_users: int
    subscription_distribution: Dict[str, int]
    registration_by_month: Dict[str, int]
    active_users_last_30_days: int
    user_growth_rate: Optional[float] = None


class AdminDashboardStats(BaseModel):
    """Schema for admin dashboard statistics."""
    user_statistics: UserStatistics
    token_usage_total: int
    token_usage_by_plan: Dict[str, int]
    token_usage_by_model: Dict[str, int]
    token_usage_by_day: Dict[str, int]
