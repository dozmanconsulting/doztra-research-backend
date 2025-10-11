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
  echo "$1"
  echo ""
}

# Get authentication token
get_auth_token() {
  print_header "1. Getting authentication token"
  
  # Use a temporary file to store the response headers
  HEADER_FILE=$(mktemp)
  
  # Make the request and store the response body
  AUTH_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=shedrack.aji@outlook.com&password=Password123!" \
    -D "$HEADER_FILE" \
    "${BASE_URL}/api/auth/login")
  
  echo "Authentication response:"
  echo "$AUTH_RESPONSE"
  
  # Extract token from response
  ACCESS_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
  
  if [ -z "$ACCESS_TOKEN" ]; then
    echo -e "${RED}Failed to get authentication token${NC}"
    echo "Response: $AUTH_RESPONSE"
    echo "Headers:"
    cat "$HEADER_FILE"
    rm "$HEADER_FILE"
    exit 1
  fi
  
  echo -e "${GREEN}Authentication successful${NC}"
  echo "Token: $ACCESS_TOKEN"
  
  # Clean up
  rm "$HEADER_FILE"
  
  # Return the token
  echo $ACCESS_TOKEN
}

# Test GET /api/tokens/me endpoint
test_token_usage() {
  local token=$1
  print_header "2. Testing GET /api/tokens/me endpoint"
  
  # Use a temporary file to store the response headers
  HEADER_FILE=$(mktemp)
  
  # Make the request and store the response body
  RESPONSE=$(curl -s -X GET "${BASE_URL}/api/tokens/me" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -D "$HEADER_FILE")
  
  print_response "$RESPONSE"
  
  # Print headers for debugging
  echo "Headers:"
  cat "$HEADER_FILE"
  
  # Check if response contains expected fields
  if echo "$RESPONSE" | grep -q "current_period" && \
     echo "$RESPONSE" | grep -q "breakdown" && \
     echo "$RESPONSE" | grep -q "models"; then
    echo -e "${GREEN}✓ Token usage endpoint test passed${NC}"
  else
    echo -e "${RED}✗ Token usage endpoint test failed${NC}"
  fi
  
  # Clean up
  rm "$HEADER_FILE"
}

# Test GET /api/tokens/me/history endpoint
test_token_usage_history() {
  local token=$1
  print_header "3. Testing GET /api/tokens/me/history endpoint"
  
  # Use a temporary file to store the response headers
  HEADER_FILE=$(mktemp)
  
  # Make the request and store the response body
  RESPONSE=$(curl -s -X GET "${BASE_URL}/api/tokens/me/history" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -D "$HEADER_FILE")
  
  print_response "$RESPONSE"
  
  # Print headers for debugging
  echo "Headers:"
  cat "$HEADER_FILE"
  
  # Check if response contains expected fields
  if echo "$RESPONSE" | grep -q "history" && \
     echo "$RESPONSE" | grep -q "total_records"; then
    echo -e "${GREEN}✓ Token usage history endpoint test passed${NC}"
  else
    echo -e "${RED}✗ Token usage history endpoint test failed${NC}"
  fi
  
  # Test with pagination parameters
  print_header "3.1. Testing GET /api/tokens/me/history with pagination"
  
  # Use a temporary file to store the response headers
  HEADER_FILE=$(mktemp)
  
  # Make the request and store the response body
  RESPONSE=$(curl -s -X GET "${BASE_URL}/api/tokens/me/history?page=1&per_page=2" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -D "$HEADER_FILE")
  
  print_response "$RESPONSE"
  
  # Print headers for debugging
  echo "Headers:"
  cat "$HEADER_FILE"
  
  # Check if pagination is working
  if echo "$RESPONSE" | grep -q "current_page" && \
     echo "$RESPONSE" | grep -q "records_per_page"; then
    echo -e "${GREEN}✓ Token usage history pagination test passed${NC}"
  else
    echo -e "${RED}✗ Token usage history pagination test failed${NC}"
  fi
  
  # Clean up
  rm "$HEADER_FILE"
}

# Test POST /api/tokens/me/track endpoint
test_track_token_usage() {
  local token=$1
  print_header "4. Testing POST /api/tokens/me/track endpoint"
  
  # Use a temporary file to store the response headers
  HEADER_FILE=$(mktemp)
  
  # Make the request and store the response body
  RESPONSE=$(curl -s -X POST "${BASE_URL}/api/tokens/me/track" \
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
    -D "$HEADER_FILE")
  
  print_response "$RESPONSE"
  
  # Print headers for debugging
  echo "Headers:"
  cat "$HEADER_FILE"
  
  # Check if response indicates success
  if echo "$RESPONSE" | grep -q "success"; then
    echo -e "${GREEN}✓ Track token usage endpoint test passed${NC}"
  else
    echo -e "${RED}✗ Track token usage endpoint test failed${NC}"
  fi
  
  # Clean up
  rm "$HEADER_FILE"
}

# Test GET /api/tokens/admin/usage endpoint
test_admin_token_usage() {
  local token=$1
  print_header "5. Testing GET /api/tokens/admin/usage endpoint"
  
  # Use a temporary file to store the response headers
  HEADER_FILE=$(mktemp)
  
  # Make the request and store the response body
  RESPONSE=$(curl -s -X GET "${BASE_URL}/api/tokens/admin/usage" \
    -H "Authorization: Bearer $token" \
    -H "Content-Type: application/json" \
    -D "$HEADER_FILE")
  
  print_response "$RESPONSE"
  
  # Print headers for debugging
  echo "Headers:"
  cat "$HEADER_FILE"
  
  # Check if response contains expected fields
  if echo "$RESPONSE" | grep -q "total_tokens" && \
     echo "$RESPONSE" | grep -q "breakdown_by_day"; then
    echo -e "${GREEN}✓ Admin token usage endpoint test passed${NC}"
  else
    # Check if it's a permission error (which is expected for non-admin users)
    if echo "$RESPONSE" | grep -q "detail"; then
      echo -e "${YELLOW}⚠ Admin token usage endpoint returned permission error (expected for non-admin users)${NC}"
    else
      echo -e "${RED}✗ Admin token usage endpoint test failed${NC}"
    fi
  fi
  
  # Clean up
  rm "$HEADER_FILE"
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
