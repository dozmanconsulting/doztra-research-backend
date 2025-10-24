"""
Test cases for Knowledge Base API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import json
import uuid
from datetime import datetime

from app.main import app
from app.db.session import get_db
from app.models.user import User
from app.services.auth import create_access_token


client = TestClient(app)


@pytest.fixture
def test_user():
    """Create a test user for authentication."""
    return {
        "id": str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "is_active": True,
        "is_verified": True
    }


@pytest.fixture
def auth_headers(test_user):
    """Create authentication headers for test requests."""
    token = create_access_token(data={"sub": test_user["email"]})
    return {"Authorization": f"Bearer {token}"}


class TestContentIngestion:
    """Test content ingestion endpoints."""
    
    def test_ingest_text_content(self, auth_headers):
        """Test text content ingestion."""
        payload = {
            "title": "Test Document",
            "content": "This is a test document for knowledge base ingestion.",
            "metadata": {"source": "test", "category": "documentation"}
        }
        
        response = client.post(
            "/api/v1/knowledge/ingest/text",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert data["status"] == "processing"
        assert "message" in data
    
    def test_ingest_file_content(self, auth_headers):
        """Test file upload ingestion."""
        test_file_content = b"This is a test PDF content"
        
        response = client.post(
            "/api/v1/knowledge/ingest/file",
            files={"file": ("test.pdf", test_file_content, "application/pdf")},
            data={"title": "Test PDF", "metadata": json.dumps({"type": "document"})},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert data["status"] == "processing"
    
    def test_ingest_url_content(self, auth_headers):
        """Test URL content ingestion."""
        response = client.post(
            "/api/v1/knowledge/ingest/url",
            data={
                "url": "https://example.com/article",
                "title": "Example Article",
                "metadata": json.dumps({"source": "web"})
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert data["status"] == "processing"
    
    def test_ingest_youtube_content(self, auth_headers):
        """Test YouTube content ingestion."""
        response = client.post(
            "/api/v1/knowledge/ingest/youtube",
            data={
                "video_url": "https://youtube.com/watch?v=example",
                "title": "Example Video",
                "metadata": json.dumps({"platform": "youtube"})
            },
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "content_id" in data
        assert data["status"] == "processing"


class TestKnowledgeQuery:
    """Test knowledge base query endpoints."""
    
    def test_query_knowledge_base(self, auth_headers):
        """Test RAG query functionality."""
        payload = {
            "query": "What is artificial intelligence?",
            "top_k": 5,
            "content_types": ["text", "file"]
        }
        
        response = client.post(
            "/api/v1/knowledge/query",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert "sources" in data
        assert "query" in data
        assert isinstance(data["sources"], list)
    
    def test_search_content(self, auth_headers):
        """Test vector similarity search."""
        params = {
            "query": "machine learning",
            "top_k": 10
        }
        
        response = client.get(
            "/api/v1/knowledge/search",
            params=params,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestContentManagement:
    """Test content management endpoints."""
    
    def test_list_content_items(self, auth_headers):
        """Test listing user's content items."""
        response = client.get(
            "/api/v1/knowledge/content",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_get_content_item(self, auth_headers):
        """Test getting specific content item."""
        # This would need a real content_id in practice
        content_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/knowledge/content/{content_id}",
            headers=auth_headers
        )
        
        # Expecting 404 since content doesn't exist
        assert response.status_code == 404
    
    def test_get_processing_status(self, auth_headers):
        """Test getting processing status."""
        content_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/knowledge/content/{content_id}/status",
            headers=auth_headers
        )
        
        # Expecting 404 since content doesn't exist
        assert response.status_code == 404


class TestErrorHandling:
    """Test error handling and validation."""
    
    def test_unauthorized_access(self):
        """Test access without authentication."""
        response = client.post("/api/v1/knowledge/ingest/text", json={})
        assert response.status_code == 401
    
    def test_invalid_content_type(self, auth_headers):
        """Test invalid content type in query."""
        payload = {
            "query": "test query",
            "content_types": ["invalid_type"]
        }
        
        response = client.post(
            "/api/v1/knowledge/query",
            json=payload,
            headers=auth_headers
        )
        
        # Should handle gracefully or return validation error
        assert response.status_code in [200, 422]
    
    def test_empty_query(self, auth_headers):
        """Test empty query string."""
        payload = {"query": ""}
        
        response = client.post(
            "/api/v1/knowledge/query",
            json=payload,
            headers=auth_headers
        )
        
        # Should return validation error
        assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__])
