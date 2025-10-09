from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Any

from app.db.session import get_db
from app.models.user import User
from app.schemas.usage_statistics import UsageResponse
from app.services.usage_statistics import get_usage_response
from app.services.auth import get_current_user

router = APIRouter()


@router.get("/me", response_model=UsageResponse)
def read_usage_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Any:
    """
    Get current user's usage statistics.
    """
    return get_usage_response(db, current_user.id)
