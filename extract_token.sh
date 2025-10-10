#!/bin/bash

# Script to extract token and check document status

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

# Check document status
echo -e "\nChecking document status..."
./check_document_status.sh doc-9a11651a-4c56-49a7-8d17-4d048326226c "$ACCESS_TOKEN"
