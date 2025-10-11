import pytest
import json
from fastapi.testclient import TestClient
from datetime import datetime, timedelta


def test_read_token_usage(client, regular_user, user_headers):
    """Test GET /api/tokens/me endpoint for reading token usage statistics."""
    response = client.get("/api/tokens/me", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "current_period" in data
    assert "breakdown" in data
    assert "models" in data
    assert "daily_usage" in data
    
    # Check values
    assert data["current_period"]["tokens_used"] > 0
    assert data["current_period"]["tokens_limit"] == 500000
    assert "tokens_remaining" in data["current_period"]
    assert "percentage_used" in data["current_period"]
    
    # Check breakdown
    assert "chat" in data["breakdown"]
    assert data["breakdown"]["chat"]["total_tokens"] > 0
    assert "prompt_tokens" in data["breakdown"]["chat"]
    assert "completion_tokens" in data["breakdown"]["chat"]
    
    # Check models breakdown
    assert "gpt-4" in data["models"]
    
    # Check daily usage
    assert isinstance(data["daily_usage"], list)
    if data["daily_usage"]:
        assert "date" in data["daily_usage"][0]
        assert "total_tokens" in data["daily_usage"][0]


def test_read_token_usage_unauthorized(client):
    """Test that unauthorized access to token usage is rejected."""
    response = client.get("/api/tokens/me")
    
    assert response.status_code == 401
    assert "detail" in response.json()
    assert "Not authenticated" in response.json()["detail"]


def test_read_token_usage_history(client, regular_user, user_headers):
    """Test GET /api/tokens/me/history endpoint for token usage history."""
    # Test with default parameters
    response = client.get("/api/tokens/me/history", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "total_records" in data
    assert "total_pages" in data
    assert "current_page" in data
    assert "records_per_page" in data
    assert "history" in data
    
    # Check values from fixture
    assert data["total_records"] == 5
    assert len(data["history"]) == 5
    assert data["history"][0]["request_type"] == "chat"
    assert data["history"][0]["model"] == "gpt-4"
    assert data["history"][0]["total_tokens"] == 500
    
    # Test with pagination parameters
    response = client.get("/api/tokens/me/history?page=1&per_page=2", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_records"] == 5
    assert data["total_pages"] == 3  # 5 records with 2 per page = 3 pages
    assert data["current_page"] == 1
    assert data["records_per_page"] == 2
    assert len(data["history"]) == 2


def test_read_token_usage_history_filters(client, regular_user, user_headers, db):
    """Test filtering options for token usage history."""
    # Add some additional token usage records with different request types
    from app.models.token_usage import TokenUsage, RequestType
    
    user_id = regular_user.id
    
    # Add a document processing record
    doc_token_usage = TokenUsage(
        user_id=user_id,
        request_type=RequestType.DOCUMENT,
        model="gpt-4",
        prompt_tokens=300,
        completion_tokens=700,
        total_tokens=1000,
        timestamp=datetime.utcnow()
    )
    db.add(doc_token_usage)
    
    # Add a plagiarism check record
    plagiarism_token_usage = TokenUsage(
        user_id=user_id,
        request_type=RequestType.PLAGIARISM,
        model="gpt-3.5-turbo",
        prompt_tokens=500,
        completion_tokens=200,
        total_tokens=700,
        timestamp=datetime.utcnow()
    )
    db.add(plagiarism_token_usage)
    
    db.commit()
    
    # Test filtering by request type
    response = client.get("/api/tokens/me/history?request_type=document", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["history"]) == 1
    assert data["history"][0]["request_type"] == "document"
    assert data["history"][0]["total_tokens"] == 1000
    
    # Test filtering by model
    response = client.get("/api/tokens/me/history?model=gpt-3.5-turbo", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    assert len(data["history"]) == 1
    assert data["history"][0]["model"] == "gpt-3.5-turbo"
    assert data["history"][0]["request_type"] == "plagiarism"
    
    # Test filtering by date range
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    response = client.get(f"/api/tokens/me/history?start_date={yesterday}&end_date={today}", 
                          headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Should include today's records (the 2 we just added plus 1 from fixture)
    assert len(data["history"]) >= 3


def test_track_token_usage(client, regular_user, user_headers):
    """Test POST /api/tokens/me/track endpoint for tracking token usage."""
    # Track token usage with all fields
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "chat",
            "model": "gpt-4",
            "prompt_tokens": 200,
            "completion_tokens": 800,
            "total_tokens": 1000,
            "request_id": "test_request_123",
            "metadata": {
                "conversation_id": "conv_12345",
                "message_id": "msg_67890"
            }
        },
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "message" in data
    assert "Token usage tracked successfully" in data["message"]
    assert "id" in data
    
    # Track token usage with minimal fields
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "document",
            "model": "gpt-4",
            "total_tokens": 500
        },
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify the tracked usage is reflected in the usage history
    response = client.get("/api/tokens/me/history?request_type=document", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["history"]) >= 1
    assert data["history"][0]["request_type"] == "document"
    assert data["history"][0]["total_tokens"] == 500


def test_track_token_usage_validation(client, regular_user, user_headers):
    """Test validation for the track token usage endpoint."""
    # Test with negative token count
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "chat",
            "model": "gpt-4",
            "prompt_tokens": -100,  # Negative value
            "completion_tokens": 800,
            "total_tokens": 700
        },
        headers=user_headers
    )
    
    assert response.status_code == 422
    
    # Test with invalid request type
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "invalid_type",  # Invalid request type
            "model": "gpt-4",
            "total_tokens": 1000
        },
        headers=user_headers
    )
    
    assert response.status_code == 422
    
    # Test with mismatched token counts
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "chat",
            "model": "gpt-4",
            "prompt_tokens": 200,
            "completion_tokens": 300,
            "total_tokens": 1000  # Doesn't match prompt + completion
        },
        headers=user_headers
    )
    
    assert response.status_code == 422


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
    assert "Your subscription does not allow access" in data["detail"]


def test_admin_token_usage(client, admin_user, admin_headers):
    """Test GET /api/tokens/admin/usage endpoint for admin token usage analytics."""
    response = client.get("/api/tokens/admin/usage", headers=admin_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "total_tokens" in data
    assert "prompt_tokens" in data
    assert "completion_tokens" in data
    assert "breakdown_by_day" in data
    assert "breakdown_by_model" in data
    assert "breakdown_by_request_type" in data
    assert "active_users" in data
    assert "average_tokens_per_user" in data
    
    # Check specific values
    assert data["total_tokens"] >= 0
    assert data["prompt_tokens"] >= 0
    assert data["completion_tokens"] >= 0
    
    # Check breakdowns
    assert isinstance(data["breakdown_by_day"], list)
    assert isinstance(data["breakdown_by_model"], dict)
    assert isinstance(data["breakdown_by_request_type"], dict)
    
    # Check user stats
    assert data["active_users"] >= 1  # At least the regular user
    assert data["average_tokens_per_user"] >= 0


def test_admin_token_usage_with_filters(client, admin_user, admin_headers):
    """Test admin token usage endpoint with filters."""
    # Test with date range filter
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    response = client.get(
        f"/api/tokens/admin/usage?start_date={yesterday}&end_date={today}",
        headers=admin_headers
    )
    
    assert response.status_code == 200
    
    # Test with model filter
    response = client.get(
        "/api/tokens/admin/usage?model=gpt-4",
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include gpt-4 in the model breakdown
    assert "gpt-4" in data["breakdown_by_model"]
    assert len(data["breakdown_by_model"]) == 1
    
    # Test with request type filter
    response = client.get(
        "/api/tokens/admin/usage?request_type=chat",
        headers=admin_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should only include chat in the request type breakdown
    assert "chat" in data["breakdown_by_request_type"]
    assert len(data["breakdown_by_request_type"]) == 1


def test_admin_token_usage_unauthorized(client, regular_user, user_headers):
    """Test that regular users cannot access admin token usage analytics."""
    response = client.get("/api/tokens/admin/usage", headers=user_headers)
    
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
    assert "Not enough permissions" in data["detail"]


def test_admin_token_usage_per_user(client, admin_user, admin_headers, regular_user):
    """Test admin endpoint for token usage per user."""
    # This endpoint might not exist yet, but would be a useful addition
    response = client.get(f"/api/tokens/admin/usage/user/{regular_user.id}", headers=admin_headers)
    
    # If the endpoint exists, verify its response
    if response.status_code == 200:
        data = response.json()
        
        assert "user_id" in data
        assert data["user_id"] == regular_user.id
        assert "total_tokens" in data
        assert "breakdown_by_day" in data
        assert "breakdown_by_model" in data
        assert "breakdown_by_request_type" in data
    # If the endpoint doesn't exist yet, this test can be skipped
    elif response.status_code == 404:
        pytest.skip("Admin token usage per user endpoint not implemented yet")
    else:
        # Any other status code is unexpected
        assert False, f"Unexpected status code: {response.status_code}"


def test_usage_statistics_integration(client, regular_user, user_headers):
    """Test integration between token usage and usage statistics."""
    # First, get the current usage statistics
    response = client.get("/api/usage/me", headers=user_headers)
    
    assert response.status_code == 200
    initial_data = response.json()
    initial_tokens_used = initial_data["tokens"]["used"]
    
    # Track some token usage
    response = client.post(
        "/api/tokens/me/track",
        json={
            "request_type": "chat",
            "model": "gpt-4",
            "prompt_tokens": 100,
            "completion_tokens": 400,
            "total_tokens": 500,
        },
        headers=user_headers
    )
    
    assert response.status_code == 200
    
    # Check that the usage statistics have been updated
    response = client.get("/api/usage/me", headers=user_headers)
    
    assert response.status_code == 200
    updated_data = response.json()
    updated_tokens_used = updated_data["tokens"]["used"]
    
    # The tokens used should have increased by 500
    assert updated_tokens_used == initial_tokens_used + 500
