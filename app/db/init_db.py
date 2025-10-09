import logging
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from app.db.base import Base
from app.db.session import engine, get_db
from app.models.user import User, Subscription, SubscriptionPlan, SubscriptionStatus
from app.services.auth import get_password_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_db(db: Session) -> None:
    """Initialize database with tables and seed data."""
    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    logger.info("Database tables recreated")
    
    logger.info("Creating initial admin user")
    
    # Create admin user
    admin_user = User(
        email="admin@doztra.ai",
        name="Admin User",
        hashed_password=get_password_hash("AdminPassword123!"),
        is_active=True,
        is_verified=True
    )
    db.add(admin_user)
    db.flush()
    
    # Create subscription for admin
    admin_subscription = Subscription(
        user_id=admin_user.id,
        plan=SubscriptionPlan.PROFESSIONAL,
        status=SubscriptionStatus.ACTIVE,
        auto_renew=True
    )
    db.add(admin_subscription)
    
    # Create test user
    test_user = User(
        email="test@doztra.ai",
        name="Test User",
        hashed_password=get_password_hash("TestPassword123!"),
        is_active=True,
        is_verified=True
    )
    db.add(test_user)
    db.flush()
    
    # Create subscription for test user
    test_subscription = Subscription(
        user_id=test_user.id,
        plan=SubscriptionPlan.BASIC,
        status=SubscriptionStatus.ACTIVE,
        auto_renew=True
    )
    db.add(test_subscription)
    
    db.commit()
    logger.info("Initial data seeded successfully")


def init_test_db() -> None:
    """Initialize test database with tables and seed data for testing."""
    # Use the test database URL from environment
    test_db_url = os.environ.get("TEST_DATABASE_URL", "sqlite:///./test.db")
    test_engine = create_engine(test_db_url)
    
    # Drop all tables and recreate them in the test database
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    
    logger.info("Test database tables recreated")
    
    # Create a session for the test database
    from sqlalchemy.orm import sessionmaker
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    db = TestSessionLocal()
    
    try:
        # Create test user with known ID for tests
        test_user = User(
            id="test-user-id",
            email="test@example.com",
            name="Test User",
            hashed_password=get_password_hash("testpassword"),
            is_active=True,
            is_verified=True
        )
        db.add(test_user)
        
        # Create subscription for test user
        test_subscription = Subscription(
            user_id=test_user.id,
            plan=SubscriptionPlan.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            auto_renew=True
        )
        db.add(test_subscription)
        
        # Create admin user with known ID for tests
        admin_user = User(
            id="admin-user-id",
            email="admin@example.com",
            name="Admin User",
            hashed_password=get_password_hash("adminpassword"),
            is_active=True,
            is_verified=True,
            role="ADMIN"  # Set admin role
        )
        db.add(admin_user)
        
        # Create subscription for admin user
        admin_subscription = Subscription(
            user_id=admin_user.id,
            plan=SubscriptionPlan.PROFESSIONAL,
            status=SubscriptionStatus.ACTIVE,
            auto_renew=True
        )
        db.add(admin_subscription)
        
        # Add any other test data needed for research options tests
        
        db.commit()
        logger.info("Test data seeded successfully")
    finally:
        db.close()
