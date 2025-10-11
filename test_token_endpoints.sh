#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL - production environment
BASE_URL="https://doztra-research.onrender.com"

# Get authentication token - using the same approach as test_with_auth.sh
get_token() {
  echo -e "${YELLOW}Getting authentication token...${NC}"
  
  # First, get an access token with the provided credentials
  TOKEN_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=shedrack.aji@outlook.com&password=Password123!" \
    "${BASE_URL}/api/auth/login")
  
  # Extract the token using grep and cut (this is a simple approach, consider using jq for better JSON parsing)
  ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
  
  if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}Failed to get access token. Response:${NC}"
    echo $TOKEN_RESPONSE
    exit 1
  fi
  
  echo -e "${GREEN}Access token obtained successfully.${NC}"
  echo "Token: $ACCESS_TOKEN"
  echo ""
  
  # Return the token
  echo $ACCESS_TOKEN
}

# Test the token usage endpoints
test_token_endpoints() {
  local token=$1
  
  # 1. Test GET /api/tokens/me
  echo -e "${YELLOW}1. Testing GET /api/tokens/me (Read Token Usage)${NC}"
  curl -s -X GET \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    "${BASE_URL}/api/tokens/me" | jq '.' || echo "Failed to parse response"
  echo ""
  
  # 2. Test GET /api/tokens/me/history
  echo -e "${YELLOW}2. Testing GET /api/tokens/me/history (Read Token Usage History)${NC}"
  curl -s -X GET \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    "${BASE_URL}/api/tokens/me/history" | jq '.' || echo "Failed to parse response"
  echo ""
  
  # 3. Test POST /api/tokens/me/track
  echo -e "${YELLOW}3. Testing POST /api/tokens/me/track (Track User Token Usage)${NC}"
  curl -s -X POST \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d '{
      "request_type": "chat",
      "model": "gpt-4",
      "prompt_tokens": 200,
      "completion_tokens": 800,
      "total_tokens": 1000,
      "request_id": "test_request_123"
    }' \
    "${BASE_URL}/api/tokens/me/track" | jq '.' || echo "Failed to parse response"
  echo ""
  
  # 4. Test GET /api/tokens/admin/usage
  echo -e "${YELLOW}4. Testing GET /api/tokens/admin/usage (Admin Token Usage)${NC}"
  curl -s -X GET \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    "${BASE_URL}/api/tokens/admin/usage" | jq '.' || echo "Failed to parse response"
  echo ""
}

# Main function
main() {
  echo -e "${YELLOW}=== TOKEN USAGE API TEST ===${NC}"
  echo ""
  
  # Get authentication token
  TOKEN=$(get_token)
  
  # Test the token usage endpoints
  test_token_endpoints "$TOKEN"
  
  echo -e "${GREEN}=== TEST COMPLETED ===${NC}"
}

# Run the main function
main
