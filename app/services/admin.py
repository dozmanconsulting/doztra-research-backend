from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.models.user import UserRole, User
from app.services.auth import verify_token
from app.db.session import get_db

security = HTTPBearer()

def verify_admin_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Verify that the token belongs to an admin user.
    """
    try:
        # Get the user ID from the token
        token_data = verify_token(credentials.credentials, db)
        # Get the user from the database
        user = db.query(User).filter(User.id == token_data.user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Check if user has admin role
        if user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized. Admin privileges required.",
                headers={"WWW-Authenticate": "Bearer"}
            )
        return user
    except HTTPException as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized. Admin privileges required.",
            headers={"WWW-Authenticate": "Bearer"}
        )
