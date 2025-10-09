import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging

from app.core.config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Get database URL from environment variable if available (for Render deployment)
# Otherwise use the URL from settings
database_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)

# Log the database URL (with password masked)
masked_url = database_url
if "://" in database_url and "@" in database_url:
    parts = database_url.split("@")
    if len(parts) > 1:
        user_pass = parts[0].split("://")[1]
        if ":" in user_pass:
            user = user_pass.split(":")[0]
            masked_url = database_url.replace(user_pass, f"{user}:****")

logger.info(f"Connecting to database: {masked_url}")

# Create engine and session
engine = create_engine(database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
