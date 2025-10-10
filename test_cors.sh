#!/bin/bash

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== TESTING CORS CONFIGURATION ===${NC}"

# Test OPTIONS request for the document query endpoint
echo -e "\n${YELLOW}1. Testing OPTIONS request for document query endpoint with Origin from doztra.ai...${NC}"
curl -v -X OPTIONS \
  -H "Origin: https://doztra.ai" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type" \
  https://doztra-research.onrender.com/api/documents/query

echo -e "\n\n${YELLOW}2. Testing OPTIONS request for document query endpoint with Origin from doztra-ai.netlify.app...${NC}"
curl -v -X OPTIONS \
  -H "Origin: https://doztra-ai.netlify.app" \
  -H "Access-Control-Request-Method: POST" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type" \
  https://doztra-research.onrender.com/api/documents/query

# Get token for actual request testing
echo -e "\n${YELLOW}3. Getting access token...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrackaji.aji@gmail.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Extract token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}Failed to get access token. Response:${NC}"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo -e "${GREEN}Access Token: ${ACCESS_TOKEN:0:20}...${NC}"

# Test actual POST request with Origin header
echo -e "\n${YELLOW}4. Testing actual POST request with Origin from doztra.ai...${NC}"
curl -v -X POST \
  -H "Origin: https://doztra.ai" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test query", "document_ids": []}' \
  https://doztra-research.onrender.com/api/documents/query

echo -e "\n\n${YELLOW}5. Testing actual POST request with Origin from doztra-ai.netlify.app...${NC}"
curl -v -X POST \
  -H "Origin: https://doztra-ai.netlify.app" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test query", "document_ids": []}' \
  https://doztra-research.onrender.com/api/documents/query

echo -e "\n\n${YELLOW}=== TEST COMPLETE ===${NC}"
