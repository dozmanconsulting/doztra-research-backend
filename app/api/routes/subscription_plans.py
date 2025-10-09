from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any, List, Dict

from app.db.session import get_db
from app.models.user import SubscriptionPlan, ModelTier
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/plans")
def get_subscription_plans() -> Any:
    """
    Get all available subscription plans with their details.
    """
    plans = {
        "free": {
            "name": "Free Plan",
            "price": 0,
            "token_limit": 100000,
            "models": [ModelTier.GPT_3_5_TURBO.value],
            "features": [
                "Basic AI chat",
                "Limited plagiarism checks",
                "Standard support"
            ]
        },
        "basic": {
            "name": "Basic Plan",
            "price": 19,
            "billing_cycle": "monthly",
            "token_limit": 500000,
            "models": [ModelTier.GPT_3_5_TURBO.value, ModelTier.GPT_4.value],
            "features": [
                "Advanced AI chat",
                "Full plagiarism detection",
                "Prompt generation",
                "Standard support"
            ]
        },
        "professional": {
            "name": "Professional Plan",
            "price": 49,
            "billing_cycle": "monthly",
            "token_limit": None,  # Unlimited
            "models": [ModelTier.GPT_3_5_TURBO.value, ModelTier.GPT_4.value, ModelTier.GPT_4_TURBO.value],
            "features": [
                "Advanced AI chat",
                "Full plagiarism detection",
                "Advanced prompt generation",
                "Priority support",
                "API access"
            ]
        }
    }
    
    return plans


@router.get("/compare")
def compare_subscription_plans(current_plan: str = None) -> Any:
    """
    Compare subscription plans, highlighting the current plan if specified.
    """
    # Get all plans
    plans = get_subscription_plans()
    
    # Add comparison data
    comparison = []
    
    for plan_id, plan_data in plans.items():
        plan_info = {
            "id": plan_id,
            "name": plan_data["name"],
            "price": plan_data["price"],
            "is_current": plan_id == current_plan,
            "features": plan_data["features"],
            "token_limit": "Unlimited" if plan_data.get("token_limit") is None else f"{plan_data.get('token_limit'):,}",
            "models": plan_data["models"]
        }
        comparison.append(plan_info)
    
    return comparison


@router.get("/me/eligible-upgrades")
def get_eligible_upgrades(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Any:
    """
    Get eligible plan upgrades for the current user.
    """
    current_plan = current_user.subscription.plan if current_user.subscription else SubscriptionPlan.FREE
    
    # Define upgrade paths
    eligible_upgrades = []
    
    if current_plan == SubscriptionPlan.FREE:
        eligible_upgrades = ["basic", "professional"]
    elif current_plan == SubscriptionPlan.BASIC:
        eligible_upgrades = ["professional"]
    # Professional users don't have upgrade options
    
    # Get details for eligible plans
    plans = get_subscription_plans()
    upgrade_details = [
        {**plans[plan], "id": plan}
        for plan in eligible_upgrades
    ]
    
    return {
        "current_plan": {**plans[current_plan], "id": current_plan},
        "eligible_upgrades": upgrade_details
    }
