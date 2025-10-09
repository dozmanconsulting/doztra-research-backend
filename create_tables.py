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
            
            # Check if modeltier enum exists
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'modeltier')"))
            if not result.scalar():
                conn.execute(text("CREATE TYPE modeltier AS ENUM ('gpt-3.5-turbo', 'gpt-4', 'gpt-4-turbo', 'gpt-4-32k', 'claude-3-opus')"))
                conn.commit()
                logger.info("Created modeltier enum")
            else:
                logger.info("modeltier enum already exists")
                
            # Check if subscriptionstatus enum exists
            result = conn.execute(text("SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'subscriptionstatus')"))
            if not result.scalar():
                conn.execute(text("CREATE TYPE subscriptionstatus AS ENUM ('active', 'canceled', 'expired')"))
                conn.commit()
                logger.info("Created subscriptionstatus enum")
            else:
                logger.info("subscriptionstatus enum already exists")
        
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
        Column('status', String(50), nullable=False, default='ACTIVE'),
        Column('start_date', DateTime, nullable=False, server_default=func.now()),
        Column('expires_at', DateTime, nullable=True),
        Column('is_active', Boolean, nullable=False, default=True),
        Column('auto_renew', Boolean, nullable=False, default=False),
        Column('stripe_customer_id', String(255), nullable=True),
        Column('stripe_subscription_id', String(255), nullable=True),
        Column('payment_method_id', String(255), nullable=True),
        Column('token_limit', Integer, nullable=True),
        Column('max_model_tier', String(50), nullable=False, default='gpt-3.5-turbo'),
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
        Column('type', String(50), nullable=False, default='general'),
        Column('status', String(50), nullable=False, default='active'),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now()),
        Column('project_metadata', JSONB, nullable=True)
    )
    
    generated_content = Table(
        'generated_content',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('project_id', PostgresUUID(as_uuid=True), ForeignKey('research_projects.id', ondelete='CASCADE'), nullable=False),
        Column('section_title', String(255), nullable=False),
        Column('content', Text, nullable=False),
        Column('version', Integer, default=1, nullable=False),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now()),
        Column('content_metadata', JSONB, nullable=True)
    )
    
    content_feedback = Table(
        'content_feedback',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('content_id', PostgresUUID(as_uuid=True), ForeignKey('generated_content.id', ondelete='CASCADE'), nullable=False),
        Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('rating', Integer, nullable=False),
        Column('comments', Text),
        Column('created_at', DateTime, nullable=False, server_default=func.now()),
        Column('updated_at', DateTime, nullable=False, server_default=func.now(), onupdate=func.now()),
        Column('feedback_metadata', JSONB, nullable=True)
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
    
    # Add usage_statistics table
    usage_statistics = Table(
        'usage_statistics',
        metadata,
        Column('id', PostgresUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        Column('user_id', PostgresUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        Column('chat_messages', Integer, nullable=False, default=0),
        Column('plagiarism_checks', Integer, nullable=False, default=0),
        Column('prompts_generated', Integer, nullable=False, default=0),
        Column('tokens_used', Integer, nullable=False, default=0),
        Column('tokens_limit', Integer, nullable=False, default=100000),
        Column('last_reset_date', DateTime, nullable=False, server_default=func.now()),
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

def ensure_usage_statistics_table(engine):
    """Ensure the usage_statistics table exists."""
    logger.info("Checking for usage_statistics table...")
    
    try:
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'usage_statistics'
                )
            """))
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("usage_statistics table already exists")
                return True
            
            # Create the table if it doesn't exist
            logger.info("Creating usage_statistics table...")
            conn.execute(text("""
                CREATE TABLE usage_statistics (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    chat_messages INTEGER NOT NULL DEFAULT 0,
                    plagiarism_checks INTEGER NOT NULL DEFAULT 0,
                    prompts_generated INTEGER NOT NULL DEFAULT 0,
                    tokens_used INTEGER NOT NULL DEFAULT 0,
                    tokens_limit INTEGER NOT NULL DEFAULT 100000,
                    last_reset_date TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
                    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
                    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
                )
            """))
            conn.commit()
            
            logger.info("Successfully created usage_statistics table")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error ensuring usage_statistics table: {e}")
        return False

def ensure_subscription_columns(engine):
    """Ensure the subscriptions table has all required columns."""
    logger.info("Checking subscriptions table columns...")
    
    try:
        with engine.connect() as conn:
            # Check if required columns exist
            columns_to_check = [
                "status", "expires_at", "auto_renew", "stripe_customer_id", 
                "stripe_subscription_id", "payment_method_id", "token_limit", "max_model_tier"
            ]
            
            for column in columns_to_check:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'subscriptions' AND column_name = '{column}'
                    )
                """))
                column_exists = result.scalar()
                
                if not column_exists:
                    logger.info(f"Adding {column} column to subscriptions table...")
                    
                    if column == "status":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN status VARCHAR(50) DEFAULT 'active' NOT NULL
                        """))
                    elif column == "expires_at":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN expires_at TIMESTAMP WITHOUT TIME ZONE
                        """))
                    elif column == "auto_renew":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN auto_renew BOOLEAN DEFAULT FALSE NOT NULL
                        """))
                    elif column == "stripe_customer_id":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN stripe_customer_id VARCHAR(255)
                        """))
                    elif column == "stripe_subscription_id":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN stripe_subscription_id VARCHAR(255)
                        """))
                    elif column == "payment_method_id":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN payment_method_id VARCHAR(255)
                        """))
                    elif column == "token_limit":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN token_limit INTEGER
                        """))
                    elif column == "max_model_tier":
                        conn.execute(text("""
                            ALTER TABLE subscriptions 
                            ADD COLUMN max_model_tier VARCHAR(50) DEFAULT 'gpt-3.5-turbo' NOT NULL
                        """))
                    
                    conn.commit()
                    logger.info(f"Successfully added {column} column to subscriptions table")
                else:
                    logger.info(f"{column} column already exists in subscriptions table")
            
            logger.info("All required columns exist in subscriptions table")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error ensuring subscription columns: {e}")
        return False

def ensure_user_preferences_columns(engine):
    """Ensure the user_preferences table has all required columns."""
    logger.info("Checking user_preferences table columns...")
    
    try:
        with engine.connect() as conn:
            # Check if the table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'user_preferences'
                )
            """))
            table_exists = result.scalar()
            
            if not table_exists:
                logger.info("Creating user_preferences table...")
                conn.execute(text("""
                    CREATE TABLE user_preferences (
                        id UUID PRIMARY KEY,
                        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        theme VARCHAR(50) DEFAULT 'light',
                        notifications BOOLEAN DEFAULT TRUE,
                        default_model VARCHAR(50) DEFAULT 'gpt-3.5-turbo',
                        created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now(),
                        updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
                    )
                """))
                conn.commit()
                logger.info("Successfully created user_preferences table")
                return True
            
            # Check if required columns exist
            columns_to_check = ["theme", "notifications", "default_model"]
            
            for column in columns_to_check:
                result = conn.execute(text(f"""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.columns 
                        WHERE table_name = 'user_preferences' AND column_name = '{column}'
                    )
                """))
                column_exists = result.scalar()
                
                if not column_exists:
                    logger.info(f"Adding {column} column to user_preferences table...")
                    
                    if column == "theme":
                        conn.execute(text("""
                            ALTER TABLE user_preferences 
                            ADD COLUMN theme VARCHAR(50) DEFAULT 'light'
                        """))
                    elif column == "notifications":
                        conn.execute(text("""
                            ALTER TABLE user_preferences 
                            ADD COLUMN notifications BOOLEAN DEFAULT TRUE
                        """))
                    elif column == "default_model":
                        conn.execute(text("""
                            ALTER TABLE user_preferences 
                            ADD COLUMN default_model VARCHAR(50) DEFAULT 'gpt-3.5-turbo'
                        """))
                    
                    conn.commit()
                    logger.info(f"Successfully added {column} column to user_preferences table")
                else:
                    logger.info(f"{column} column already exists in user_preferences table")
            
            # Check if preferences column exists and is NOT NULL
            result = conn.execute(text("""
                SELECT is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'user_preferences' AND column_name = 'preferences'
            """))
            row = result.fetchone()
            
            if row and row[0] == 'NO':  # Column exists and is NOT NULL
                logger.info("Making preferences column nullable...")
                conn.execute(text("""
                    ALTER TABLE user_preferences 
                    ALTER COLUMN preferences DROP NOT NULL
                """))
                conn.commit()
                logger.info("Successfully made preferences column nullable")
            
            logger.info("All required columns exist in user_preferences table")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error ensuring user_preferences columns: {e}")
        return False

def ensure_refresh_tokens_table(engine):
    """Ensure the refresh_tokens table exists."""
    logger.info("Checking for refresh_tokens table...")
    
    try:
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT 1 
                    FROM information_schema.tables 
                    WHERE table_name = 'refresh_tokens'
                )
            """))
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("refresh_tokens table already exists")
                return True
            
            # Create the table if it doesn't exist
            logger.info("Creating refresh_tokens table...")
            conn.execute(text("""
                CREATE TABLE refresh_tokens (
                    id UUID PRIMARY KEY,
                    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token VARCHAR(255) NOT NULL,
                    expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT now()
                )
            """))
            conn.commit()
            
            logger.info("Successfully created refresh_tokens table")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Error ensuring refresh_tokens table: {e}")
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
        
        # Ensure usage_statistics table exists
        ensure_usage_statistics_table(engine)
        
        # Ensure subscription columns exist
        ensure_subscription_columns(engine)
        
        # Ensure user_preferences columns exist
        ensure_user_preferences_columns(engine)
        
        # Ensure refresh_tokens table exists
        ensure_refresh_tokens_table(engine)
        
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
