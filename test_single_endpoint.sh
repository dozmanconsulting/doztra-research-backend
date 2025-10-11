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

# Get authentication token
get_auth_token() {
  print_header "Getting authentication token"
  
  # Make the request and store the response body
  AUTH_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=shedrack.aji@outlook.com&password=Password123!" \
    "${BASE_URL}/api/auth/login")
  
  echo "Authentication response:"
  echo "$AUTH_RESPONSE"
  
  # Extract token from response
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

# Test a specific endpoint
test_endpoint() {
  local token=$1
  local endpoint=$2
  local method=$3
  local data=$4
  
  print_header "Testing $method $endpoint"
  
  if [ "$method" = "GET" ]; then
    # Make the request and store the response body
    RESPONSE=$(curl -s -X GET "${BASE_URL}${endpoint}" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json")
  elif [ "$method" = "POST" ]; then
    # Make the request and store the response body
    RESPONSE=$(curl -s -X POST "${BASE_URL}${endpoint}" \
      -H "Authorization: Bearer $token" \
      -H "Content-Type: application/json" \
      -d "$data")
  fi
  
  echo -e "${BLUE}Response:${NC}"
  echo "$RESPONSE"
  echo ""
}

# Main function
main() {
  echo -e "${YELLOW}=== SINGLE ENDPOINT TEST ===${NC}"
  
  # Get authentication token
  TOKEN=$(get_auth_token)
  
  # Choose which endpoint to test
  echo -e "\nWhich endpoint would you like to test?"
  echo "1. GET /api/tokens/me (Read Token Usage)"
  echo "2. GET /api/tokens/me/history (Read Token Usage History)"
  echo "3. POST /api/tokens/me/track (Track User Token Usage)"
  echo "4. GET /api/tokens/admin/usage (Admin Token Usage)"
  echo -n "Enter your choice (1-4): "
  read choice
  
  case $choice in
    1)
      test_endpoint "$TOKEN" "/api/tokens/me" "GET"
      ;;
    2)
      test_endpoint "$TOKEN" "/api/tokens/me/history" "GET"
      ;;
    3)
      data='{
        "request_type": "chat",
        "model": "gpt-4",
        "prompt_tokens": 200,
        "completion_tokens": 800,
        "total_tokens": 1000,
        "request_id": "test_request_123"
      }'
      test_endpoint "$TOKEN" "/api/tokens/me/track" "POST" "$data"
      ;;
    4)
      test_endpoint "$TOKEN" "/api/tokens/admin/usage" "GET"
      ;;
    *)
      echo -e "${RED}Invalid choice${NC}"
      exit 1
      ;;
  esac
  
  echo -e "\n${GREEN}=== TEST COMPLETED ===${NC}"
}

# Run the main function
main
