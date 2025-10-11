#!/bin/bash

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== TESTING GOOGLE OAUTH INTEGRATION ===${NC}"

# Base URL for the API
API_URL="https://doztra-research.onrender.com"
LOCAL_API_URL="http://localhost:8000"

# Check if we should use local API
if [ "$1" == "local" ]; then
  CURRENT_API_URL=$LOCAL_API_URL
  echo -e "${YELLOW}Using local API at ${LOCAL_API_URL}${NC}"
else
  CURRENT_API_URL=$API_URL
  echo -e "${YELLOW}Using production API at ${API_URL}${NC}"
fi

# 1. Test Google OAuth login URL
echo -e "\n${YELLOW}1. Testing Google OAuth login URL...${NC}"
LOGIN_URL_RESPONSE=$(curl -s -w "%{http_code}" "${CURRENT_API_URL}/api/auth/oauth/login/google")

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
CALLBACK_RESPONSE=$(curl -s -w "%{http_code}" "${CURRENT_API_URL}/api/auth/oauth/google/callback?code=invalid_code")

HTTP_CODE="${CALLBACK_RESPONSE: -3}"
RESPONSE_BODY="${CALLBACK_RESPONSE:0:${#CALLBACK_RESPONSE}-3}"

if [[ "$HTTP_CODE" == "400" ]]; then
  echo -e "${GREEN}Success! Received expected error response (HTTP 400)${NC}"
  echo "Response: $RESPONSE_BODY"
else
  echo -e "${RED}Failed! Expected HTTP 400, got ${HTTP_CODE}${NC}"
  echo "Response: $RESPONSE_BODY"
fi

# 3. Check environment variables
echo -e "\n${YELLOW}3. Checking environment variables...${NC}"
if [ -f .env ]; then
  if grep -q "GOOGLE_OAUTH_CLIENT_ID" .env && grep -q "GOOGLE_OAUTH_CLIENT_SECRET" .env; then
    echo -e "${GREEN}Google OAuth environment variables found in .env file${NC}"
    
    # Check if they are set to default values
    if grep -q "GOOGLE_OAUTH_CLIENT_ID=your-client-id-here" .env; then
      echo -e "${RED}Warning: Google OAuth client ID is set to default value${NC}"
      echo -e "${YELLOW}Please update it with your actual Google OAuth client ID${NC}"
    fi
    
    if grep -q "GOOGLE_OAUTH_CLIENT_SECRET=your-client-secret-here" .env; then
      echo -e "${RED}Warning: Google OAuth client secret is set to default value${NC}"
      echo -e "${YELLOW}Please update it with your actual Google OAuth client secret${NC}"
    fi
  else
    echo -e "${RED}Google OAuth environment variables not found in .env file${NC}"
    echo -e "${YELLOW}Please run deploy_google_auth.sh to set up the environment variables${NC}"
  fi
else
  echo -e "${RED}.env file not found${NC}"
  echo -e "${YELLOW}Please run deploy_google_auth.sh to create the .env file${NC}"
fi

echo -e "\n${YELLOW}=== GOOGLE OAUTH TEST COMPLETED ===${NC}"
echo -e "${YELLOW}Note: Full OAuth flow testing requires browser interaction${NC}"
echo -e "${YELLOW}To test the complete flow, visit:${NC}"
echo -e "${GREEN}${CURRENT_API_URL}/api/auth/oauth/login/google${NC}"
