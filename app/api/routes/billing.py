from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
import logging
import stripe
from typing import Any, Dict

from app.core.config import settings
from app.db.session import get_db
from app.services.auth import get_current_user
from app.models.user import User, SubscriptionPlan, SubscriptionStatus
from app.services.user import update_subscription

router = APIRouter()

logger = logging.getLogger(__name__)


def _require_env(var_name: str) -> str:
    value = getattr(settings, var_name, None)
    if not value:
        raise HTTPException(status_code=500, detail=f"Missing configuration: {var_name}")
    return value


@router.post("/billing/create-checkout-session")
def create_checkout_session(payload: Dict[str, Any], db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a Stripe Checkout session for a subscription plan."""
    plan = payload.get("plan")
    if plan not in ("basic", "professional"):
        raise HTTPException(status_code=422, detail="Invalid plan. Must be 'basic' or 'professional'")
    billing_period = payload.get("billing_period", "monthly")
    if billing_period not in ("monthly", "yearly"):
        raise HTTPException(status_code=422, detail="Invalid billing_period. Must be 'monthly' or 'yearly'")

    secret_key = _require_env("STRIPE_SECRET_KEY")
    price_basic = _require_env("STRIPE_PRICE_BASIC")
    price_pro = _require_env("STRIPE_PRICE_PRO")
    price_basic_yearly = getattr(settings, "STRIPE_PRICE_BASIC_YEARLY", None)
    price_pro_yearly = getattr(settings, "STRIPE_PRICE_PRO_YEARLY", None)
    success_url = _require_env("STRIPE_SUCCESS_URL")
    cancel_url = _require_env("STRIPE_CANCEL_URL")

    stripe.api_key = secret_key

    try:
        # Reuse or create a Stripe customer
        customer_id = None
        if current_user.subscription and current_user.subscription.stripe_customer_id:
            customer_id = current_user.subscription.stripe_customer_id
        else:
            customer = stripe.Customer.create(
                email=current_user.email,
                name=current_user.name,
                metadata={"user_id": current_user.id}
            )
            customer_id = customer.id

        if billing_period == "yearly":
            if plan == "basic" and price_basic_yearly:
                price_id = price_basic_yearly
            elif plan == "professional" and price_pro_yearly:
                price_id = price_pro_yearly
            else:
                # Fall back to monthly price if yearly not configured
                price_id = price_basic if plan == "basic" else price_pro
        else:
            price_id = price_basic if plan == "basic" else price_pro

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                "user_id": current_user.id,
                "plan": plan,
                "billing_period": billing_period,
            }
        )

        return {"url": session.url, "id": session.id}
    except Exception as e:
        logger.exception("Failed to create checkout session")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/billing/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Handle Stripe webhooks to keep subscription state in sync."""
    webhook_secret = _require_env("STRIPE_WEBHOOK_SECRET")
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=webhook_secret
        )
    except Exception as e:
        logger.warning(f"Webhook verification failed: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event.get("type")
    data = event.get("data", {}).get("object", {})
    logger.info(f"Stripe webhook received: {event_type}")

    try:
        if event_type == "checkout.session.completed":
            # Retrieve expanded subscription to get customer/sub info
            session_id = data.get("id")
            stripe.api_key = _require_env("STRIPE_SECRET_KEY")
            session = stripe.checkout.Session.retrieve(session_id, expand=["subscription"])

            customer_id = session.get("customer")
            subscription_id = session.get("subscription", {}).get("id") if isinstance(session.get("subscription"), dict) else session.get("subscription")
            plan_meta = session.get("metadata", {}).get("plan")
            user_id = session.get("metadata", {}).get("user_id")

            # Map plan string to internal enum
            plan_enum = SubscriptionPlan.BASIC if plan_meta == "basic" else SubscriptionPlan.PROFESSIONAL

            from app.services.user import get_user_by_id
            user = get_user_by_id(db, user_id)
            if not user:
                logger.error(f"Webhook: user not found for user_id={user_id}")
                return {"status": "ignored"}

            update_subscription(
                db=db,
                user=user,
                plan=plan_enum,
                status=SubscriptionStatus.ACTIVE,
                is_active=True,
                auto_renew=True,
                stripe_customer_id=customer_id,
                stripe_subscription_id=subscription_id,
            )
            return {"status": "ok"}

        elif event_type in ("customer.subscription.updated", "customer.subscription.created"):
            subscription = data
            customer_id = subscription.get("customer")
            status_str = subscription.get("status")
            stripe.api_key = _require_env("STRIPE_SECRET_KEY")
            # Find user by customer_id
            from app.models.user import Subscription
            user = db.query(User).join(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
            if user:
                status_enum = SubscriptionStatus.ACTIVE if status_str == "active" else SubscriptionStatus.CANCELED
                update_subscription(db, user, user.subscription.plan, status=status_enum, is_active=(status_enum == SubscriptionStatus.ACTIVE))
            return {"status": "ok"}

        elif event_type == "customer.subscription.deleted":
            customer_id = data.get("customer")
            from app.models.user import Subscription
            user = db.query(User).join(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
            if user:
                update_subscription(db, user, user.subscription.plan, status=SubscriptionStatus.CANCELED, is_active=False)
            return {"status": "ok"}

        elif event_type == "invoice.payment_failed":
            customer_id = data.get("customer")
            from app.models.user import Subscription
            user = db.query(User).join(Subscription).filter(Subscription.stripe_customer_id == customer_id).first()
            if user:
                update_subscription(db, user, user.subscription.plan, status=SubscriptionStatus.CANCELED, is_active=False)
            return {"status": "ok"}

    except Exception as e:
        logger.exception("Error processing webhook")
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "ignored"}
