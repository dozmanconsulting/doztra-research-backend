#!/bin/bash

# First, get an access token through the Netlify proxy
echo "Getting access token through Netlify proxy..."
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-ai.netlify.app/api/auth/login)

echo "Token response:"
echo $TOKEN_RESPONSE

# Extract the token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token. Response:"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo "Access token obtained successfully."

# Test research projects endpoint with auth token through Netlify proxy
echo -e "\nTesting research projects endpoint with auth through Netlify proxy..."
curl -i -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-ai.netlify.app/api/research/projects/

# Test research content generate-section endpoint with auth token through Netlify proxy
echo -e "\n\nTesting research content generate-section endpoint with auth through Netlify proxy..."
curl -i -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"project_id": "test-id", "section_title": "Introduction"}' \
  https://doztra-ai.netlify.app/api/research/content/generate-section
