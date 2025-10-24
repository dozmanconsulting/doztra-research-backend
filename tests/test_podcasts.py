"""
Test cases for Podcast Generation API endpoints.
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


class TestPodcastGeneration:
    """Test podcast generation functionality."""
    
    def test_generate_podcast(self, auth_headers):
        """Test podcast generation request."""
        payload = {
            "title": "AI Research Podcast",
            "topic": "Latest developments in artificial intelligence",
            "knowledge_query": "artificial intelligence machine learning",
            "settings": {
                "duration_minutes": 10,
                "voice_settings": {
                    "voice_id": "default",
                    "speed": 1.0
                }
            }
        }
        
        response = client.post(
            "/api/v1/podcasts/generate",
            json=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "podcast_id" in data
        assert data["status"] == "processing"
    
    def test_list_podcasts(self, auth_headers):
        """Test listing user's podcasts."""
        response = client.get(
            "/api/v1/podcasts/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "podcasts" in data
        assert "total_count" in data
    
    def test_get_podcast(self, auth_headers):
        """Test getting specific podcast."""
        podcast_id = str(uuid.uuid4())
        
        response = client.get(
            f"/api/v1/podcasts/{podcast_id}",
            headers=auth_headers
        )
        
        # Expecting 404 since podcast doesn't exist
        assert response.status_code == 404
    
    def test_preview_script(self, auth_headers):
        """Test script preview generation."""
        payload = {
            "topic": "Machine Learning Basics",
            "knowledge_query": "machine learning fundamentals",
            "settings": json.dumps({"duration_minutes": 5})
        }
        
        response = client.post(
            "/api/v1/podcasts/preview-script",
            data=payload,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "script_preview" in data
        assert "estimated_duration" in data


if __name__ == "__main__":
    pytest.main([__file__])
