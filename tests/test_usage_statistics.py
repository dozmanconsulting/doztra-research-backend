import pytest
from fastapi.testclient import TestClient


def test_read_usage_statistics(client, regular_user, user_headers):
    """Test getting usage statistics."""
    response = client.get("/api/usage/me", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "chat_messages" in data
    assert "plagiarism_checks" in data
    assert "prompts_generated" in data
    assert "tokens" in data
    
    assert data["chat_messages"]["used"] == 50
    assert data["plagiarism_checks"]["used"] == 5
    assert data["prompts_generated"]["used"] == 10
    assert data["tokens"]["used"] == 100000
    assert data["tokens"]["limit"] == 500000
    assert "reset_date" in data["tokens"]


def test_read_usage_statistics_alternative_endpoint(client, regular_user, user_headers):
    """Test getting usage statistics from the alternative endpoint."""
    response = client.get("/api/users/me/usage", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "chat_messages" in data
    assert "plagiarism_checks" in data
    assert "prompts_generated" in data
    assert "tokens" in data
    
    assert data["chat_messages"]["used"] == 50
    assert data["plagiarism_checks"]["used"] == 5
    assert data["prompts_generated"]["used"] == 10
    assert data["tokens"]["used"] == 100000
    assert data["tokens"]["limit"] == 500000
    assert "reset_date" in data["tokens"]
