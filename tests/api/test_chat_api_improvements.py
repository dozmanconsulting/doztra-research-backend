"""
Tests for the improved Chat API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.main import app
from app.models.chat import Conversation, Message, MessageRole
from app.models.user import User
from app.services.chat import create_conversation, create_message
from app.db.session import get_db
from tests.utils.auth import get_test_token


@pytest.fixture
def test_conversation_with_metadata(db: Session, test_user: User):
    """Create a test conversation with metadata."""
    metadata = {"category": "research", "tags": ["AI", "ethics"]}
    conversation = create_conversation(
        db, 
        test_user.id, 
        "Test Conversation with Metadata",
        metadata=metadata
    )
    
    # Add some messages
    create_message(db, conversation.id, "Hello, how are you?", MessageRole.user)
    create_message(db, conversation.id, "I'm doing well, thank you for asking!", MessageRole.assistant)
    
    return conversation


def test_send_message_to_new_endpoint(client: TestClient, test_user: User):
    """Test sending a message to the new /api/messages endpoint."""
    token = get_test_token(test_user)
    
    # Mock the AI response
    with patch('app.services.chat.get_ai_response', return_value=("This is a test response", {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    })):
        # Mock content moderation
        with patch('app.services.chat.moderate_content', return_value=False):
            response = client.post(
                "/api/messages",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "message": "Test message",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "conversation_id" in data
            assert "message_id" in data
            assert data["content"] == "This is a test response"
            assert data["usage"] == {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
            assert "created_at" in data


def test_list_conversations_with_sorting(client: TestClient, test_user: User, db: Session):
    """Test listing conversations with sorting options."""
    token = get_test_token(test_user)
    
    # Create test conversations
    conv1 = create_conversation(db, test_user.id, "A - First Conversation")
    conv2 = create_conversation(db, test_user.id, "B - Second Conversation")
    conv3 = create_conversation(db, test_user.id, "C - Third Conversation")
    
    # Test sorting by title ascending
    response = client.get(
        "/api/conversations?sort_by=title&sort_order=asc",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3
    
    # Check if titles are in ascending order
    titles = [conv["title"] for conv in data[:3]]
    assert "A - First Conversation" in titles[0]
    
    # Test sorting by title descending
    response = client.get(
        "/api/conversations?sort_by=title&sort_order=desc",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check if titles are in descending order
    titles = [conv["title"] for conv in data[:3]]
    assert "C - Third Conversation" in titles[0] or "B - Second Conversation" in titles[0]
    
    # Check that message_count and last_message are included
    assert "message_count" in data[0]
    assert "last_message" in data[0] or data[0]["last_message"] is None


def test_create_conversation_with_metadata(client: TestClient, test_user: User):
    """Test creating a conversation with metadata."""
    token = get_test_token(test_user)
    
    metadata = {
        "category": "research",
        "tags": ["AI", "ethics"],
        "priority": "high"
    }
    
    response = client.post(
        "/api/conversations",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Conversation with Metadata",
            "metadata": metadata
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Conversation with Metadata"
    
    # Get the conversation to verify metadata
    conversation_id = data["id"]
    
    # Check the conversation in the database
    db = next(app.dependency_overrides[get_db]())
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    assert conversation is not None
    assert conversation.conversation_metadata == metadata


def test_get_conversation_messages_with_pagination(client: TestClient, test_user: User, db: Session):
    """Test getting conversation messages with pagination."""
    token = get_test_token(test_user)
    
    # Create a conversation with multiple messages
    conversation = create_conversation(db, test_user.id, "Conversation for Pagination")
    
    # Add 10 messages
    for i in range(10):
        role = MessageRole.user if i % 2 == 0 else MessageRole.assistant
        create_message(db, conversation.id, f"Message {i+1}", role)
    
    # Test pagination - first page
    response = client.get(
        f"/api/conversations/{conversation.id}/messages?skip=0&limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 5
    assert data["total_messages"] == 10
    
    # Test pagination - second page
    response = client.get(
        f"/api/conversations/{conversation.id}/messages?skip=5&limit=5",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["messages"]) == 5
    assert data["messages"][0]["content"] == "Message 6"


def test_update_conversation_status_code(client: TestClient, test_user: User, test_conversation_with_metadata: Conversation):
    """Test that update conversation returns correct status code."""
    token = get_test_token(test_user)
    
    response = client.put(
        f"/api/conversations/{test_conversation_with_metadata.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Conversation Title"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Conversation Title"


def test_delete_conversation_returns_id(client: TestClient, test_user: User, test_conversation_with_metadata: Conversation):
    """Test that delete conversation returns the deleted ID."""
    token = get_test_token(test_user)
    
    response = client.delete(
        f"/api/conversations/{test_conversation_with_metadata.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["id"] == test_conversation_with_metadata.id
