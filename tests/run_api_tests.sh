#!/bin/bash
# Doztra Auth Service API Test Runner
# This script runs tests against the API endpoints with actual commands

# Set base URL
BASE_URL="http://localhost:8000/api"

# Colors for better readability
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Doztra Auth Service API Test Runner ===${NC}"
echo "This script runs tests against the API endpoints"
echo "Make sure the server is running on http://localhost:8000"
echo ""

# Function to run a command and display the result
run_command() {
  local description=$1
  local command=$2
  
  echo -e "${BLUE}$description${NC}"
  echo "Command: $command"
  echo -e "${GREEN}Response:${NC}"
  eval $command
  echo ""
  echo "----------------------------------------------"
  echo ""
  # Sleep to avoid overwhelming the server
  sleep 1
}

# ===================================
# Authentication Endpoints
# ===================================
echo -e "${GREEN}=== Authentication Endpoints ===${NC}"

# Login with admin credentials
run_command "Login with admin credentials" "curl -s -X POST $BASE_URL/auth/login -d \"username=admin@doztra.ai&password=AdminPassword123!\" -H \"Content-Type: application/x-www-form-urlencoded\""

# Store the token from the admin login
ADMIN_TOKEN=$(curl -s -X POST $BASE_URL/auth/login -d "username=admin@doztra.ai&password=AdminPassword123!" -H "Content-Type: application/x-www-form-urlencoded" | grep -o '\"access_token\":\"[^\"]*\"' | cut -d':' -f2 | tr -d '\"')

# Login with test user credentials
run_command "Login with test user credentials" "curl -s -X POST $BASE_URL/auth/login -d \"username=test@doztra.ai&password=TestPassword123!\" -H \"Content-Type: application/x-www-form-urlencoded\""

# Store the token from the test user login
USER_TOKEN=$(curl -s -X POST $BASE_URL/auth/login -d "username=test@doztra.ai&password=TestPassword123!" -H "Content-Type: application/x-www-form-urlencoded" | grep -o '\"access_token\":\"[^\"]*\"' | cut -d':' -f2 | tr -d '\"')

# Register a new user
run_command "Register a new user" "curl -s -X POST $BASE_URL/auth/register -H \"Content-Type: application/json\" -d '{\"email\": \"newuser2@example.com\", \"name\": \"New User 2\", \"password\": \"NewUser123!\", \"role\": \"user\"}'"

# ===================================
# User Endpoints
# ===================================
echo -e "${GREEN}=== User Endpoints ===${NC}"

# Get current user profile (admin)
run_command "Get current user profile (admin)" "curl -s -X GET $BASE_URL/users/me -H \"Authorization: Bearer $ADMIN_TOKEN\""

# Get current user profile (test user)
run_command "Get current user profile (test user)" "curl -s -X GET $BASE_URL/users/me -H \"Authorization: Bearer $USER_TOKEN\""

# Update current user profile
run_command "Update current user profile" "curl -s -X PUT $BASE_URL/users/me -H \"Authorization: Bearer $USER_TOKEN\" -H \"Content-Type: application/json\" -d '{\"name\": \"Updated Test User\"}'"

# Get user subscription
run_command "Get user subscription" "curl -s -X GET $BASE_URL/users/me/subscription -H \"Authorization: Bearer $USER_TOKEN\""

# Get user usage statistics
run_command "Get user usage statistics" "curl -s -X GET $BASE_URL/users/me/usage -H \"Authorization: Bearer $USER_TOKEN\""

# ===================================
# Token Usage Endpoints
# ===================================
echo -e "${GREEN}=== Token Usage Endpoints ===${NC}"

# Track token usage
run_command "Track token usage" "curl -s -X POST $BASE_URL/tokens/me/track -H \"Authorization: Bearer $USER_TOKEN\" -H \"Content-Type: application/json\" -d '{\"request_type\": \"chat\", \"model\": \"gpt-4\", \"prompt_tokens\": 100, \"completion_tokens\": 400, \"total_tokens\": 500, \"request_id\": \"test-request-123\"}'"

# Get token usage statistics
run_command "Get token usage statistics" "curl -s -X GET $BASE_URL/tokens/me -H \"Authorization: Bearer $USER_TOKEN\""

# ===================================
# User Preferences Endpoints
# ===================================
echo -e "${GREEN}=== User Preferences Endpoints ===${NC}"

# Update user preferences
run_command "Update user preferences" "curl -s -X PUT $BASE_URL/preferences/me -H \"Authorization: Bearer $USER_TOKEN\" -H \"Content-Type: application/json\" -d '{\"theme\": \"dark\", \"notifications\": true, \"default_model\": \"gpt-3.5-turbo\"}'"

# Get user preferences
run_command "Get user preferences" "curl -s -X GET $BASE_URL/preferences/me -H \"Authorization: Bearer $USER_TOKEN\""

# ===================================
# Admin Endpoints
# ===================================
echo -e "${GREEN}=== Admin Endpoints ===${NC}"

# Get admin dashboard
run_command "Get admin dashboard" "curl -s -X GET $BASE_URL/admin/dashboard -H \"Authorization: Bearer $ADMIN_TOKEN\""

# Get all users
run_command "Get all users" "curl -s -X GET \"$BASE_URL/admin/users?limit=10\" -H \"Authorization: Bearer $ADMIN_TOKEN\""

# Get all users with filtering
run_command "Get all users with filtering (by email)" "curl -s -X GET \"$BASE_URL/admin/users?filter_by=email&filter_value=test\" -H \"Authorization: Bearer $ADMIN_TOKEN\""

# Get all users with sorting
run_command "Get all users with sorting (by created_at)" "curl -s -X GET \"$BASE_URL/admin/users?sort_by=created_at&sort_desc=false\" -H \"Authorization: Bearer $ADMIN_TOKEN\""

# Get user statistics (admin)
run_command "Get user statistics (admin)" "curl -s -X GET $BASE_URL/admin/users/statistics -H \"Authorization: Bearer $ADMIN_TOKEN\""

echo -e "${GREEN}=== End of API Tests ===${NC}"
echo "All tests completed successfully!"
