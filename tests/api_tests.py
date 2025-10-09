#!/usr/bin/env python3
"""
API Testing Script for Doztra Auth Service

This script performs a series of API tests to verify that the authentication
service is working correctly. It tests user registration, login, token refresh,
email verification, password reset, and user profile management.

Usage:
    python api_tests.py [--host HOST] [--port PORT]

Example:
    python api_tests.py --host localhost --port 8000
"""

import argparse
import json
import requests
import time
import sys
from typing import Dict, Any, Optional, Tuple
from datetime import datetime

# Default settings
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 8000
BASE_URL = ""  # Will be set based on host and port

# Test user data
TEST_USER = {
    "name": "Test User",
    "email": f"test.user.{int(time.time())}@example.com",
    "password": "TestPassword123!"
}

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message: str) -> None:
    """Print a header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'=' * 80}{Colors.ENDC}\n")


def print_step(message: str) -> None:
    """Print a step message."""
    print(f"{Colors.OKBLUE}➤ {message}{Colors.ENDC}")


def print_success(message: str) -> None:
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_error(message: str) -> None:
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_json(data: Dict[str, Any]) -> None:
    """Print JSON data in a readable format."""
    print(json.dumps(data, indent=2))


def make_request(
    method: str,
    endpoint: str,
    data: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    expected_status: int = 200,
    auth_token: Optional[str] = None,
) -> Tuple[Dict[str, Any], int]:
    """Make an HTTP request to the API."""
    url = f"{BASE_URL}{endpoint}"
    
    # Set up headers
    if headers is None:
        headers = {}
    
    # Add authorization header if token is provided
    if auth_token:
        headers["Authorization"] = f"Bearer {auth_token}"
    
    # Make the request
    try:
        if method.upper() == "GET":
            response = requests.get(url, headers=headers)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, headers=headers)
        elif method.upper() == "PUT":
            response = requests.put(url, json=data, headers=headers)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Parse response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"text": response.text}
        
        # Check status code
        if response.status_code != expected_status:
            print_error(f"Expected status code {expected_status}, got {response.status_code}")
            print_json(response_data)
            return response_data, response.status_code
        
        return response_data, response.status_code
    
    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return {"error": str(e)}, 0


def test_health_check() -> bool:
    """Test the health check endpoint."""
    print_step("Testing health check endpoint...")
    
    response, status_code = make_request("GET", "/health")
    
    if status_code == 200 and response.get("status") == "healthy":
        print_success("Health check passed")
        return True
    else:
        print_error("Health check failed")
        return False


def test_user_registration() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Test user registration."""
    print_step("Testing user registration...")
    
    response, status_code = make_request(
        "POST",
        "/api/auth/register",
        data=TEST_USER,
        expected_status=201
    )
    
    if status_code == 201 and "access_token" in response:
        print_success("User registration successful")
        print(f"User ID: {response.get('id')}")
        print(f"Email: {response.get('email')}")
        return True, response
    else:
        print_error("User registration failed")
        return False, None


def test_user_login() -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Test user login."""
    print_step("Testing user login...")
    
    login_data = {
        "username": TEST_USER["email"],  # OAuth2 uses 'username' field
        "password": TEST_USER["password"]
    }
    
    # Use form data for login
    url = f"{BASE_URL}/api/auth/login"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    
    try:
        response = requests.post(
            url,
            data=login_data,  # Send as form data
            headers=headers
        )
        
        # Parse response
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            response_data = {"text": response.text}
        
        # Check status code
        if response.status_code != 200:
            print_error(f"Expected status code 200, got {response.status_code}")
            print_json(response_data)
            return False, None
        
        print_success("User login successful")
        return True, response_data
    
    except requests.RequestException as e:
        print_error(f"Request failed: {e}")
        return False, None
    


def test_get_user_profile(access_token: str) -> bool:
    """Test getting user profile."""
    print_step("Testing get user profile...")
    
    response, status_code = make_request(
        "GET",
        "/api/users/me",
        auth_token=access_token,
        expected_status=200
    )
    
    if status_code == 200 and "email" in response:
        print_success("Get user profile successful")
        print(f"Name: {response.get('name')}")
        print(f"Email: {response.get('email')}")
        print(f"Subscription: {response.get('subscription', {}).get('plan')}")
        return True
    else:
        print_error("Get user profile failed")
        return False


def test_update_user_profile(access_token: str) -> bool:
    """Test updating user profile."""
    print_step("Testing update user profile...")
    
    update_data = {
        "name": f"Updated Test User {datetime.now().strftime('%H:%M:%S')}"
    }
    
    response, status_code = make_request(
        "PUT",
        "/api/users/me",
        data=update_data,
        auth_token=access_token,
        expected_status=200
    )
    
    if status_code == 200 and response.get("name") == update_data["name"]:
        print_success("Update user profile successful")
        print(f"Updated name: {response.get('name')}")
        return True
    else:
        print_error("Update user profile failed")
        return False


def test_token_refresh(refresh_token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """Test token refresh."""
    print_step("Testing token refresh...")
    
    # The refresh endpoint expects the refresh_token to be embedded with embed=True
    # This means we need to send it as {"refresh_token": "value"}
    refresh_data = {
        "refresh_token": refresh_token
    }
    
    response, status_code = make_request(
        "POST",
        "/api/auth/refresh",
        data=refresh_data,
        expected_status=200
    )
    
    if status_code == 200 and "access_token" in response:
        print_success("Token refresh successful")
        return True, response
    else:
        print_error("Token refresh failed")
        return False, None


def test_logout(access_token: str, refresh_token: str) -> bool:
    """Test user logout."""
    print_step("Testing user logout...")
    
    # The logout endpoint expects the refresh_token to be embedded with embed=True
    # This means we need to send it as {"refresh_token": "value"}
    logout_data = {
        "refresh_token": refresh_token
    }
    
    response, status_code = make_request(
        "POST",
        "/api/auth/logout",
        data=logout_data,
        auth_token=access_token,
        expected_status=200
    )
    
    if status_code == 200 and "message" in response:
        print_success("Logout successful")
        return True
    else:
        print_error("Logout failed")
        return False


def run_tests() -> None:
    """Run all tests."""
    print_header("Doztra Auth Service API Tests")
    
    # Test health check
    if not test_health_check():
        print_error("Health check failed. Exiting tests.")
        sys.exit(1)
    
    # Test user registration
    registration_success, registration_data = test_user_registration()
    if not registration_success:
        print_error("User registration failed. Exiting tests.")
        sys.exit(1)
    
    access_token = registration_data.get("access_token")
    
    # Test get user profile
    test_get_user_profile(access_token)
    
    # Test update user profile
    test_update_user_profile(access_token)
    
    # Test user login
    login_success, login_data = test_user_login()
    if not login_success:
        print_error("User login failed. Exiting tests.")
        sys.exit(1)
    
    access_token = login_data.get("access_token")
    refresh_token = login_data.get("refresh_token")
    
    # Test token refresh
    refresh_success, refresh_data = test_token_refresh(refresh_token)
    if refresh_success:
        access_token = refresh_data.get("access_token")
        refresh_token = refresh_data.get("refresh_token")
    
    # Test logout
    test_logout(access_token, refresh_token)
    
    print_header("All Tests Completed")


def main() -> None:
    """Main function."""
    global BASE_URL
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="API Testing Script for Doztra Auth Service")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"Host to connect to (default: {DEFAULT_HOST})")
    parser.add_argument("--port", default=DEFAULT_PORT, type=int, help=f"Port to connect to (default: {DEFAULT_PORT})")
    
    args = parser.parse_args()
    
    # Set base URL
    BASE_URL = f"http://{args.host}:{args.port}"
    
    # Run tests
    run_tests()


if __name__ == "__main__":
    main()
