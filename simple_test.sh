#!/bin/bash

# Get token
echo "Getting token..."
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:20}..."

# Test projects endpoint
echo -e "\nTesting projects endpoint..."
curl -s -X GET \
  -H "Authorization: Bearer $TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/ | head -c 300
