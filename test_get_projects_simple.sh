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
RESPONSE=$(curl -s -X GET \
  -H "Authorization: Bearer $TOKEN" \
  -H "Origin: https://doztra-frontend.onrender.com" \
  https://doztra-research.onrender.com/api/research/projects/)

# Print response status
echo "Response received"
echo "Response contains 'items': $(echo $RESPONSE | grep -o '"items"' | wc -l)"
echo "Response contains 'total': $(echo $RESPONSE | grep -o '"total"' | wc -l)"

# Print first 300 characters of the response
echo -e "\nResponse preview:"
echo $RESPONSE | head -c 300
