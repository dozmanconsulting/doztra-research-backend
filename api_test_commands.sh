#!/bin/bash
# Doztra Auth Service API Test Commands
# This script contains curl commands to test all the API endpoints

# Set base URL
BASE_URL="http://localhost:8000/api"

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Doztra Auth Service API Test Commands ===${NC}"
echo "This script contains curl commands to test all the API endpoints"
echo "Make sure the server is running on http://localhost:8000"
echo ""

# ===================================
# Authentication Endpoints
# ===================================
echo -e "${GREEN}=== Authentication Endpoints ===${NC}"

# Login with admin credentials
echo -e "${BLUE}Login with admin credentials:${NC}"
echo "curl -X POST $BASE_URL/auth/login -d \"username=admin@doztra.ai&password=AdminPassword123!\" -H \"Content-Type: application/x-www-form-urlencoded\""
echo ""

# Login with test user credentials
echo -e "${BLUE}Login with test user credentials:${NC}"
echo "curl -X POST $BASE_URL/auth/login -d \"username=test@doztra.ai&password=TestPassword123!\" -H \"Content-Type: application/x-www-form-urlencoded\""
echo ""

# Register a new user
echo -e "${BLUE}Register a new user:${NC}"
echo "curl -X POST $BASE_URL/auth/register -H \"Content-Type: application/json\" -d '{
  \"email\": \"newuser@example.com\",
  \"name\": \"New User\",
  \"password\": \"NewUser123!\",
  \"role\": \"user\"
}'"
echo ""

# Register a new user with subscription information
echo -e "${BLUE}Register a new user with subscription information:${NC}"
echo "curl -X POST $BASE_URL/auth/register -H \"Content-Type: application/json\" -d '{
  \"email\": \"subscriber@example.com\",
  \"name\": \"Subscriber User\",
  \"password\": \"Subscriber123!\",
  \"role\": \"user\",
  \"subscription\": {
    \"plan\": \"basic\",
    \"payment_method_id\": \"pm_test_123456\"
  }
}'"
echo ""

# Refresh token
echo -e "${BLUE}Refresh token:${NC}"
echo "curl -X POST $BASE_URL/auth/refresh -H \"Content-Type: application/json\" -d '{
  \"refresh_token\": \"YOUR_REFRESH_TOKEN\"
}'"
echo ""

# Logout
echo -e "${BLUE}Logout:${NC}"
echo "curl -X POST $BASE_URL/auth/logout -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" -H \"Content-Type: application/json\" -d '{
  \"refresh_token\": \"YOUR_REFRESH_TOKEN\"
}'"
echo ""

# Request password reset
echo -e "${BLUE}Request password reset:${NC}"
echo "curl -X POST $BASE_URL/auth/password-reset -H \"Content-Type: application/json\" -d '{
  \"email\": \"user@example.com\"
}'"
echo ""

# Reset password
echo -e "${BLUE}Reset password:${NC}"
echo "curl -X POST $BASE_URL/auth/reset-password -H \"Content-Type: application/json\" -d '{
  \"token\": \"PASSWORD_RESET_TOKEN\",
  \"new_password\": \"NewPassword123!\"
}'"
echo ""

# ===================================
# User Endpoints
# ===================================
echo -e "${GREEN}=== User Endpoints ===${NC}"

# Get current user profile
echo -e "${BLUE}Get current user profile:${NC}"
echo "curl -X GET $BASE_URL/users/me -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Update current user profile
echo -e "${BLUE}Update current user profile:${NC}"
echo "curl -X PUT $BASE_URL/users/me -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" -H \"Content-Type: application/json\" -d '{
  \"name\": \"Updated Name\",
  \"email\": \"updated@example.com\"
}'"
echo ""

# Get user by ID
echo -e "${BLUE}Get user by ID:${NC}"
echo "curl -X GET $BASE_URL/users/USER_ID -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Update user subscription
echo -e "${BLUE}Update user subscription:${NC}"
echo "curl -X PUT $BASE_URL/users/me/subscription -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" -H \"Content-Type: application/json\" -d '{
  \"plan\": \"professional\",
  \"payment_method_id\": \"pm_test_123456\"
}'"
echo ""

# Get user subscription
echo -e "${BLUE}Get user subscription:${NC}"
echo "curl -X GET $BASE_URL/users/me/subscription -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Get user usage statistics
echo -e "${BLUE}Get user usage statistics:${NC}"
echo "curl -X GET $BASE_URL/users/me/usage -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# ===================================
# Token Usage Endpoints
# ===================================
echo -e "${GREEN}=== Token Usage Endpoints ===${NC}"

# Get token usage statistics
echo -e "${BLUE}Get token usage statistics:${NC}"
echo "curl -X GET $BASE_URL/tokens/me -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Get token usage history
echo -e "${BLUE}Get token usage history:${NC}"
echo "curl -X GET $BASE_URL/tokens/me/history -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Track token usage
echo -e "${BLUE}Track token usage:${NC}"
echo "curl -X POST $BASE_URL/tokens/me/track -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" -H \"Content-Type: application/json\" -d '{
  \"request_type\": \"chat\",
  \"model\": \"gpt-4\",
  \"prompt_tokens\": 100,
  \"completion_tokens\": 400,
  \"total_tokens\": 500,
  \"request_id\": \"test-request-123\"
}'"
echo ""

# Get admin token usage analytics
echo -e "${BLUE}Get admin token usage analytics:${NC}"
echo "curl -X GET $BASE_URL/tokens/admin/usage -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# ===================================
# User Preferences Endpoints
# ===================================
echo -e "${GREEN}=== User Preferences Endpoints ===${NC}"

# Get user preferences
echo -e "${BLUE}Get user preferences:${NC}"
echo "curl -X GET $BASE_URL/preferences/me -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Update user preferences
echo -e "${BLUE}Update user preferences:${NC}"
echo "curl -X PUT $BASE_URL/preferences/me -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" -H \"Content-Type: application/json\" -d '{
  \"theme\": \"dark\",
  \"notifications\": true,
  \"default_model\": \"gpt-3.5-turbo\"
}'"
echo ""

# ===================================
# Usage Statistics Endpoints
# ===================================
echo -e "${GREEN}=== Usage Statistics Endpoints ===${NC}"

# Get usage statistics
echo -e "${BLUE}Get usage statistics:${NC}"
echo "curl -X GET $BASE_URL/usage/me -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# ===================================
# Admin Endpoints
# ===================================
echo -e "${GREEN}=== Admin Endpoints ===${NC}"

# Get admin dashboard
echo -e "${BLUE}Get admin dashboard:${NC}"
echo "curl -X GET $BASE_URL/admin/dashboard -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Get all users
echo -e "${BLUE}Get all users:${NC}"
echo "curl -X GET \"$BASE_URL/admin/users?limit=10\" -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Get all users with filtering
echo -e "${BLUE}Get all users with filtering:${NC}"
echo "curl -X GET \"$BASE_URL/admin/users?filter_by=email&filter_value=user@example.com\" -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Get all users with sorting
echo -e "${BLUE}Get all users with sorting:${NC}"
echo "curl -X GET \"$BASE_URL/admin/users?sort_by=created_at&sort_desc=false\" -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Get user by ID (admin)
echo -e "${BLUE}Get user by ID (admin):${NC}"
echo "curl -X GET $BASE_URL/admin/users/USER_ID -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Create user (admin)
echo -e "${BLUE}Create user (admin):${NC}"
echo "curl -X POST $BASE_URL/admin/users -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" -H \"Content-Type: application/json\" -d '{
  \"email\": \"adminuser@example.com\",
  \"name\": \"Admin Created User\",
  \"password\": \"AdminCreated123!\",
  \"role\": \"user\",
  \"is_active\": true,
  \"is_verified\": true,
  \"subscription\": {
    \"plan\": \"basic\",
    \"payment_method_id\": \"pm_test_123456\"
  }
}'"
echo ""

# Update user status (admin)
echo -e "${BLUE}Update user status (admin):${NC}"
echo "curl -X PATCH $BASE_URL/admin/users/USER_ID/status -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\" -H \"Content-Type: application/json\" -d '{
  \"is_active\": true,
  \"is_verified\": true,
  \"role\": \"admin\"
}'"
echo ""

# Delete user (admin)
echo -e "${BLUE}Delete user (admin):${NC}"
echo "curl -X DELETE $BASE_URL/admin/users/USER_ID -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

# Get user statistics (admin)
echo -e "${BLUE}Get user statistics (admin):${NC}"
echo "curl -X GET $BASE_URL/admin/users/statistics -H \"Authorization: Bearer YOUR_ACCESS_TOKEN\""
echo ""

echo -e "${GREEN}=== End of API Test Commands ===${NC}"
echo "To use these commands, replace YOUR_ACCESS_TOKEN, YOUR_REFRESH_TOKEN, USER_ID, etc. with actual values."
echo "You can get an access token by logging in with the login command."
echo ""
echo "Example of setting the token as an environment variable:"
echo "export TOKEN=\"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...\""
echo "curl -X GET $BASE_URL/users/me -H \"Authorization: Bearer \$TOKEN\""
