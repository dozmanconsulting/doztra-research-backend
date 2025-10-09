#!/usr/bin/env python3
"""
Test script for testing the Doztra API endpoints against the deployed backend.
"""

import requests
import os
import json
import sys
from datetime import datetime, timedelta
import time

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.auth import create_access_token
from app.models.user import UserRole

# Use the deployed endpoint
API_BASE_URL = "https://doztra-research-backend-gi8q.onrender.com"

def get_user_token():
    """Create a test user token"""
    return create_access_token(
        data={"sub": "test-user-id", "email": "test@example.com", "role": UserRole.USER},
        expires_delta=timedelta(minutes=30)
    )

def get_admin_token():
    """Create a test admin token"""
    return create_access_token(
        data={"sub": "admin-user-id", "email": "admin@example.com", "role": UserRole.ADMIN},
        expires_delta=timedelta(minutes=30)
    )

def test_get_academic_disciplines():
    """Test getting academic disciplines"""
    print("\n=== Testing Academic Disciplines ===")
    
    # Get user token
    user_token = get_user_token()
    
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
    print(f"Response: {response.text[:200]}...")  # Truncate long response
    
    # Check response
    if response.status_code == 200:
        data = response.json()
        
        # Check the structure of the response
        if isinstance(data, list):
            # If response is a list of items
            print(f"✅ Success: Received {len(data)} disciplines")
            
            # Sample a few disciplines
            sample_size = min(5, len(data))
            print(f"Sample of {sample_size} disciplines:")
            for i in range(sample_size):
                print(f"  - {data[i]}")
        elif "disciplines" in data:
            # If response is an object with disciplines key
            print(f"✅ Success: Received {len(data['disciplines'])} disciplines")
        else:
            # If response has another structure
            print("❌ Error: Unexpected response structure:", data)
    else:
        print(f"❌ Error: Status code {response.status_code}")
        print(f"Response: {response.text}")

def test_unauthorized_access():
    """Test unauthorized access to endpoints"""
    print("\n=== Testing Unauthorized Access ===")
    
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
        
        # Check response
        if response.status_code in [401, 403]:
            print(f"✅ Success: Unauthorized access properly rejected with status {response.status_code}")
        else:
            print(f"❌ Error: Expected 401 or 403, got {response.status_code}")

def run_tests():
    """Run all tests"""
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 50)
    
    # Run tests
    test_get_academic_disciplines()
    test_unauthorized_access()
    
    print("\n" + "=" * 50)
    print("All tests completed!")

if __name__ == "__main__":
    run_tests()
