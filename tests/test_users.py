import pytest
from fastapi.testclient import TestClient


def test_read_current_user(client, regular_user, user_headers):
    """Test getting the current user profile."""
    response = client.get("/api/users/me", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["name"] == "Regular User"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert data["is_verified"] is True
    assert "subscription" in data
    assert data["subscription"]["plan"] == "basic"


def test_read_current_user_unauthorized(client):
    """Test getting the current user profile without authentication."""
    response = client.get("/api/users/me")
    
    assert response.status_code == 401
    data = response.json()
    assert "detail" in data


def test_update_current_user(client, regular_user, user_headers):
    """Test updating the current user profile."""
    response = client.put(
        "/api/users/me",
        json={"name": "Updated User Name"},
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated User Name"
    assert data["email"] == "user@example.com"  # Unchanged


def test_update_current_user_email(client, regular_user, user_headers):
    """Test updating the current user's email."""
    response = client.put(
        "/api/users/me",
        json={"email": "updated@example.com"},
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "updated@example.com"
    assert data["name"] == "Regular User"  # Unchanged


def test_update_current_user_password(client, regular_user, user_headers):
    """Test updating the current user's password."""
    response = client.put(
        "/api/users/me",
        json={"password": "NewPassword123!"},
        headers=user_headers
    )
    
    assert response.status_code == 200
    
    # Try logging in with the new password
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": "user@example.com",
            "password": "NewPassword123!"
        }
    )
    
    assert login_response.status_code == 200
    assert "access_token" in login_response.json()


def test_get_user_by_id(client, regular_user, user_headers):
    """Test getting a user by ID."""
    response = client.get(f"/api/users/{regular_user.id}", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == regular_user.id
    assert data["email"] == "user@example.com"
    assert data["name"] == "Regular User"


def test_get_user_by_id_not_self(client, regular_user, admin_user, user_headers):
    """Test that a user cannot access another user's profile."""
    response = client.get(f"/api/users/{admin_user.id}", headers=user_headers)
    
    assert response.status_code == 403
    data = response.json()
    assert "detail" in data


def test_update_user_subscription(client, regular_user, user_headers):
    """Test updating a user's subscription."""
    response = client.put(
        "/api/users/me/subscription",
        json={
            "plan": "professional",
            "payment_method_id": "pm_test_123456"
        },
        headers=user_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["subscription"]["plan"] == "professional"
    assert data["subscription"]["payment_method_id"] == "pm_test_123456"


def test_get_user_subscription(client, regular_user, user_headers):
    """Test getting a user's subscription details."""
    response = client.get("/api/users/me/subscription", headers=user_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["plan"] == "basic"
    assert data["status"] == "active"
    assert data["is_active"] is True
    assert data["auto_renew"] is True
    assert data["token_limit"] == 500000
    assert data["max_model_tier"] == "gpt-4"


def test_get_user_usage(client, regular_user, user_headers):
    """Test getting a user's usage statistics."""
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
