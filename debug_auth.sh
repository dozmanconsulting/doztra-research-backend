#!/bin/bash

# This script tests the authentication flow and checks for issues with the research projects API and token usage

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DOZTRA BACKEND DEBUG SCRIPT ===${NC}"
echo -e "${YELLOW}Testing authentication and API endpoints${NC}"
echo 

# Get access token
echo -e "${YELLOW}1. Getting access token...${NC}"
AUTH_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrackaji.aji@gmail.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Check if authentication was successful
if [[ $AUTH_RESPONSE == *"access_token"* ]]; then
  echo -e "${GREEN}Authentication successful!${NC}"
else
  echo -e "${RED}Authentication failed!${NC}"
  echo "Response: $AUTH_RESPONSE"
  exit 1
fi

# Extract tokens
ACCESS_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
REFRESH_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"refresh_token":"[^"]*"' | cut -d'"' -f4)

echo -e "${GREEN}Access Token (first 20 chars): ${ACCESS_TOKEN:0:20}...${NC}"
echo -e "${GREEN}Refresh Token (first 20 chars): ${REFRESH_TOKEN:0:20}...${NC}"

# Test user info endpoint
echo -e "\n${YELLOW}2. Testing /api/users/me endpoint...${NC}"
USER_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/users/me)

if [[ $USER_RESPONSE == *"id"* ]]; then
  echo -e "${GREEN}User info endpoint working!${NC}"
  echo "User data:"
  echo $USER_RESPONSE | jq
else
  echo -e "${RED}User info endpoint failed!${NC}"
  echo "Response: $USER_RESPONSE"
fi

# Test research projects endpoint
echo -e "\n${YELLOW}3. Testing /api/research/projects/ endpoint...${NC}"
PROJECTS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Origin: https://doztra-ai.netlify.app" \
  https://doztra-research.onrender.com/api/research/projects/)

if [[ $PROJECTS_RESPONSE == *"items"* ]]; then
  echo -e "${GREEN}Research projects endpoint working!${NC}"
  echo "Projects data:"
  echo $PROJECTS_RESPONSE | jq
else
  echo -e "${RED}Research projects endpoint failed!${NC}"
  echo "Response: $PROJECTS_RESPONSE"
  
  # Debug with verbose output
  echo -e "\n${YELLOW}Debugging research projects endpoint with verbose output...${NC}"
  curl -v -H "Authorization: Bearer $ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Origin: https://doztra-ai.netlify.app" \
    https://doztra-research.onrender.com/api/research/projects/
fi

# Test chat endpoint to check token usage
echo -e "\n${YELLOW}4. Testing chat endpoint to check token usage...${NC}"
CHAT_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, this is a test message","model":"gpt-3.5-turbo"}' \
  https://doztra-research.onrender.com/api/messages)

if [[ $CHAT_RESPONSE == *"content"* ]]; then
  echo -e "${GREEN}Chat endpoint working!${NC}"
  echo "Chat response:"
  echo $CHAT_RESPONSE | jq
else
  echo -e "${RED}Chat endpoint failed! This may be due to the token_usage timestamp issue.${NC}"
  echo "Response: $CHAT_RESPONSE"
fi

# Test refresh token endpoint
echo -e "\n${YELLOW}5. Testing refresh token endpoint...${NC}"
REFRESH_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d "{\"refresh_token\":\"$REFRESH_TOKEN\"}" \
  https://doztra-research.onrender.com/api/auth/refresh)

if [[ $REFRESH_RESPONSE == *"access_token"* ]]; then
  echo -e "${GREEN}Token refresh successful!${NC}"
  NEW_ACCESS_TOKEN=$(echo $REFRESH_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)
  echo -e "${GREEN}New Access Token (first 20 chars): ${NEW_ACCESS_TOKEN:0:20}...${NC}"
  
  # Test research projects with new token
  echo -e "\n${YELLOW}6. Testing /api/research/projects/ endpoint with new token...${NC}"
  NEW_PROJECTS_RESPONSE=$(curl -s -H "Authorization: Bearer $NEW_ACCESS_TOKEN" \
    -H "Content-Type: application/json" \
    -H "Origin: https://doztra-ai.netlify.app" \
    https://doztra-research.onrender.com/api/research/projects/)
  
  if [[ $NEW_PROJECTS_RESPONSE == *"items"* ]]; then
    echo -e "${GREEN}Research projects endpoint working with new token!${NC}"
    echo "Projects data:"
    echo $NEW_PROJECTS_RESPONSE | jq
  else
    echo -e "${RED}Research projects endpoint failed with new token!${NC}"
    echo "Response: $NEW_PROJECTS_RESPONSE"
  fi
else
  echo -e "${RED}Token refresh failed!${NC}"
  echo "Response: $REFRESH_RESPONSE"
fi

# Test creating a research project
echo -e "\n${YELLOW}7. Testing creating a new research project...${NC}"
CREATE_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Origin: https://doztra-ai.netlify.app" \
  -d '{
    "title": "Debug Test Project",
    "description": "Project created by debug script",
    "type": "general",
    "metadata": {
      "academic_level": "Undergraduate",
      "target_audience": "Students",
      "research_methodology": "Qualitative",
      "country": "United States"
    }
  }' \
  https://doztra-research.onrender.com/api/research/projects/)

if [[ $CREATE_RESPONSE == *"id"* ]]; then
  echo -e "${GREEN}Project creation successful!${NC}"
  echo "Project data:"
  echo $CREATE_RESPONSE | jq
  
  # Extract project ID for deletion test
  PROJECT_ID=$(echo $CREATE_RESPONSE | jq -r '.id')
  
  # Test deleting the project
  if [[ ! -z "$PROJECT_ID" ]]; then
    echo -e "\n${YELLOW}8. Testing deleting the project...${NC}"
    DELETE_RESPONSE=$(curl -s -X DELETE \
      -H "Authorization: Bearer $ACCESS_TOKEN" \
      https://doztra-research.onrender.com/api/research/projects/$PROJECT_ID)
    
    if [[ $DELETE_RESPONSE == *"success"* ]]; then
      echo -e "${GREEN}Project deletion successful!${NC}"
      echo "Response:"
      echo $DELETE_RESPONSE | jq
    else
      echo -e "${RED}Project deletion failed!${NC}"
      echo "Response: $DELETE_RESPONSE"
    fi
  fi
else
  echo -e "${RED}Project creation failed!${NC}"
  echo "Response: $CREATE_RESPONSE"
fi

echo -e "\n${YELLOW}=== DEBUG SCRIPT COMPLETED ===${NC}"
echo -e "${YELLOW}Check the results above to identify any issues${NC}"
