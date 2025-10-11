from pydantic import BaseModel
from typing import Dict, Optional, List
from app.core.config import settings

class OAuthConfig(BaseModel):
    client_id: str
    client_secret: str
    authorize_url: str
    token_url: str
    userinfo_url: str
    redirect_uri: str
    scope: List[str]

# Google OAuth configuration
google_oauth_config = OAuthConfig(
    client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
    client_secret=settings.GOOGLE_OAUTH_CLIENT_SECRET,
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    token_url="https://oauth2.googleapis.com/token",
    userinfo_url="https://www.googleapis.com/oauth2/v3/userinfo",
    redirect_uri=f"{settings.BASE_URL}/api/auth/oauth/google/callback",
    scope=["email", "profile"]
)

# Dictionary of supported OAuth providers
oauth_configs: Dict[str, OAuthConfig] = {
    "google": google_oauth_config,
    # Add more providers here as needed
}
