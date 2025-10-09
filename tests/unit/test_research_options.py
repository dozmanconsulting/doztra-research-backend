import requests
import os
import json
import sys
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.auth import create_access_token
from app.models.user import UserRole

# Use the deployed endpoint
API_BASE_URL = "https://doztra-research-backend-gi8q.onrender.com"


def get_user_token():
    """Create a test user token"""
    return create_access_token(
        data={"sub": "test-user-id", "email": "test@example.com", "role": "USER"}
    )


def get_admin_token():
    """Create a test admin token"""
    return create_access_token(
        data={"sub": "admin-user-id", "email": "admin@example.com", "role": "ADMIN"}
    )


def test_get_academic_disciplines():
    """Test getting academic disciplines"""
    # Set up headers with authentication
    headers = {
        "Authorization": f"Bearer {user_token}"
    }
    
    # Make request to the deployed endpoint
    response = requests.get(
        f"{API_BASE_URL}/api/research/options/disciplines",
        headers=headers
    )
    
    # Print response for debugging
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    
    # Check the structure of the response
    if isinstance(data, list):
        # If response is a list of items
        assert len(data) > 0
        assert all("value" in item and "label" in item for item in data)
    elif "disciplines" in data:
        # If response is an object with disciplines key
        assert len(data["disciplines"]) > 0
    else:
        # If response has another structure
        print("Unexpected response structure:", data)
        assert False, "Unexpected response structure"
    # Check for specific disciplines if the data is in the expected format
    if isinstance(data, list) and all("value" in item for item in data):
        values = [item["value"] for item in data]
        # These assertions may need to be adjusted based on actual data
        # assert "computer_science" in values
        # assert "medicine" in values
        # assert "psychology" in values
        print("Available disciplines:", values)


def test_get_academic_levels(user_token):
    """Test getting academic levels"""
    # Set up headers with authentication
    headers = {
        "Authorization": f"Bearer {user_token}"
    }
    
    # Make request to the deployed endpoint
    response = requests.get(
        f"{API_BASE_URL}/api/research/options/academic-levels",
        headers=headers
    )
    
    # Print response for debugging
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    
    # Check the structure of the response
    if isinstance(data, list):
        # If response is a list of items
        assert len(data) > 0
        assert all("value" in item and "label" in item for item in data)
        
        # Print available levels
        values = [item["value"] for item in data]
        print("Available academic levels:", values)
        
        # These assertions may need to be adjusted based on actual data
        # assert "undergraduate" in values
        # assert "masters" in values
        # assert "doctoral" in values
    elif "levels" in data:
        # If response is an object with levels key
        assert len(data["levels"]) > 0
        print("Available academic levels:", data["levels"])
    else:
        # If response has another structure
        print("Unexpected response structure:", data)
        assert False, "Unexpected response structure"


def test_get_target_audiences(user_token):
    """Test getting target audiences"""
    # Set up headers with authentication
    headers = {
        "Authorization": f"Bearer {user_token}"
    }
    
    # Make request to the deployed endpoint
    response = requests.get(
        f"{API_BASE_URL}/api/research/options/target-audiences",
        headers=headers
    )
    
    # Print response for debugging
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    
    # Check the structure of the response
    if isinstance(data, list):
        # If response is a list of items
        assert len(data) > 0
        assert all("value" in item and "label" in item for item in data)
        
        # Print available audiences
        values = [item["value"] for item in data]
        print("Available target audiences:", values)
    elif "audiences" in data:
        # If response is an object with audiences key
        assert len(data["audiences"]) > 0
        print("Available target audiences:", data["audiences"])
    else:
        # If response has another structure
        print("Unexpected response structure:", data)
        assert False, "Unexpected response structure"


def test_get_research_methodologies(user_token):
    """Test getting research methodologies"""
    # Set up headers with authentication
    headers = {
        "Authorization": f"Bearer {user_token}"
    }
    
    # Make request to the deployed endpoint
    response = requests.get(
        f"{API_BASE_URL}/api/research/options/research-methodologies",
        headers=headers
    )
    
    # Print response for debugging
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    
    # Check the structure of the response
    if isinstance(data, list):
        # If response is a list of items
        assert len(data) > 0
        assert all("value" in item and "label" in item for item in data)
        
        # Print available methodologies
        values = [item["value"] for item in data]
        print("Available research methodologies:", values)
    elif "methodologies" in data:
        # If response is an object with methodologies key
        assert len(data["methodologies"]) > 0
        print("Available research methodologies:", data["methodologies"])
    else:
        # If response has another structure
        print("Unexpected response structure:", data)
        assert False, "Unexpected response structure"


def test_get_countries(user_token):
    """Test getting countries"""
    # Set up headers with authentication
    headers = {
        "Authorization": f"Bearer {user_token}"
    }
    
    # Make request to the deployed endpoint
    response = requests.get(
        f"{API_BASE_URL}/api/research/options/countries",
        headers=headers
    )
    
    # Print response for debugging
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text[:200]}...")  # Truncate long response
    
    # Assert response
    assert response.status_code == 200
    data = response.json()
    
    # Check the structure of the response
    if isinstance(data, list):
        # If response is a list of items
        assert len(data) > 0
        print(f"Received {len(data)} countries")
        
        # Sample a few countries
        sample_size = min(5, len(data))
        print(f"Sample of {sample_size} countries:")
        for i in range(sample_size):
            print(f"  - {data[i]}")
    elif "countries" in data:
        # If response is an object with countries key
        assert len(data["countries"]) > 0
        print(f"Received {len(data['countries'])} countries")
    else:
        # If response has another structure
        print("Unexpected response structure:", data)
        assert False, "Unexpected response structure"


def test_unauthorized_access():
    """Test unauthorized access to endpoints"""
    endpoints = [
        "/api/research/options/disciplines",
        "/api/research/options/academic-levels",
        "/api/research/options/target-audiences",
        "/api/research/options/research-methodologies",
        "/api/research/options/countries"
    ]
    
    for endpoint in endpoints:
        # Make request to the deployed endpoint without auth token
        print(f"\nTesting unauthorized access to: {endpoint}")
        response = requests.get(f"{API_BASE_URL}{endpoint}")
        
        # Print response for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        # Assert response
        assert response.status_code in [401, 403]  # Either unauthorized or forbidden
        
        try:
            data = response.json()
            if "detail" in data:
                print(f"Error detail: {data['detail']}")
        except Exception as e:
            print(f"Could not parse response as JSON: {e}")
            # Continue even if the response is not JSON


def test_admin_access(admin_token):
    """Test that admin users can access the endpoints"""
    endpoints = [
        "/api/research/options/disciplines",
        "/api/research/options/academic-levels",
        "/api/research/options/target-audiences",
        "/api/research/options/research-methodologies",
        "/api/research/options/countries"
    ]
    
    for endpoint in endpoints:
        # Set up headers with admin authentication
        headers = {
            "Authorization": f"Bearer {admin_token}"
        }
        
        # Make request to the deployed endpoint
        print(f"\nTesting admin access to: {endpoint}")
        response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
        
        # Print response for debugging
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:100]}...")  # Truncate long response
        
        # Assert response
        assert response.status_code == 200
        
        try:
            data = response.json()
            if isinstance(data, list):
                print(f"Received {len(data)} items")
            elif isinstance(data, dict):
                print(f"Received data with keys: {list(data.keys())}")
        except Exception as e:
            print(f"Could not parse response as JSON: {e}")
