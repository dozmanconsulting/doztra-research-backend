#!/usr/bin/env python3
"""
Script to check database connection on Render.com
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
    
    # Log the database URL (with password masked)
    masked_url = database_url
    if "://" in database_url and "@" in database_url:
        parts = database_url.split("@")
        if len(parts) > 1:
            user_pass = parts[0].split("://")[1]
            if ":" in user_pass:
                user = user_pass.split(":")[0]
                masked_url = database_url.replace(user_pass, f"{user}:****")
    
    logger.info(f"Using DATABASE_URL: {masked_url}")
    
    try:
        # Create engine and test connection
        logger.info("Creating database engine...")
        engine = create_engine(database_url)
        
        logger.info("Testing database connection...")
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            value = result.fetchone()[0]
            logger.info(f"Database connection successful: {value}")
            
            # Check PostgreSQL version
            version_result = connection.execute(text("SELECT version()"))
            version = version_result.fetchone()[0]
            logger.info(f"PostgreSQL version: {version}")
            
            # List tables
            tables_result = connection.execute(text(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'public'"
            ))
            tables = [row[0] for row in tables_result]
            logger.info(f"Tables in database: {', '.join(tables) if tables else 'No tables found'}")
            
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
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
