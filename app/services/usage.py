from datetime import date
from typing import Tuple
from sqlalchemy.orm import Session

from app.models.user import User, SubscriptionPlan

# Simple config; consider moving to database/config
PLAN_LIMITS = {
    "free": {"day_limit": 500, "max_in": 2000, "max_out": 500},
    "basic": {"month_limit": 500_000, "max_in": 8000, "max_out": 1500},
    "professional": {"month_limit": 2_000_000, "max_in": 16000, "max_out": 3000},
}

# SQLAlchemy model stubs; replace with your actual models if needed
from sqlalchemy import Column, Date, BigInteger, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class UserUsage(Base):
    __tablename__ = "user_usage"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    day_tokens_used = Column(BigInteger, nullable=False)
    day_anchor = Column(Date, nullable=False)
    month_tokens_used = Column(BigInteger, nullable=False)
    month_anchor = Column(Date, nullable=False)
    bonus_tokens_remaining = Column(BigInteger, nullable=False)
    updated_at = Column(TIMESTAMP(timezone=True), nullable=False)


def _get_limits(plan: SubscriptionPlan):
    return PLAN_LIMITS.get(plan.value, PLAN_LIMITS["free"])  # default safe


def _ensure_usage_row(db: Session, user_id) -> UserUsage:
    usage = db.query(UserUsage).get(user_id)
    if not usage:
        usage = UserUsage(
            user_id=user_id,
            day_tokens_used=0,
            day_anchor=date.today(),
            month_tokens_used=0,
            month_anchor=date.today().replace(day=1),
            bonus_tokens_remaining=0,
        )
        db.add(usage)
        db.commit()
        db.refresh(usage)
    return usage


def estimate_tokens(prompt: str) -> int:
    # Lightweight estimate without tokenizer; replace with tiktoken for accuracy
    if not prompt:
        return 0
    # heuristic: ~4 chars per token
    return max(1, len(prompt) // 4)


def before_llm_check(db: Session, user: User, planned_out: int, prompt: str) -> Tuple[int, int, int, UserUsage]:
    """
    Returns: (clamped_out_tokens, est_total, plan_remaining, usage_row)
    Raises: HTTPException (handled by route) — leave raising to caller if desired
    """
    limits = _get_limits(user.subscription.plan if user.subscription else SubscriptionPlan.FREE)

    usage = _ensure_usage_row(db, user.id)

    # Reset windows if needed
    today = date.today()
    first_of_month = today.replace(day=1)
    if usage.day_anchor != today:
        usage.day_anchor = today
        usage.day_tokens_used = 0
    if usage.month_anchor != first_of_month:
        usage.month_anchor = first_of_month
        usage.month_tokens_used = 0

    est_in = estimate_tokens(prompt)
    clamped_out = min(max(0, planned_out), limits.get("max_out", planned_out))
    est_total = est_in + clamped_out

    # Remaining plan tokens
    if (user.subscription and user.subscription.plan == SubscriptionPlan.FREE) or not user.subscription:
        plan_remaining = max(0, limits.get("day_limit", 0) - (usage.day_tokens_used or 0))
    else:
        plan_remaining = max(0, limits.get("month_limit", 0) - (usage.month_tokens_used or 0))

    return clamped_out, est_total, plan_remaining, usage


def after_llm_update(db: Session, user: User, usage: UserUsage, actual_in: int, actual_out: int) -> None:
    total = max(0, (actual_in or 0) + (actual_out or 0))
    if total == 0:
        return

    limits = _get_limits(user.subscription.plan if user.subscription else SubscriptionPlan.FREE)

    # Consume plan first, then bonus
    if (user.subscription and user.subscription.plan == SubscriptionPlan.FREE) or not user.subscription:
        cap = limits.get("day_limit", 0)
        room = max(0, cap - (usage.day_tokens_used or 0))
        consume_plan = min(room, total)
        usage.day_tokens_used = (usage.day_tokens_used or 0) + consume_plan
    else:
        cap = limits.get("month_limit", 0)
        room = max(0, cap - (usage.month_tokens_used or 0))
        consume_plan = min(room, total)
        usage.month_tokens_used = (usage.month_tokens_used or 0) + consume_plan

    leftover = total - consume_plan
    if leftover > 0:
        usage.bonus_tokens_remaining = max(0, (usage.bonus_tokens_remaining or 0) - leftover)

    db.add(usage)
    db.commit()
