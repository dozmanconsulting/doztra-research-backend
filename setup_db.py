#!/usr/bin/env python3
"""
Database setup script for Doztra Research Backend.
Creates database tables and runs initial migrations.
"""

import sys
import os
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine


def create_database():
    """Create the database if it doesn't exist."""
    try:
        # Extract database name from URL
        db_url_parts = settings.DATABASE_URL.split('/')
        db_name = db_url_parts[-1]
        base_url = '/'.join(db_url_parts[:-1])
        
        # Connect to PostgreSQL server (not specific database)
        server_engine = create_engine(f"{base_url}/postgres")
        
        with server_engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :db_name"),
                {"db_name": db_name}
            )
            
            if not result.fetchone():
                # Create database
                conn.execute(text("COMMIT"))  # End any existing transaction
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print(f"✓ Created database: {db_name}")
            else:
                print(f"✓ Database already exists: {db_name}")
                
        server_engine.dispose()
        
    except SQLAlchemyError as e:
        print(f"✗ Error creating database: {e}")
        return False
    
    return True


def create_tables(force=False):
    """Create all database tables."""
    try:
        if force:
            print("⚠️  Dropping all existing tables...")
            Base.metadata.drop_all(bind=engine)
            
        print("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables created successfully")
        
    except SQLAlchemyError as e:
        print(f"✗ Error creating tables: {e}")
        return False
    
    return True


def run_migrations():
    """Run Alembic migrations."""
    try:
        import subprocess
        
        print("Running Alembic migrations...")
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(__file__)
        )
        
        if result.returncode == 0:
            print("✓ Migrations completed successfully")
            return True
        else:
            print(f"✗ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        return False


def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description="Set up Doztra Research Backend database")
    parser.add_argument(
        "--force", 
        action="store_true", 
        help="Force recreate all tables (WARNING: This will delete all data)"
    )
    parser.add_argument(
        "--no-migrations", 
        action="store_true", 
        help="Skip running Alembic migrations"
    )
    
    args = parser.parse_args()
    
    print("🚀 Setting up Doztra Research Backend database...")
    print(f"Database URL: {settings.DATABASE_URL}")
    
    # Step 1: Create database
    if not create_database():
        sys.exit(1)
    
    # Step 2: Create tables
    if not create_tables(force=args.force):
        sys.exit(1)
    
    # Step 3: Run migrations (unless skipped)
    if not args.no_migrations:
        if not run_migrations():
            print("⚠️  Migrations failed, but tables were created. You may need to run migrations manually.")
    
    print("✅ Database setup completed successfully!")


if __name__ == "__main__":
    main()
