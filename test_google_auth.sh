#!/bin/bash

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DOZTRA GOOGLE OAUTH TEST SCRIPT ===${NC}"

# Base URL for the API
API_URL="https://doztra-research.onrender.com"

# 1. Test Google OAuth login URL
echo -e "\n${YELLOW}1. Testing Google OAuth login URL...${NC}"
LOGIN_URL_RESPONSE=$(curl -s -w "%{http_code}" "${API_URL}/api/auth/oauth/login/google")

HTTP_CODE="${LOGIN_URL_RESPONSE: -3}"
RESPONSE_BODY="${LOGIN_URL_RESPONSE:0:${#LOGIN_URL_RESPONSE}-3}"

if [[ "$HTTP_CODE" == "302" ]]; then
  echo -e "${GREEN}Success! Received redirect response (HTTP 302)${NC}"
  echo "This would redirect the user to the Google login page"
else
  echo -e "${RED}Failed! Expected HTTP 302, got ${HTTP_CODE}${NC}"
  echo "Response: $RESPONSE_BODY"
fi

# 2. Test OAuth callback with invalid code (should fail)
echo -e "\n${YELLOW}2. Testing OAuth callback with invalid code (should fail)...${NC}"
CALLBACK_RESPONSE=$(curl -s -w "%{http_code}" "${API_URL}/api/auth/oauth/google/callback?code=invalid_code")

HTTP_CODE="${CALLBACK_RESPONSE: -3}"
RESPONSE_BODY="${CALLBACK_RESPONSE:0:${#CALLBACK_RESPONSE}-3}"

if [[ "$HTTP_CODE" == "400" ]]; then
  echo -e "${GREEN}Success! Received expected error response (HTTP 400)${NC}"
  echo "Response: $RESPONSE_BODY"
else
  echo -e "${RED}Failed! Expected HTTP 400, got ${HTTP_CODE}${NC}"
  echo "Response: $RESPONSE_BODY"
fi

echo -e "\n${YELLOW}=== GOOGLE OAUTH TEST COMPLETED ===${NC}"
echo -e "${YELLOW}Note: Full OAuth flow testing requires browser interaction${NC}"
echo -e "${YELLOW}To test the complete flow, visit:${NC}"
echo -e "${GREEN}${API_URL}/api/auth/oauth/login/google${NC}"
