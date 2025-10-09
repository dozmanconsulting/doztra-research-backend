"""
Tests for the Chat API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from unittest.mock import patch, MagicMock

from app.main import app
from app.models.chat import Conversation, Message, MessageRole
from app.models.user import User
from app.services.chat import create_conversation, create_message
from tests.utils.auth import get_test_token


@pytest.fixture
def test_conversation(db: Session, test_user: User):
    """Create a test conversation."""
    conversation = create_conversation(db, test_user.id, "Test Conversation")
    
    # Add some messages
    create_message(db, conversation.id, "Hello, how are you?", MessageRole.USER)
    create_message(db, conversation.id, "I'm doing well, thank you for asking!", MessageRole.ASSISTANT)
    
    return conversation


def test_send_message(client: TestClient, test_user: User):
    """Test sending a message and getting AI response."""
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
                "/api/chat/message",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "message": "Test message",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "max_tokens": 1000
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
            assert "message_id" in data
            assert data["content"] == "This is a test response"
            assert data["usage"] == {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }


def test_list_conversations(client: TestClient, test_user: User, test_conversation: Conversation):
    """Test listing user conversations."""
    token = get_test_token(test_user)
    
    response = client.get(
        "/api/chat/conversations",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(conv["id"] == test_conversation.id for conv in data)


def test_get_conversation_detail(client: TestClient, test_user: User, test_conversation: Conversation):
    """Test getting conversation details with messages."""
    token = get_test_token(test_user)
    
    response = client.get(
        f"/api/chat/conversations/{test_conversation.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_conversation.id
    assert "messages" in data
    assert len(data["messages"]) == 2
    assert data["messages"][0]["role"] == "user"
    assert data["messages"][1]["role"] == "assistant"


def test_update_conversation(client: TestClient, test_user: User, test_conversation: Conversation):
    """Test updating conversation details."""
    token = get_test_token(test_user)
    
    response = client.put(
        f"/api/chat/conversations/{test_conversation.id}",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "title": "Updated Conversation Title"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == test_conversation.id
    assert data["title"] == "Updated Conversation Title"


def test_delete_conversation(client: TestClient, test_user: User, test_conversation: Conversation):
    """Test deleting a conversation."""
    token = get_test_token(test_user)
    
    response = client.delete(
        f"/api/chat/conversations/{test_conversation.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify it's soft-deleted
    response = client.get(
        f"/api/chat/conversations/{test_conversation.id}",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404


def test_create_conversation(client: TestClient, test_user: User):
    """Test creating a new conversation."""
    token = get_test_token(test_user)
    
    # Mock the AI response for initial message
    with patch('app.services.chat.get_ai_response', return_value=("This is a test response", {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    })):
        # Mock content moderation
        with patch('app.services.chat.moderate_content', return_value=False):
            response = client.post(
                "/api/chat/conversations",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "title": "New Test Conversation",
                    "initial_message": "Hello, this is a test"
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["title"] == "New Test Conversation"
            
            # Verify conversation was created with messages
            conversation_id = data["id"]
            response = client.get(
                f"/api/chat/conversations/{conversation_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["messages"]) == 2  # User message + AI response
