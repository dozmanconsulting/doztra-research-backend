from pydantic import BaseModel, EmailStr


class EmailVerificationRequest(BaseModel):
    """Schema for email verification request."""
    email: EmailStr


class EmailVerificationResponse(BaseModel):
    success: bool = True
    """Schema for email verification response."""
    message: str


class PasswordResetRequest(BaseModel):
    """Schema for password reset request."""
    email: EmailStr


class PasswordResetResponse(BaseModel):
    success: bool = True
    """Schema for password reset response."""
    message: str


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation."""
    token: str
    new_password: str
