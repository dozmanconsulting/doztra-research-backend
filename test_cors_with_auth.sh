#!/bin/bash

# First, get an access token with the provided credentials
echo "Getting access token..."
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Extract the token using grep and cut
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token. Response:"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo "Access token obtained successfully."
echo "Token: ${ACCESS_TOKEN:0:15}..."

# Test CORS configuration with authentication
echo "Testing CORS configuration with authentication..."

# Test OPTIONS request with Origin header
echo "Sending OPTIONS request with Origin header..."
curl -v -X OPTIONS \
  -H "Origin: https://doztra-ai.netlify.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type" \
  https://doztra-research.onrender.com/api/research/projects/

echo -e "\n\nTesting actual GET request with Origin header and Authorization..."
curl -v -X GET \
  -H "Origin: https://doztra-ai.netlify.app" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/
