#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL - production environment
BASE_URL="https://doztra-research.onrender.com"

# Function to print section headers
print_header() {
  echo -e "\n${YELLOW}=== $1 ===${NC}\n"
}

# Function to print response
print_response() {
  echo -e "${BLUE}Response:${NC}"
  echo "$1" | jq '.' || echo "$1"
  echo ""
}

# Get authentication token
get_auth_token() {
  print_header "1. Getting authentication token"
  
  AUTH_RESPONSE=$(curl -v -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=shedrack.aji@outlook.com&password=Password123!" \
    "${BASE_URL}/api/auth/login" 2>&1)
  
  echo "Authentication response:"
  echo "$AUTH_RESPONSE" | jq '.' || echo "$AUTH_RESPONSE"
  
  # Extract token using grep and cut (same as test_with_auth.sh)
  ACCESS_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
  
  if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}Failed to get authentication token${NC}"
    echo "Response: $AUTH_RESPONSE"
    exit 1
  fi
  
  echo -e "${GREEN}Authentication successful${NC}"
  echo "Token: $ACCESS_TOKEN"
  
  # Return the token
  echo $ACCESS_TOKEN
}

# Test GET /api/tokens/me endpoint
test_token_usage() {
  local token=$1
  print_header "2. Testing GET /api/tokens/me endpoint"
  
  RESPONSE=$(curl -v -X GET "${BASE_URL}/api/tokens/me" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" 2>&1)
  
  print_response "$RESPONSE"
  
  # Check if response contains expected fields
  if echo "$RESPONSE" | jq -e '.current_period' > /dev/null && \
     echo "$RESPONSE" | jq -e '.breakdown' > /dev/null && \
     echo "$RESPONSE" | jq -e '.models' > /dev/null; then
    echo -e "${GREEN}✓ Token usage endpoint test passed${NC}"
  else
    echo -e "${RED}✗ Token usage endpoint test failed${NC}"
  fi
}

# Test GET /api/tokens/me/history endpoint
test_token_usage_history() {
  local token=$1
  print_header "3. Testing GET /api/tokens/me/history endpoint"
  
  RESPONSE=$(curl -v -X GET "${BASE_URL}/api/tokens/me/history" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" 2>&1)
  
  print_response "$RESPONSE"
  
  # Check if response contains expected fields
  if echo "$RESPONSE" | jq -e '.history' > /dev/null && \
     echo "$RESPONSE" | jq -e '.total_records' > /dev/null; then
    echo -e "${GREEN}✓ Token usage history endpoint test passed${NC}"
  else
    echo -e "${RED}✗ Token usage history endpoint test failed${NC}"
  fi
  
  # Test with pagination parameters
  print_header "3.1. Testing GET /api/tokens/me/history with pagination"
  
  RESPONSE=$(curl -v -X GET "${BASE_URL}/api/tokens/me/history?page=1&per_page=2" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" 2>&1)
  
  print_response "$RESPONSE"
  
  # Check if pagination is working
  if echo "$RESPONSE" | jq -e '.current_page == 1' > /dev/null && \
     echo "$RESPONSE" | jq -e '.records_per_page == 2' > /dev/null; then
    echo -e "${GREEN}✓ Token usage history pagination test passed${NC}"
  else
    echo -e "${RED}✗ Token usage history pagination test failed${NC}"
  fi
}

# Test POST /api/tokens/me/track endpoint
test_track_token_usage() {
  local token=$1
  print_header "4. Testing POST /api/tokens/me/track endpoint"
  
  RESPONSE=$(curl -v -X POST "${BASE_URL}/api/tokens/me/track" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -d '{
      "request_type": "chat",
      "model": "gpt-4",
      "prompt_tokens": 200,
      "completion_tokens": 800,
      "total_tokens": 1000,
      "request_id": "test_request_123"
    }' 2>&1)
  
  print_response "$RESPONSE"
  
  # Check if response indicates success
  if echo "$RESPONSE" | jq -e '.success == true' > /dev/null; then
    echo -e "${GREEN}✓ Track token usage endpoint test passed${NC}"
  else
    echo -e "${RED}✗ Track token usage endpoint test failed${NC}"
  fi
}

# Test GET /api/tokens/admin/usage endpoint
test_admin_token_usage() {
  local token=$1
  print_header "5. Testing GET /api/tokens/admin/usage endpoint"
  
  RESPONSE=$(curl -v -X GET "${BASE_URL}/api/tokens/admin/usage" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" 2>&1)
  
  print_response "$RESPONSE"
  
  # Check if response contains expected fields
  if echo "$RESPONSE" | jq -e '.total_tokens' > /dev/null && \
     echo "$RESPONSE" | jq -e '.breakdown_by_day' > /dev/null; then
    echo -e "${GREEN}✓ Admin token usage endpoint test passed${NC}"
  else
    # Check if it's a permission error (which is expected for non-admin users)
    if echo "$RESPONSE" | jq -e '.detail' > /dev/null; then
      echo -e "${YELLOW}⚠ Admin token usage endpoint returned permission error (expected for non-admin users)${NC}"
    else
      echo -e "${RED}✗ Admin token usage endpoint test failed${NC}"
    fi
  fi
}

# Main function
main() {
  echo -e "${YELLOW}=== TOKEN USAGE API TEST ===${NC}"
  
  # Get authentication token
  TOKEN=$(get_auth_token)
  
  # Run tests
  test_token_usage "$TOKEN"
  test_token_usage_history "$TOKEN"
  test_track_token_usage "$TOKEN"
  test_admin_token_usage "$TOKEN"
  
  echo -e "\n${GREEN}=== TOKEN USAGE API TESTS COMPLETED ===${NC}"
}

# Run the main function
main
