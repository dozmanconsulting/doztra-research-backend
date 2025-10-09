"""
Test to verify that all routers are properly registered.
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_documents_router_registered():
    """Test that the documents router endpoints are registered."""
    client = TestClient(app)
    
    # Try to access the documents endpoint (should return 401 if registered)
    response = client.get("/api/documents")
    assert response.status_code == 401  # Unauthorized but registered
    
    # Try to access a non-existent endpoint (should return 404)
    response = client.get("/api/nonexistent")
    assert response.status_code == 404  # Not found


def test_chat_query_router_registered():
    """Test that the chat query endpoints are registered."""
    client = TestClient(app)
    
    # Try to access the chat query endpoint (should return 422 if registered)
    response = client.post("/api/chat/query", json={})
    assert response.status_code in [401, 422]  # Either unauthorized or validation error
    
    # Try to access the chat search endpoint (should return 422 if registered)
    response = client.post("/api/chat/search", json={})
    assert response.status_code in [401, 422]  # Either unauthorized or validation error
