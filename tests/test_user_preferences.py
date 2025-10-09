import pytest
from fastapi.testclient import TestClient


def test_read_user_preferences(client, regular_user, user_headers):
    """Test getting user preferences."""
    response = client.get("/api/preferences/me", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "light"
    assert data["notifications"] is True
    assert data["default_model"] == "gpt-4"
    assert data["user_id"] == regular_user.id


def test_update_user_preferences(client, regular_user, user_headers):
    """Test updating user preferences."""
    response = client.put(
        "/api/preferences/me",
        json={
            "theme": "dark",
            "notifications": False,
            "default_model": "gpt-3.5-turbo"
        },
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"
    assert data["notifications"] is False
    assert data["default_model"] == "gpt-3.5-turbo"
    
    # Verify the changes were saved
    get_response = client.get("/api/preferences/me", headers=user_headers)
    get_data = get_response.json()
    assert get_data["theme"] == "dark"
    assert get_data["notifications"] is False
    assert get_data["default_model"] == "gpt-3.5-turbo"


def test_update_user_preferences_partial(client, regular_user, user_headers):
    """Test updating only some user preferences."""
    response = client.put(
        "/api/preferences/me",
        json={"theme": "dark"},
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["theme"] == "dark"
    assert data["notifications"] is True  # Unchanged
    assert data["default_model"] == "gpt-4"  # Unchanged


def test_update_user_preferences_unauthorized_model(client, regular_user, user_headers, monkeypatch):
    """Test updating user preferences with an unauthorized model."""
    # Mock the subscription check to enforce model tier restrictions
    def mock_check(*args, **kwargs):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Your subscription does not allow access to gpt-4-turbo")
    
    # Apply the monkeypatch
    import app.services.user_preferences
    monkeypatch.setattr("app.services.user_preferences.check_model_access", mock_check)
    
    response = client.put(
        "/api/preferences/me",
        json={"default_model": "gpt-4-turbo"},  # User only has access to gpt-4
        headers=user_headers
    )
    
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data
