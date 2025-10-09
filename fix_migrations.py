#!/usr/bin/env python3
"""
Script to fix migration files and run database setup.
This script will:
1. Fix the migration files to use SQLAlchemy text() function
2. Run the migrations
3. Set up the admin user
"""

import os
import sys
import re
import glob
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("migration-fixer")

def set_database_url():
    """Set the DATABASE_URL environment variable."""
    database_url = "postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"
    os.environ["DATABASE_URL"] = database_url
    logger.info(f"Set DATABASE_URL to: {database_url}")
    return database_url

def fix_migration_files():
    """Fix migration files to use SQLAlchemy text() function."""
    logger.info("Fixing migration files...")
    
    # Find all migration files
    migration_files = glob.glob("alembic/versions/*.py")
    logger.info(f"Found {len(migration_files)} migration files")
    
    for file_path in migration_files:
        logger.info(f"Processing {file_path}")
        
        with open(file_path, 'r') as file:
            content = file.read()
        
        # Check if the file needs fixing
        if "connection.execute(" in content and "from sqlalchemy import text" not in content:
            logger.info(f"Adding import for text() in {file_path}")
            content = "from sqlalchemy import text\n" + content
        
        # Fix raw SQL executions
        content = re.sub(
            r'connection\.execute\(\s*"""(.*?)"""\s*\)',
            r'connection.execute(text("\1"))',
            content,
            flags=re.DOTALL
        )
        
        content = re.sub(
            r'connection\.execute\(\s*"(.*?)"\s*\)',
            r'connection.execute(text("\1"))',
            content
        )
        
        content = re.sub(
            r"connection\.execute\(\s*'(.*?)'\s*\)",
            r"connection.execute(text('\1'))",
            content
        )
        
        # Write the fixed content back
        with open(file_path, 'w') as file:
            file.write(content)
        
        logger.info(f"Fixed {file_path}")
    
    return True

def run_migrations():
    """Run the database migrations."""
    logger.info("Running database migrations...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "alembic", "upgrade", "head"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Migrations completed successfully!")
        logger.info(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Migration failed: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False

def create_new_migration():
    """Create a new migration from scratch."""
    logger.info("Creating a new migration from scratch...")
    
    try:
        # Create a new migration
        result = subprocess.run(
            ["python", "-m", "alembic", "revision", "--autogenerate", "-m", "recreate_schema"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("New migration created successfully!")
        logger.info(result.stdout)
        
        # Run the new migration
        return run_migrations()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to create new migration: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False

def setup_admin_user():
    """Set up the admin user."""
    logger.info("Setting up admin user...")
    
    try:
        result = subprocess.run(
            ["python", "setup_render_db.py"],
            check=True,
            capture_output=True,
            text=True
        )
        logger.info("Admin user setup completed successfully!")
        logger.info(result.stdout)
        logger.info("You can now log in with:")
        logger.info("Email: admin@doztra.ai")
        logger.info("Password: Admin123!")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Admin user setup failed: {e}")
        logger.error(e.stdout)
        logger.error(e.stderr)
        return False

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
    
    # Fix migration files
    fix_migration_files()
    
    # Run migrations
    if run_migrations():
        # Set up admin user
        setup_admin_user()
    else:
        # If migrations fail, create a new migration
        logger.info("Migrations failed. Creating a new migration from scratch...")
        if create_new_migration():
            # Set up admin user
            setup_admin_user()
        else:
            logger.error("All migration attempts failed.")
    
    # Check database tables
    check_database_tables(database_url)
    
    logger.info("Script completed.")

if __name__ == "__main__":
    main()
