#!/usr/bin/env python3
"""
Script to create all database tables and admin user.
"""

import os
import sys
import logging
import uuid
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Text, Enum, UUID
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("table-creator")

# Set database URL
DATABASE_URL = "postgresql://doztra:CVKjhOhJVhz6cZrkmOEEYmrimqAGrJc9@dpg-d3jn88hr0fns738d19cg-a.frankfurt-postgres.render.com/doztra_db_xbng"
os.environ["DATABASE_URL"] = DATABASE_URL

# Import after setting environment variable
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.user import UserRole
from app.services.auth import get_password_hash

def create_engine_and_session():
    """Create SQLAlchemy engine and session."""
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    return engine, Session()

def create_enum_types(engine):
    """Create PostgreSQL enum types if they don't exist."""
    logger.info("Creating enum types...")
    
    try:
        with engine.connect() as conn:
            # Check if subscriptionplan enum exists
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionplan')"))
            if not result.scalar():
                conn.execute(text("CREATE TYPE subscriptionplan AS ENUM ('FREE', 'BASIC', 'PROFESSIONAL')"))
                conn.commit()
                logger.info("Created subscriptionplan enum")
            else:
                logger.info("subscriptionplan enum already exists")
            
            # Add other enum types here if needed
        
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating enum types: {e}")
        return False

def create_tables(engine):
    """Create all database tables."""
    logger.info("Creating database tables...")
    
    metadata = MetaData()
    
    # Define tables
    users = Table(
        'users',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('email', String(255), unique=True, nullable=False),
        Column('name', String(255)),
        Column('hashed_password', String(255), nullable=False),
        Column('role', String(50), nullable=False),
        Column('is_active', Boolean, nullable=False, default=True),
        Column('is_verified', Boolean, nullable=False, default=False),
        Column('last_login', DateTime, nullable=True),  # Added last_login column
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    subscriptions = Table(
        'subscriptions',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('plan', String(50), nullable=False),
        Column('start_date', DateTime, nullable=False, server_default=func.now()),
        Column('end_date', DateTime),
        Column('is_active', Boolean, nullable=False, default=True),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    token_usage = Table(
        'token_usage',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('tokens_used', Integer, nullable=False, default=0),
        Column('date', DateTime, nullable=False, server_default=func.now()),
        Column('model', String(50)),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    user_preferences = Table(
        'user_preferences',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
        Column('preferences', JSONB, nullable=False, default={}),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    research_projects = Table(
        'research_projects',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('title', String(255), nullable=False),
        Column('description', Text),
        Column('status', String(50), nullable=False, default='active'),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    research_content = Table(
        'research_content',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('project_id', PostgresUUID(as_uuid=True), ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False),
        Column('title', String(255), nullable=False),
        Column('content', Text, nullable=False),
        Column('content_type', String(50), nullable=False),
        Column('metadata', JSONB),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    documents = Table(
        'documents',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('title', String(255), nullable=False),
        Column('content', Text, nullable=False),
        Column('metadata', JSONB),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    document_queries = Table(
        'document_queries',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('document_id', PostgresUUID(as_uuid=True), ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        Column('query', Text, nullable=False),
        Column('response', Text, nullable=False),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    )
    
    # Create tables
    try:
        for table in metadata.sorted_tables:
            try:
                table.create(engine, checkfirst=True)
                logger.info(f"Created or verified table: {table.name}")
            except SQLAlchemyError as e:
                logger.error(f"Error creating table {table.name}: {e}")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating tables: {e}")
        return False

def create_admin_user(session):
    """Create admin user if it doesn't exist."""
    logger.info("Creating admin user...")
    
    try:
        # Check if admin user exists
        result = session.execute(text("SELECT COUNT(*) FROM users WHERE email = 'admin@doztra.ai'"))
        if result.scalar() > 0:
            logger.info("Admin user already exists")
            return True
        
        # Create admin user
        admin_id = uuid.uuid4()
        now = datetime.utcnow()
        
        session.execute(
            text("""
            INSERT INTO users (id, email, name, hashed_password, role, is_active, is_verified, created_at, updated_at)
            VALUES (:id, :email, :name, :hashed_password, :role, :is_active, :is_verified, :created_at, :updated_at)
            """),
            {
                "id": admin_id,
                "email": "admin@doztra.ai",
                "name": "Admin User",
                "hashed_password": get_password_hash("Admin123!"),
                "role": UserRole.ADMIN.value,
                "is_active": True,
                "is_verified": True,
                "created_at": now,
                "updated_at": now
            }
        )
        
        session.commit()
        logger.info("Admin user created successfully")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Error creating admin user: {e}")
        session.rollback()
        return False

def ensure_last_login_column(engine):
    """Ensure the last_login column exists in the users table."""
    logger.info("Checking for last_login column in users table...")
    
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
            
            # Add the column if it doesn't exist
            logger.info("Adding last_login column to users table...")
            conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN last_login TIMESTAMP WITHOUT TIME ZONE NULL
            """))
            conn.commit()
            
            logger.info("Successfully added last_login column to users table")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error ensuring last_login column: {e}")
        return False

def check_tables(engine):
    """Check which tables exist in the database."""
    logger.info("Checking database tables...")
    
    try:
        with engine.connect() as conn:
            result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
            """))
            
            tables = [row[0] for row in result]
            
            if tables:
                logger.info("Tables in database:")
                for table in tables:
                    logger.info(f"  - {table}")
            else:
                logger.info("No tables found in database")
                
            return tables
    except SQLAlchemyError as e:
        logger.error(f"Error checking tables: {e}")
        return []

def main():
    """Main function."""
    logger.info(f"Starting table creation with DATABASE_URL: {DATABASE_URL}")
    
    # Create engine and session
    engine, session = create_engine_and_session()
    
    try:
        # Create enum types
        create_enum_types(engine)
        
        # Create tables
        create_tables(engine)
        
        # Ensure last_login column exists
        ensure_last_login_column(engine)
        
        # Create admin user
        create_admin_user(session)
        
        # Check tables
        check_tables(engine)
        
        logger.info("Database setup completed successfully")
    except Exception as e:
        logger.error(f"Error setting up database: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    main()
