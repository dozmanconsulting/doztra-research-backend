#!/bin/bash

# Script to list all documents for the current user

# Get token
echo "Getting access token..."
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrackaji.aji@gmail.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Extract token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token. Response:"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo "Access Token: ${ACCESS_TOKEN:0:20}..."

# List all documents
echo -e "\nListing all documents..."
curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents/ | jq
