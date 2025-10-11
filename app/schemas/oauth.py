"""
OAuth schemas for request and response validation.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class OAuthRequest(BaseModel):
    """OAuth authorization request."""
    provider: str = Field(..., description="OAuth provider (e.g., 'google')")
    redirect_uri: Optional[str] = Field(None, description="Optional override for redirect URI")


class OAuthCallback(BaseModel):
    """OAuth callback parameters."""
    code: str = Field(..., description="Authorization code from OAuth provider")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")


class OAuthUserInfo(BaseModel):
    """User information from OAuth provider."""
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    locale: Optional[str] = None
    provider: str
    raw_data: Dict[str, Any]
