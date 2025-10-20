import httpx
from datetime import datetime, timezone
from typing import Optional

from app.core.config import settings

KLAVIYO_EVENTS_URL = "https://a.klaviyo.com/api/events/"
KLAVIYO_REVISION = "2024-06-15"  # Klaviyo API revision date
KLAVIYO_LIST_SUBSCRIBE_URL_TMPL = "https://a.klaviyo.com/api/v2/list/{list_id}/members"


async def send_user_signed_up_event(email: str, first_name: Optional[str] = None, plan: Optional[str] = None) -> None:
    """
    Sends a custom 'user_signed_up' event to Klaviyo Events API.
    Configure a Klaviyo Flow to trigger on this metric name to send your welcome email.
    """
    if not settings.KLAVIYO_API_KEY:
        # No API key configured; skip silently to avoid breaking signup
        return

    headers = {
        "Authorization": f"Klaviyo-API-Key {settings.KLAVIYO_API_KEY}",
        "revision": KLAVIYO_REVISION,
        "Content-Type": "application/json",
    }

    payload = {
        "data": {
            "type": "event",
            "attributes": {
                "metric": {
                    "data": {
                        "type": "metric",
                        "attributes": {"name": settings.KLAVIYO_EVENT_SIGNUP},
                    }
                },
                "profile": {
                    "data": {
                        "type": "profile",
                        "attributes": {
                            "email": email,
                            **({"first_name": first_name} if first_name else {}),
                        },
                    }
                },
                "properties": {**({"plan": plan} if plan else {})},
                "time": datetime.now(timezone.utc).isoformat(),
            },
        }
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(KLAVIYO_EVENTS_URL, json=payload, headers=headers)
            resp.raise_for_status()
    except Exception:
        # Avoid breaking signup flow if Klaviyo is unreachable
        pass


async def subscribe_user_to_list(email: str, first_name: Optional[str] = None) -> None:
    """
    Subscribes a profile to a Klaviyo List using the v2 List Members API.
    Requires settings.KLAVIYO_API_KEY and settings.KLAVIYO_LIST_ID.
    """
    if not settings.KLAVIYO_API_KEY or not settings.KLAVIYO_LIST_ID:
        return

    url = KLAVIYO_LIST_SUBSCRIBE_URL_TMPL.format(list_id=settings.KLAVIYO_LIST_ID)
    payload = {
        "api_key": settings.KLAVIYO_API_KEY,
        "profiles": [
            {
                "email": email,
                **({"first_name": first_name} if first_name else {}),
            }
        ],
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, json=payload, headers={"Content-Type": "application/json"})
            resp.raise_for_status()
    except Exception:
        # Never break signup if list subscribe fails
        pass

