#!/bin/bash

# Get token
echo "Getting token..."
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:20}..."

# Check CORS headers
echo -e "\nChecking CORS headers for research projects endpoint..."
curl -s -I -X OPTIONS \
  -H "Origin: https://doztra-frontend.onrender.com" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization" \
  https://doztra-research.onrender.com/api/research/projects/

# Test the endpoint with token
echo -e "\nTesting research projects endpoint..."
curl -s -X GET \
  -H "Authorization: Bearer $TOKEN" \
  -H "Origin: https://doztra-frontend.onrender.com" \
  https://doztra-research.onrender.com/api/research/projects/ | head -c 300
