#!/usr/bin/env python3
"""
Database setup script for Doztra Auth Service.

This script creates the database schema directly using SQLAlchemy.
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

from app.db.base import Base
from app.models.user import User, Subscription, RefreshToken, UserRole
from app.core.config import settings
from app.services.auth import get_password_hash

def setup_database(force_recreate=False):
    """Set up the database schema.
    
    Args:
        force_recreate: If True, drop and recreate all tables. If False, only create tables if they don't exist.
    """
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Check if tables exist
        inspector = inspect(engine)
        tables_exist = len(inspector.get_table_names()) > 0
        
        if force_recreate and tables_exist:
            # Drop all tables if they exist and force_recreate is True
            Base.metadata.drop_all(engine)
            print("Dropped existing tables.")
            tables_exist = False
        
        if not tables_exist:
            # Create tables
            Base.metadata.create_all(engine)
            print("Database schema created successfully.")
        else:
            print("Database schema already exists. Skipping creation.")
            
        return True
    except SQLAlchemyError as e:
        print(f"Error creating database schema: {e}")
        return False

def create_admin_user():
    """Create an admin user."""
    from sqlalchemy.orm import sessionmaker
    
    try:
        # Create engine
        engine = create_engine(settings.DATABASE_URL)
        
        # Create session
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        
        # Check if admin user already exists
        admin_user = db.query(User).filter(User.email == "admin@doztra.ai").first()
        if admin_user:
            print("Admin user already exists.")
            return True
        
        # Create admin user with admin role
        admin_user = User(
            email="admin@doztra.ai",
            name="Admin User",
            hashed_password=get_password_hash("AdminPassword123!"),
            role=UserRole.ADMIN,  # Explicitly set admin role
            is_active=True,
            is_verified=True
        )
        print("Creating admin user with role:", UserRole.ADMIN)
        db.add(admin_user)
        db.flush()
        
        # Create subscription for admin
        admin_subscription = Subscription(
            user_id=admin_user.id,
            plan="PROFESSIONAL",
            status="ACTIVE",
            auto_renew=True
        )
        db.add(admin_subscription)
        
        # Create test user with regular user role
        test_user = User(
            email="test@doztra.ai",
            name="Test User",
            hashed_password=get_password_hash("TestPassword123!"),
            role=UserRole.USER,  # Regular user role
            is_active=True,
            is_verified=True
        )
        print("Creating test user with role:", UserRole.USER)
        db.add(test_user)
        db.flush()
        
        # Create subscription for test user
        test_subscription = Subscription(
            user_id=test_user.id,
            plan="BASIC",
            status="ACTIVE",
            auto_renew=True
        )
        db.add(test_subscription)
        
        db.commit()
        print("Admin and test users created successfully.")
        return True
    except SQLAlchemyError as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def main():
    """Main function."""
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Set up the database schema")
    parser.add_argument("--force", action="store_true", help="Force recreate all tables")
    args = parser.parse_args()
    
    print("Setting up database...")
    
    # Setup database
    if not setup_database(force_recreate=args.force):
        sys.exit(1)
    
    # Create admin user
    if not create_admin_user():
        sys.exit(1)
    
    print("Database setup completed successfully.")

if __name__ == "__main__":
    main()
