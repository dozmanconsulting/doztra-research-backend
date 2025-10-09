import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
from app.services.auth import create_access_token
from app.models.user import UserRole

client = TestClient(app)


@pytest.fixture
def user_token():
    """Create a test user token"""
    return create_access_token(
        data={"sub": "test-user-id", "email": "test@example.com", "role": "USER"}
    )


@pytest.fixture
def admin_token():
    """Create a test admin token"""
    return create_access_token(
        data={"sub": "admin-user-id", "email": "admin@example.com", "role": "ADMIN"}
    )


def test_get_academic_disciplines(user_token):
    """Test getting academic disciplines"""
    response = client.get(
        "/api/research/options/academic-disciplines",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("value" in item and "label" in item for item in data)
    # Check for specific disciplines
    values = [item["value"] for item in data]
    assert "computer_science" in values
    assert "medicine" in values
    assert "psychology" in values


def test_get_academic_levels(user_token):
    """Test getting academic levels"""
    response = client.get(
        "/api/research/options/academic-levels",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("value" in item and "label" in item for item in data)
    # Check for specific levels
    values = [item["value"] for item in data]
    assert "undergraduate" in values
    assert "masters" in values
    assert "doctoral" in values


def test_get_target_audiences(user_token):
    """Test getting target audiences"""
    response = client.get(
        "/api/research/options/target-audiences",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("value" in item and "label" in item for item in data)
    # Check for specific audiences
    values = [item["value"] for item in data]
    assert "researchers" in values
    assert "students" in values
    assert "general_public" in values


def test_get_research_methodologies(user_token):
    """Test getting research methodologies"""
    response = client.get(
        "/api/research/options/research-methodologies",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("value" in item and "label" in item for item in data)
    # Check for specific methodologies
    values = [item["value"] for item in data]
    assert "qualitative" in values
    assert "quantitative" in values
    assert "mixed_methods" in values


def test_get_countries(user_token):
    """Test getting countries"""
    response = client.get(
        "/api/research/options/countries",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert all("value" in item and "label" in item for item in data)
    # Check for specific countries
    values = [item["value"] for item in data]
    assert "us" in values
    assert "uk" in values
    assert "ca" in values


def test_unauthorized_access():
    """Test unauthorized access to endpoints"""
    endpoints = [
        "/api/research/options/academic-disciplines",
        "/api/research/options/academic-levels",
        "/api/research/options/target-audiences",
        "/api/research/options/research-methodologies",
        "/api/research/options/countries"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401
        assert "detail" in response.json()


def test_admin_access(admin_token):
    """Test that admin users can access the endpoints"""
    endpoints = [
        "/api/research/options/academic-disciplines",
        "/api/research/options/academic-levels",
        "/api/research/options/target-audiences",
        "/api/research/options/research-methodologies",
        "/api/research/options/countries"
    ]
    
    for endpoint in endpoints:
        response = client.get(
            endpoint,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0


@patch('app.api.routes.research_options.get_db')
def test_database_error_handling(mock_get_db, user_token):
    """Test error handling when database connection fails"""
    # Setup mock to simulate database error
    mock_db = MagicMock()
    mock_db.query.side_effect = Exception("Database connection error")
    mock_get_db.return_value = mock_db
    
    # Test endpoint with simulated database error
    response = client.get(
        "/api/research/options/academic-disciplines",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    
    # Even with DB error, the endpoint should return default options
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0


@patch('app.services.auth.verify_token')
def test_expired_token(mock_verify_token):
    """Test behavior with expired token"""
    # Setup mock to simulate expired token
    mock_verify_token.side_effect = Exception("Token has expired")
    
    response = client.get(
        "/api/research/options/academic-disciplines",
        headers={"Authorization": "Bearer expired_token"}
    )
    
    assert response.status_code == 401
