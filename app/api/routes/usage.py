from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import date

from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User, SubscriptionPlan
from app.services.usage import PLAN_LIMITS, _ensure_usage_row

router = APIRouter()

@router.get("/usage/remaining")
async def get_remaining_usage(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        raw_plan = (current_user.subscription.plan if current_user.subscription else SubscriptionPlan.FREE)
        # Accept both enum and string values safely
        if isinstance(raw_plan, SubscriptionPlan):
            plan_key = raw_plan.value
        else:
            plan_key = str(raw_plan).lower()
        limits = PLAN_LIMITS.get(plan_key, PLAN_LIMITS["free"])  # default to free

        usage = _ensure_usage_row(db, current_user.id)

        # Reset windows if needed (non-destructive if same day/month)
        today = date.today()
        first_of_month = today.replace(day=1)
        if usage.day_anchor != today:
            usage.day_anchor = today
            usage.day_tokens_used = 0
        if usage.month_anchor != first_of_month:
            usage.month_anchor = first_of_month
            usage.month_tokens_used = 0
        db.add(usage)
        db.commit()

        if plan_key == SubscriptionPlan.FREE.value or plan_key == "free":
            window = "day"
            cap = limits.get("day_limit", 0)
            plan_used = usage.day_tokens_used or 0
        else:
            window = "month"
            cap = limits.get("month_limit", 0)
            plan_used = usage.month_tokens_used or 0

        plan_remaining = max(0, cap - plan_used)
        bonus_remaining = usage.bonus_tokens_remaining or 0

        return {
            "plan": plan_key,
            "window": window,
            "plan_cap": cap,
            "plan_used": plan_used,
            "plan_remaining": plan_remaining,
            "bonus_remaining": bonus_remaining,
            "total_available": plan_remaining + bonus_remaining,
        }
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
