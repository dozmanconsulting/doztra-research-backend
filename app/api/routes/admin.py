from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from typing import Any, List, Optional
from datetime import datetime, timedelta

from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.user import User as UserSchema
from app.schemas.admin import UserStatistics, AdminDashboardStats
from app.schemas.admin_user import UserStatusUpdate, AdminUserCreate
from app.services.admin import verify_admin_token
from app.services.admin_stats import get_user_statistics, get_admin_dashboard_stats
from app.services.user import get_users, get_user_by_id, update_user_status, create_user, get_user_by_email, delete_user

router = APIRouter()


@router.get("/dashboard", response_model=AdminDashboardStats)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_token),
) -> Any:
    """
    Get admin dashboard statistics.
    
    Returns:
        AdminDashboardStats object with admin dashboard statistics
    """
    return get_admin_dashboard_stats(db)


@router.get("/users", response_model=List[UserSchema])
def read_all_users(
    skip: int = 0,
    limit: int = 100,
    filter_by: Optional[str] = None,
    filter_value: Optional[str] = None,
    sort_by: str = "created_at",
    sort_desc: bool = True,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_token),
) -> Any:
    """
    Get all users with filtering and sorting options. Admin only.
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Maximum number of records to return (default: 100)
    - filter_by: Field to filter by (email, name, role, is_active, is_verified, subscription.plan)
    - filter_value: Value to filter by
    - sort_by: Field to sort by (id, email, name, created_at, updated_at)
    - sort_desc: Sort in descending order if true, ascending if false (default: true)
    """
    return get_users(
        db, 
        skip=skip, 
        limit=limit, 
        filter_by=filter_by, 
        filter_value=filter_value,
        sort_by=sort_by,
        sort_desc=sort_desc
    )


@router.get("/users/statistics", response_model=UserStatistics)
def get_users_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_token),
) -> Any:
    """
    Get user statistics. Admin only.
    
    Returns:
        UserStatistics object with user statistics
    """
    return get_user_statistics(db)


@router.get("/users/{user_id}", response_model=UserSchema)
def read_user(    
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_token),
) -> Any:
    """
    Get a specific user by ID. Admin only.
    
    Path Parameters:
    - user_id: ID of the user to retrieve
    """
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_endpoint(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_token),
    response: Response = None,
) -> None:
    """
    Delete a user. Admin only.
    
    Path Parameters:
    - user_id: ID of the user to delete
    """
    # Get the user
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent admins from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )
    
    # Delete the user
    success = delete_user(db, user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user",
        )
    
    # For 204 responses, we don't return anything
    # response.status_code is already set by FastAPI based on the status_code parameter


@router.patch("/users/{user_id}/status", response_model=UserSchema)
def update_user_status_endpoint(
    user_id: str,
    status_update: UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_token),
) -> Any:
    """
    Update a user's status (active, verified, role). Admin only.
    
    Path Parameters:
    - user_id: ID of the user to update
    
    Request Body:
    - is_active: Whether the user is active (optional)
    - is_verified: Whether the user is verified (optional)
    - role: User role (optional)
    """
    # Get the user
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent admins from deactivating themselves
    if current_user.id == user_id and status_update.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    # Prevent admins from changing their own role
    if current_user.id == user_id and status_update.role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )
    
    # Update user status
    updated_user = update_user_status(
        db, 
        user, 
        is_active=status_update.is_active,
        is_verified=status_update.is_verified,
        role=status_update.role
    )
    
    return updated_user


@router.post("/users", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
def create_user_admin(
    user_in: AdminUserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(verify_admin_token),
) -> Any:
    """
    Create a new user. Admin only.
    
    Request Body:
    - email: User email
    - name: User name
    - password: User password
    - role: User role (optional, default: user)
    - is_active: Whether the user is active (optional, default: true)
    - is_verified: Whether the user is verified (optional, default: true)
    - subscription: Subscription information (optional)
    """
    # Check if user with this email already exists
    existing_user = get_user_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # Create new user
    user = create_user(db, user_in)
    
    # Update user status if needed
    if user_in.is_active is not None or user_in.is_verified is not None or user_in.role != UserRole.USER:
        user = update_user_status(
            db, 
            user, 
            is_active=user_in.is_active,
            is_verified=user_in.is_verified,
            role=user_in.role
        )
    
    return user
