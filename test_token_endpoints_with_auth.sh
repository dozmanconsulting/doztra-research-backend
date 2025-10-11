#!/bin/bash

# First, get an access token with the provided credentials
echo "Getting access token..."
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Extract the token using grep and cut (this is a simple approach, consider using jq for better JSON parsing)
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token. Response:"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo "Access token obtained successfully."
echo "Token: $ACCESS_TOKEN"

# 1. Test GET /api/tokens/me endpoint
echo -e "\n1. Testing GET /api/tokens/me endpoint..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  https://doztra-research.onrender.com/api/tokens/me

# 2. Test GET /api/tokens/me/history endpoint
echo -e "\n\n2. Testing GET /api/tokens/me/history endpoint..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  https://doztra-research.onrender.com/api/tokens/me/history

# 3. Test GET /api/tokens/me/history with pagination
echo -e "\n\n3. Testing GET /api/tokens/me/history with pagination..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  https://doztra-research.onrender.com/api/tokens/me/history?page=1&per_page=5

# 4. Test POST /api/tokens/me/track endpoint
echo -e "\n\n4. Testing POST /api/tokens/me/track endpoint..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "request_type": "chat",
    "model": "gpt-4",
    "prompt_tokens": 200,
    "completion_tokens": 800,
    "total_tokens": 1000,
    "request_id": "test_request_123"
  }' \
  https://doztra-research.onrender.com/api/tokens/me/track

# 5. Test GET /api/tokens/admin/usage endpoint
echo -e "\n\n5. Testing GET /api/tokens/admin/usage endpoint..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  https://doztra-research.onrender.com/api/tokens/admin/usage
