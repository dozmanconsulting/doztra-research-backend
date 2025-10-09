#!/bin/bash

# Get token
echo "Getting token..."
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:20}..."

# Test project retrieval endpoint
echo -e "\nTesting project retrieval endpoint..."
curl -v -X GET \
  -H "Authorization: Bearer $TOKEN" \
  -H "Origin: https://doztra-frontend.onrender.com" \
  https://doztra-research.onrender.com/api/research/projects/
