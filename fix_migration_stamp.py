#!/usr/bin/env python3
"""
Script to mark migrations as completed and create admin user directly.
This script will:
1. Mark the migration as completed in Alembic without running it
2. Create the admin user directly using SQLAlchemy
"""

import os
import sys
import logging
import subprocess
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migration-fixer")

# Import models after setting up logging
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.user import User, UserRole
from app.services.auth import get_password_hash

def set_database_url():
    """Set the DATABASE_URL environment variable."""
    database_url = "postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"
    os.environ["DATABASE_URL"] = database_url
    logger.info(f"Set DATABASE_URL to: {database_url}")
    return database_url

def stamp_migration():
    """Mark the migration as completed without running it."""
    logger.info("Marking migration as completed...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "stamp", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Migration marked as completed!")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to mark migration: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False

def create_tables_manually(engine):
    """Create tables manually using SQLAlchemy."""
    logger.info("Creating tables manually...")
    
    try:
        # Create users table
        engine.execute(text("""
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255),
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            is_verified BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
        """))
        logger.info("Created users table")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create tables: {e}")
        return False

def create_admin_user(engine):
    """Create admin user directly."""
    logger.info("Creating admin user...")
    
    try:
        # Create a session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Check if admin user exists
        admin_exists = session.query(text("COUNT(*)")).from_statement(
            text("SELECT COUNT(*) FROM users WHERE email = 'admin@doztra.ai'")
        ).scalar()
        
        if admin_exists and admin_exists > 0:
            logger.info("Admin user already exists")
            return True
        
        # Create admin user
        admin_user = User(
            email="admin@doztra.ai",
            name="Admin User",
            hashed_password=get_password_hash("Admin123!"),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True
        )
        
        session.add(admin_user)
        session.commit()
        logger.info("Admin user created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Failed to create admin user: {e}")
        if session:
            session.rollback()
        return False
    finally:
        if session:
            session.close()

def check_database_tables(database_url):
    """Check the database tables."""
    logger.info("Checking database tables...")
    
    try:
        result = subprocess.run(
            ["psql", database_url, "-c", "\\dt"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Database tables:")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to check database tables: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False

def main():
    """Main function to run the script."""
    logger.info("Starting migration fix and database setup...")
    
    # Set the DATABASE_URL environment variable
    database_url = set_database_url()
    
    # Create engine
    engine = create_engine(database_url)
    
    # Mark migration as completed
    if stamp_migration():
        logger.info("Migration stamped successfully")
    else:
        logger.error("Failed to stamp migration")
    
    # Create admin user
    if create_admin_user(engine):
        logger.info("Admin user setup completed")
    else:
        logger.error("Failed to set up admin user")
    
    # Check database tables
    check_database_tables(database_url)
    
    logger.info("Script completed.")

if __name__ == "__main__":
    main()
