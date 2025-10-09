import pytest
from fastapi.testclient import TestClient


def test_read_token_usage(client, regular_user, user_headers):
    """Test getting token usage statistics."""
    response = client.get("/api/tokens/me", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "current_period" in data
    assert "breakdown" in data
    assert "models" in data
    assert "daily_usage" in data
    
    assert data["current_period"]["tokens_used"] > 0
    assert data["current_period"]["tokens_limit"] == 500000
    
    assert "chat" in data["breakdown"]
    assert data["breakdown"]["chat"]["total_tokens"] > 0


def test_read_token_usage_history(client, regular_user, user_headers):
    """Test getting token usage history."""
    response = client.get("/api/tokens/me/history", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total_records" in data
    assert "total_pages" in data
    assert "current_page" in data
    assert "records_per_page" in data
    assert "history" in data
    
    assert data["total_records"] == 5  # From our fixture
    assert len(data["history"]) == 5
    assert data["history"][0]["request_type"] == "chat"
    assert data["history"][0]["model"] == "gpt-4"
    assert data["history"][0]["total_tokens"] == 500


def test_track_token_usage(client, regular_user, user_headers):
    """Test tracking token usage."""
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "chat",
            "model": "gpt-4",
            "prompt_tokens": 200,
            "completion_tokens": 800,
            "total_tokens": 1000,
            "request_id": "test_request_123"
        },
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    assert "Token usage tracked successfully" in data["message"]
    assert "id" in data


def test_track_token_usage_unauthorized_model(client, regular_user, user_headers, monkeypatch):
    """Test tracking token usage with an unauthorized model."""
    # Mock the subscription check to enforce model tier restrictions
    def mock_check(*args, **kwargs):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Your subscription does not allow access to gpt-4-turbo")
    
    # Apply the monkeypatch
    import app.services.token_usage
    monkeypatch.setattr("app.services.token_usage.check_model_access", mock_check)
    
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "chat",
            "model": "gpt-4-turbo",  # User only has access to gpt-4
            "prompt_tokens": 200,
            "completion_tokens": 800,
            "total_tokens": 1000,
            "request_id": "test_request_123"
        },
        headers=user_headers
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


def test_admin_token_usage(client, admin_user, admin_headers):
    """Test admin endpoint for token usage analytics."""
    response = client.get("/api/tokens/admin/usage", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "total_tokens" in data
    assert "prompt_tokens" in data
    assert "completion_tokens" in data
    assert "breakdown_by_day" in data
    assert "breakdown_by_model" in data
    assert "breakdown_by_request_type" in data
    assert "active_users" in data
    assert "average_tokens_per_user" in data


def test_admin_token_usage_unauthorized(client, regular_user, user_headers):
    """Test that regular users cannot access admin token usage analytics."""
    response = client.get("/api/tokens/admin/usage", headers=user_headers)
    
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
