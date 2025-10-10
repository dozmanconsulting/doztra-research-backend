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

# Get a valid project ID
echo "Getting a valid project ID..."
PROJECT_RESPONSE=$(curl -s -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/)

# Extract the first project ID
PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$PROJECT_ID" ]; then
  echo "Failed to get a project ID. Response:"
  echo $PROJECT_RESPONSE
  exit 1
fi

echo "Using project ID: $PROJECT_ID"

# Test content generation with valid project ID
echo "Testing content generation with valid project ID..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"project_id\": \"$PROJECT_ID\", \"section_title\": \"Introduction\"}" \
  https://doztra-research.onrender.com/api/research/content/generate-section

# Test content generation with invalid project ID
echo -e "\n\nTesting content generation with invalid project ID..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"project_id": "project-1", "section_title": "Introduction"}' \
  https://doztra-research.onrender.com/api/research/content/generate-section
