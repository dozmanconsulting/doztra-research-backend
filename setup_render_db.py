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
from app.db.session import get_db
from app.models.user import User, UserRole
from app.services.auth import get_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_db():
    """Set up the database with initial data."""
    logger.info("Setting up database...")
    
    # Create a database session
    db = next(get_db())
    
    try:
        # Check if admin user exists
        admin_user = db.query(User).filter(User.email == "admin@doztra.ai").first()
        
        if admin_user:
            logger.info("Admin user already exists.")
        else:
            logger.info("Creating admin user...")
            # Create admin user
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
        
        logger.info("Database setup completed successfully.")
        return True
    
    except SQLAlchemyError as e:
        logger.error(f"Database setup failed: {e}")
        db.rollback()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = setup_db()
    sys.exit(0 if success else 1)
