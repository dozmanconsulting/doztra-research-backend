#!/usr/bin/env python3
"""
Script to add the last_login column to the users table
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("column-adder")

# Set database URL
DATABASE_URL = "postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"
os.environ["DATABASE_URL"] = DATABASE_URL

def add_last_login_column():
    """Add last_login column to users table if it doesn't exist."""
    logger.info("Adding last_login column to users table...")
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' AND column_name = 'last_login'
                )
            """))
            column_exists = result.scalar()
            
            if column_exists:
                logger.info("last_login column already exists in users table")
                return True
            
            # Add the column
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN last_login TIMESTAMP WITHOUT TIME ZONE NULL
            """))
            conn.commit()
            
            logger.info("Successfully added last_login column to users table")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error adding last_login column: {e}")
        return False

def check_users_table_schema():
    """Check the schema of the users table."""
    logger.info("Checking users table schema...")
    
    # Create engine
    engine = create_engine(DATABASE_URL)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            
            logger.info("Users table schema:")
            for column in columns:
                logger.info(f"  - {column[0]}: {column[1]} (nullable: {column[2]})")
            
            return columns
    except SQLAlchemyError as e:
        logger.error(f"Error checking users table schema: {e}")
        return []

if __name__ == "__main__":
    logger.info(f"Starting with DATABASE_URL: {DATABASE_URL}")
    
    # Add last_login column
    add_last_login_column()
    
    # Check users table schema
    check_users_table_schema()
    
    logger.info("Script completed")
