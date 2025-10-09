import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
import os
import sys
import uuid

# Add the parent directory to sys.path to allow imports from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app
from app.db.base_class import Base
from app.db.session import get_db
from app.models.user import User, Subscription, SubscriptionPlan, SubscriptionStatus, UserRole
from app.models.token_usage import TokenUsage, TokenUsageSummary, RequestType
from app.models.user_preferences import UserPreferences
from app.models.usage_statistics import UsageStatistics
from app.services.auth import create_access_token, get_password_hash

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Override the get_db dependency
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    
    # Use TestClient for testing
    with TestClient(app) as test_client:
        yield test_client
    
    # Drop the database after the test
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db():
    # Create a new database session for a test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def admin_user(db):
    # Create an admin user
    user_id = str(uuid.uuid4())
    admin = User(
        id=user_id,
        email="admin@example.com",
        name="Admin User",
        hashed_password=get_password_hash("Admin123!"),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True
    )
    db.add(admin)
    
    # Create subscription for admin
    subscription = Subscription(
        user_id=user_id,
        plan=SubscriptionPlan.PROFESSIONAL,
        status=SubscriptionStatus.ACTIVE,
        is_active=True,
        auto_renew=True,
        token_limit=None,  # Unlimited
        max_model_tier="gpt-4-turbo"
    )
    db.add(subscription)
    
    # Create preferences for admin
    preferences = UserPreferences(
        user_id=user_id,
        theme="dark",
        notifications=True,
        default_model="gpt-4-turbo"
    )
    db.add(preferences)
    
    # Create usage statistics for admin
    usage_stats = UsageStatistics(
        user_id=user_id,
        tokens_limit=None  # Unlimited
    )
    db.add(usage_stats)
    
    db.commit()
    db.refresh(admin)
    
    return admin


@pytest.fixture
def regular_user(db):
    # Create a regular user
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email="user@example.com",
        name="Regular User",
        hashed_password=get_password_hash("User123!"),
        role=UserRole.USER,
        is_active=True,
        is_verified=True
    )
    db.add(user)
    
    # Create subscription for user
    subscription = Subscription(
        user_id=user_id,
        plan=SubscriptionPlan.BASIC,
        status=SubscriptionStatus.ACTIVE,
        is_active=True,
        auto_renew=True,
        token_limit=500000,
        max_model_tier="gpt-4"
    )
    db.add(subscription)
    
    # Create preferences for user
    preferences = UserPreferences(
        user_id=user_id,
        theme="light",
        notifications=True,
        default_model="gpt-4"
    )
    db.add(preferences)
    
    # Create usage statistics for user
    usage_stats = UsageStatistics(
        user_id=user_id,
        chat_messages=50,
        plagiarism_checks=5,
        prompts_generated=10,
        tokens_used=100000,
        tokens_limit=500000
    )
    db.add(usage_stats)
    
    # Create some token usage records
    for i in range(5):
        token_usage = TokenUsage(
            user_id=user_id,
            request_type=RequestType.CHAT,
            model="gpt-4",
            prompt_tokens=100,
            completion_tokens=400,
            total_tokens=500,
            timestamp=datetime.utcnow() - timedelta(days=i)
        )
        db.add(token_usage)
    
    # Create token usage summary
    today = datetime.utcnow()
    token_summary = TokenUsageSummary(
        user_id=user_id,
        year=today.year,
        month=today.month,
        day=today.day,
        chat_prompt_tokens=500,
        chat_completion_tokens=2000,
        chat_total_tokens=2500,
        plagiarism_tokens=1000,
        prompt_generation_tokens=500,
        total_tokens=4000
    )
    db.add(token_summary)
    
    db.commit()
    db.refresh(user)
    
    return user


@pytest.fixture
def admin_token(admin_user):
    # Create access token for admin user
    access_token = create_access_token(
        data={"sub": admin_user.id},
        expires_delta=timedelta(minutes=30)
    )
    return access_token


@pytest.fixture
def user_token(regular_user):
    # Create access token for regular user
    access_token = create_access_token(
        data={"sub": regular_user.id},
        expires_delta=timedelta(minutes=30)
    )
    return access_token


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def user_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def test_user(regular_user):
    """Alias for regular_user to match test_chat.py."""
    return regular_user
