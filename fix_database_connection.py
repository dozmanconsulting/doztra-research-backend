#!/usr/bin/env python3
"""
Script to fix database connection issues on Render.com
This script will check and update the database connection settings.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Check the database connection and print diagnostic information."""
    # Get the DATABASE_URL from environment
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL environment variable is not set!")
        return False
    
    logger.info(f"Using DATABASE_URL: {database_url}")
    
    try:
        # Create engine and test connection
        engine = create_engine(database_url)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info(f"Database connection successful: {result.fetchone()}")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("Checking database connection...")
    
    # Print environment variables for debugging
    logger.info("Environment variables:")
    for key, value in os.environ.items():
        if "DATABASE" in key or "POSTGRES" in key:
            # Mask password in connection string for security
            if "PASSWORD" in key or "URL" in key:
                masked_value = value
                if "://" in value:
                    parts = value.split("@")
                    if len(parts) > 1:
                        user_pass = parts[0].split("://")[1]
                        if ":" in user_pass:
                            user = user_pass.split(":")[0]
                            masked_value = value.replace(user_pass, f"{user}:****")
                logger.info(f"  {key}={masked_value}")
            else:
                logger.info(f"  {key}={value}")
    
    # Check connection
    success = check_database_connection()
    sys.exit(0 if success else 1)
