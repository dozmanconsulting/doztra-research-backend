"""
Test cases for Conversation Management API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
import json
import uuid

from app.main import app
from app.services.auth import create_access_token


client = TestClient(app)


@pytest.fixture
def test_user():
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com", 
        "name": "Test User"
    }


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}


class TestConversationSessions:
    """Test conversation session management."""
    
    def test_create_session(self, auth_headers):
        """Test creating a new conversation session."""
        payload = {
            "title": "Test Conversation",
            "metadata": {"topic": "AI research"}
        }
        
        response = client.post(
            "/api/v1/conversations/",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["title"] == "Test Conversation"
        assert "created_at" in data
    
    def test_list_sessions(self, auth_headers):
        """Test listing conversation sessions."""
        response = client.get(
            "/api/v1/conversations/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert "total_count" in data
        assert isinstance(data["sessions"], list)
    
    def test_get_session(self, auth_headers):
        """Test getting specific session."""
        session_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/conversations/{session_id}",
            headers=auth_headers
        )
        
        # Expecting 404 since session doesn't exist
        assert response.status_code == 404


class TestConversationMessages:
    """Test conversation messaging."""
    
    def test_send_message(self, auth_headers):
        """Test sending a message in conversation."""
        session_id = str(uuid.uuid4())
        payload = {
            "message": "What is machine learning?",
            "metadata": {"intent": "question"}
        }
        
        response = client.post(
            f"/api/v1/conversations/{session_id}/messages",
            json=payload,
            headers=auth_headers
        )
        
        # May return 404 if session doesn't exist
        assert response.status_code in [200, 404]
    
    def test_get_messages(self, auth_headers):
        """Test getting conversation messages."""
        session_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/conversations/{session_id}/messages",
            headers=auth_headers
        )
        
        # May return 404 if session doesn't exist
        assert response.status_code in [200, 404]


if __name__ == "__main__":
    pytest.main([__file__])
