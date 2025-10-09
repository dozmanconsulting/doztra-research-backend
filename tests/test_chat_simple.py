"""
Simplified test for Chat API functionality.
"""

import uuid
import sys
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.base_class import Base
from app.db.session import get_db
from app.models.user import User, UserRole
from app.models.chat import Conversation, Message, MessageRole
from tests.utils.mock_auth import get_password_hash, get_test_token

# Use an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_chat.db"

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


# Mock the authentication dependency
async def mock_get_current_active_user():
    return test_user


# Create a test user
test_user = User(
    id=str(uuid.uuid4()),
    email="test@example.com",
    name="Test User",
    hashed_password=get_password_hash("password"),
    role=UserRole.USER,
    is_active=True,
    is_verified=True
)


# Override the authentication dependency
from app.api.routes.chat import get_current_active_user
app.dependency_overrides[get_current_active_user] = mock_get_current_active_user


# Create a test client
client = TestClient(app)


def setup_module():
    # Create the database and tables
    Base.metadata.create_all(bind=engine)
    
    # Add the test user to the database
    db = TestingSessionLocal()
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    db.close()


def teardown_module():
    # Drop the database after all tests
    Base.metadata.drop_all(bind=engine)


def test_create_conversation():
    """Test creating a new conversation."""
    
    # Create a new conversation
    response = client.post(
        "/api/chat/conversations",
        json={"title": "Test Conversation"}
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert data["is_active"] is True
    
    # Store conversation ID for later tests
    conversation_id = data["id"]
    
    # Verify conversation exists by getting it
    response = client.get(f"/api/chat/conversations/{conversation_id}")
    
    assert response.status_code == 200
    assert response.json()["id"] == conversation_id


def test_send_message():
    """Test sending a message and getting AI response."""
    
    # Mock AI response
    ai_response = "This is a test response from the AI."
    usage_data = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    
    # Create a conversation first
    response = client.post(
        "/api/chat/conversations",
        json={"title": "Message Test Conversation"}
    )
    conversation_id = response.json()["id"]
    
    # Use patch to mock the AI service
    with patch('app.services.chat.get_ai_response', return_value=(ai_response, usage_data)):
        # Mock content moderation
        with patch('app.services.chat.moderate_content', return_value=False):
            # Send a test message
            response = client.post(
                "/api/chat/message",
                json={
                    "message": "Hello, this is a test message.",
                    "conversation_id": conversation_id,
                    "model": "gpt-3.5-turbo"
                }
            )
            
            # Check response
            assert response.status_code == 200
            data = response.json()
            assert data["conversation_id"] == conversation_id
            assert "message_id" in data
            assert data["content"] == ai_response
            assert data["usage"] == usage_data


if __name__ == "__main__":
    setup_module()
    try:
        test_create_conversation()
        test_send_message()
        print("All tests passed!")
    finally:
        teardown_module()
