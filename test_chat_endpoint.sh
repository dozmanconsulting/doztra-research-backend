#!/bin/bash

# Get authentication token
echo "Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Extract the token from the response
AUTH_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AUTH_TOKEN" ]; then
  echo "Failed to get authentication token. Response:"
  echo "$TOKEN_RESPONSE"
  exit 1
fi

echo "Authentication token obtained successfully."
echo "Token: ${AUTH_TOKEN:0:20}..."

# Test the chat endpoint
echo -e "\nTesting chat endpoint..."
CHAT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "message": "Tell me about AI research",
    "model": "gpt-3.5-turbo"
  }' \
  https://doztra-research.onrender.com/api/messages)

echo "Chat Response:"
echo "$CHAT_RESPONSE" | head -c 500
echo -e "\n...(truncated)"

# Test the research projects endpoint
echo -e "\nTesting research projects endpoint..."
PROJECTS_RESPONSE=$(curl -s -X GET \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/)

echo "Projects Response:"
echo "$PROJECTS_RESPONSE" | head -c 300
echo -e "\n...(truncated)"

# Create a new research project
echo -e "\nCreating a new research project..."
PROJECT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d '{
    "title": "AI in Healthcare: Current Applications and Future Directions",
    "description": "This research project explores the current applications of artificial intelligence in healthcare and discusses potential future directions.",
    "type": "academic"
  }' \
  https://doztra-research.onrender.com/api/research/projects/)

echo "Project Creation Response:"
echo "$PROJECT_RESPONSE" | head -c 300
echo -e "\n...(truncated)"

# Extract the project ID
PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$PROJECT_ID" ]; then
  echo "Failed to extract project ID. Using a default ID for testing."
  PROJECT_ID="0f516270-4e1b-47ad-a193-a498a677ffbc"
else
  echo "Project ID: $PROJECT_ID"
fi

# Generate content for the project
echo -e "\nGenerating content for the project..."
CONTENT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"section_title\": \"Introduction\"
  }" \
  https://doztra-research.onrender.com/api/research/content/generate-section)

echo "Content Generation Response:"
echo "$CONTENT_RESPONSE" | head -c 500
echo -e "\n...(truncated)"

echo -e "\nAll tests completed!"
