#!/usr/bin/env python3
"""
Script to set up the database for Render.com deployment.
This script creates the initial admin user if it doesn't exist.
"""

import logging
import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.user import User, UserRole
from app.services.auth import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
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

logger.info(f"Setting up database with URL: {masked_url}")

# Create engine and session
try:
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    sys.exit(1)

# Create a function to get a database session
def get_db_session():
    db = SessionLocal()
    try:
        return db
    except Exception as e:
        logger.error(f"Error getting database session: {e}")
        raise

def setup_db():
    """Set up the database with initial data."""
    logger.info("Setting up database...")
    
    # Create a database session
    try:
        db = get_db_session()
        logger.info("Database session created successfully")
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        return False
    
    try:
        # Test database connection
        try:
            db.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
            
        # Check if admin user exists
        try:
            admin_user = db.query(User).filter(User.email == "admin@doztra.ai").first()
            logger.info(f"Admin user query executed successfully. Found: {admin_user is not None}")
        except Exception as e:
            logger.error(f"Error querying admin user: {e}")
            return False
        
        if admin_user:
            logger.info("Admin user already exists.")
        else:
            logger.info("Creating admin user...")
            # Create admin user
            try:
                admin_user = User(
                    email="admin@doztra.ai",
                    name="Admin User",
                    hashed_password=get_password_hash("Admin123!"),
                    role=UserRole.ADMIN,
                    is_active=True,
                    is_verified=True
                )
                db.add(admin_user)
                db.commit()
                logger.info("Admin user created successfully.")
            except Exception as e:
                logger.error(f"Failed to create admin user: {e}")
                db.rollback()
                return False
        
        logger.info("Database setup completed successfully.")
        return True
    
    except SQLAlchemyError as e:
        logger.error(f"Database setup failed: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()
        logger.info("Database connection closed")

if __name__ == "__main__":
    success = setup_db()
    sys.exit(0 if success else 1)
