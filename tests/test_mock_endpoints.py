"""
Tests with mocked authentication to verify endpoint functionality.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

from app.main import app
from app.models.user import User, UserRole


@pytest.fixture
def mock_auth():
    """Mock the authentication dependency."""
    with patch('app.api.routes.documents.get_current_active_user') as mock_auth:
        # Create a mock user
        mock_user = MagicMock(spec=User)
        mock_user.id = str(uuid.uuid4())
        mock_user.email = "test@example.com"
        mock_user.role = UserRole.USER
        mock_auth.return_value = mock_user
        yield mock_auth


def test_documents_endpoints_with_mock_auth(mock_auth):
    """Test documents endpoints with mocked authentication."""
    client = TestClient(app)
    
    # Test list documents endpoint
    response = client.get("/api/documents")
    assert response.status_code == 200
    assert "documents" in response.json()
    
    # Test get document endpoint
    document_id = f"doc-{uuid.uuid4()}"
    response = client.get(f"/api/documents/{document_id}")
    assert response.status_code == 404  # Document not found, but endpoint works
    
    
def test_chat_query_endpoints_with_mock_auth(mock_auth):
    """Test chat query endpoints with mocked authentication."""
    client = TestClient(app)
    
    # Test query endpoint
    with patch('app.services.openai_service.query_with_documents') as mock_query:
        mock_query.return_value = {
            "answer": "Test response",
            "sources": [],
            "query": "test",
            "model": "gpt-4"
        }
        
        response = client.post(
            "/api/chat/query",
            json={
                "message": "test",
                "document_ids": [],
                "options": {}
            }
        )
        
        assert response.status_code == 200
        assert response.json()["answer"] == "Test response"
    
    # Test search endpoint
    with patch('app.services.openai_service.search_document_chunks') as mock_search:
        mock_search.return_value = []
        
        response = client.post(
            "/api/chat/search",
            json={
                "query": "test",
                "document_ids": [],
                "top_k": 5
            }
        )
        
        assert response.status_code == 200
        assert "results" in response.json()
