#!/usr/bin/env python3
"""
Migration script to add last_login column to users table.
"""

import logging
from sqlalchemy import create_engine, Column, DateTime, text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_migration():
    """Add last_login column to users table."""
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Check if column exists
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name='users' AND column_name='last_login'"
            ))
            if result.fetchone():
                logger.info("Column 'last_login' already exists in users table.")
                return True
        
        # Add column
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE users ADD COLUMN last_login TIMESTAMP"))
            conn.commit()
            
        logger.info("Successfully added 'last_login' column to users table.")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error adding 'last_login' column: {e}")
        return False

if __name__ == "__main__":
    logger.info("Running migration to add last_login column...")
    success = run_migration()
    if success:
        logger.info("Migration completed successfully.")
    else:
        logger.error("Migration failed.")
