"""
Unit tests for the Chat API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import json

from app.models.chat import MessageRole
from app.services.chat import create_conversation, create_message
from tests.utils.mock_auth import get_test_token


def test_send_message_success(client, user_headers):
    """Test successful message sending."""
    
    # Mock AI response
    ai_response = "This is a test response from the AI."
    usage_data = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
    
    # Use patch to mock the AI service
    with patch('app.services.chat.get_ai_response', return_value=(ai_response, usage_data)):
        # Mock content moderation
        with patch('app.services.chat.moderate_content', return_value=False):
            # Send a test message
            response = client.post(
                "/api/chat/message",
                headers=user_headers,
                json={
                    "message": "Hello, this is a test message.",
                    "model": "gpt-3.5-turbo"
                }
            )
            
            # Check response
            assert response.status_code == 200
            data = response.json()
            assert "conversation_id" in data
            assert "message_id" in data
            assert data["content"] == ai_response
            assert data["usage"] == usage_data


def test_send_message_with_moderation_block(client, user_headers):
    """Test message being blocked by content moderation."""
    
    # Mock content moderation to return True (content flagged)
    with patch('app.services.chat.moderate_content', return_value=True):
        # Send a test message with inappropriate content
        response = client.post(
            "/api/chat/message",
            headers=user_headers,
            json={
                "message": "This message contains inappropriate content.",
                "model": "gpt-3.5-turbo"
            }
        )
        
        # Check response
        assert response.status_code == 400
        data = response.json()
        assert "content policy" in data["detail"].lower()


def test_create_conversation(client, user_headers):
    """Test creating a new conversation."""
    
    # Create a new conversation
    response = client.post(
        "/api/chat/conversations",
        headers=user_headers,
        json={
            "title": "Test Conversation"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Conversation"
    assert data["is_active"] is True
    
    # Store conversation ID for later tests
    conversation_id = data["id"]
    
    # Verify conversation exists by getting it
    response = client.get(
        f"/api/chat/conversations/{conversation_id}",
        headers=user_headers
    )
    
    assert response.status_code == 200
    assert response.json()["id"] == conversation_id


def test_create_conversation_with_initial_message(client, user_headers):
    """Test creating a conversation with an initial message."""
    
    # Mock AI response
    ai_response = "I'm happy to help with your test!"
    usage_data = {"prompt_tokens": 8, "completion_tokens": 15, "total_tokens": 23}
    
    # Use patch to mock the AI service
    with patch('app.services.chat.get_ai_response', return_value=(ai_response, usage_data)):
        # Mock content moderation
        with patch('app.services.chat.moderate_content', return_value=False):
            # Create a new conversation with initial message
            response = client.post(
                "/api/chat/conversations",
                headers=user_headers,
                json={
                    "title": "Test With Initial Message",
                    "initial_message": "This is an initial test message."
                }
            )
            
            # Check response
            assert response.status_code == 200
            data = response.json()
            conversation_id = data["id"]
            
            # Get conversation details to verify messages
            response = client.get(
                f"/api/chat/conversations/{conversation_id}",
                headers=user_headers
            )
            
            # Check that conversation has messages
            assert response.status_code == 200
            data = response.json()
            assert len(data["messages"]) == 2  # User message + AI response
            assert data["messages"][0]["content"] == "This is an initial test message."
            assert data["messages"][0]["role"] == "user"
            assert data["messages"][1]["content"] == ai_response
            assert data["messages"][1]["role"] == "assistant"


def test_list_conversations(client, user_headers, db, test_user):
    """Test listing user conversations."""
    
    # Create some test conversations
    conv1 = create_conversation(db, test_user.id, "First Test Conversation")
    conv2 = create_conversation(db, test_user.id, "Second Test Conversation")
    
    # Get conversations list
    response = client.get(
        "/api/chat/conversations",
        headers=user_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2
    
    # Check that our test conversations are in the list
    conversation_ids = [conv["id"] for conv in data]
    assert conv1.id in conversation_ids
    assert conv2.id in conversation_ids


def test_get_conversation_detail(client, user_headers, db, test_user):
    """Test getting conversation details with messages."""
    
    # Create a test conversation with messages
    conversation = create_conversation(db, test_user.id, "Conversation With Messages")
    
    # Add messages to the conversation
    user_message = create_message(db, conversation.id, "Hello AI!", MessageRole.USER)
    ai_message = create_message(
        db, 
        conversation.id, 
        "Hello human! How can I help you today?", 
        MessageRole.ASSISTANT,
        model="gpt-3.5-turbo"
    )
    
    # Get conversation details
    response = client.get(
        f"/api/chat/conversations/{conversation.id}",
        headers=user_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation.id
    assert data["title"] == "Conversation With Messages"
    
    # Check messages
    assert len(data["messages"]) == 2
    assert data["messages"][0]["id"] == user_message.id
    assert data["messages"][0]["content"] == "Hello AI!"
    assert data["messages"][0]["role"] == "user"
    
    assert data["messages"][1]["id"] == ai_message.id
    assert data["messages"][1]["content"] == "Hello human! How can I help you today?"
    assert data["messages"][1]["role"] == "assistant"
    assert data["messages"][1]["model"] == "gpt-3.5-turbo"


def test_update_conversation(client, user_headers, db, test_user):
    """Test updating a conversation."""
    
    # Create a test conversation
    conversation = create_conversation(db, test_user.id, "Original Title")
    
    # Update the conversation
    response = client.put(
        f"/api/chat/conversations/{conversation.id}",
        headers=user_headers,
        json={
            "title": "Updated Title"
        }
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == conversation.id
    assert data["title"] == "Updated Title"
    
    # Verify update by getting the conversation
    response = client.get(
        f"/api/chat/conversations/{conversation.id}",
        headers=user_headers
    )
    
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"


def test_delete_conversation(client, user_headers, db, test_user):
    """Test deleting a conversation (soft delete)."""
    
    # Create a test conversation
    conversation = create_conversation(db, test_user.id, "To Be Deleted")
    
    # Delete the conversation
    response = client.delete(
        f"/api/chat/conversations/{conversation.id}",
        headers=user_headers
    )
    
    # Check response
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify deletion by trying to get the conversation
    response = client.get(
        f"/api/chat/conversations/{conversation.id}",
        headers=user_headers
    )
    
    # Should return 404 since it's soft-deleted
    assert response.status_code == 404


def test_unauthorized_access(client):
    """Test unauthorized access to chat endpoints."""
    
    # Try to access endpoints without authentication
    endpoints = [
        {"method": "post", "url": "/api/chat/message", "json": {"message": "test"}},
        {"method": "get", "url": "/api/chat/conversations"},
        {"method": "post", "url": "/api/chat/conversations", "json": {"title": "test"}},
    ]
    
    for endpoint in endpoints:
        method = getattr(client, endpoint["method"])
        json_data = endpoint.get("json", {})
        
        response = method(endpoint["url"], json=json_data)
        assert response.status_code in (401, 403), f"Expected 401/403 for {endpoint['url']}, got {response.status_code}"


def test_access_another_users_conversation(client, user_headers, admin_headers, db, test_user, admin_user):
    """Test that a user cannot access another user's conversation."""
    
    # Create a conversation for the regular user
    conversation = create_conversation(db, test_user.id, "Regular User's Conversation")
    
    # Try to access it with admin user's token
    response = client.get(
        f"/api/chat/conversations/{conversation.id}",
        headers=admin_headers
    )
    
    # Should return 404 since it's not admin's conversation
    assert response.status_code == 404
