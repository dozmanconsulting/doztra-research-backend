#!/bin/bash

# Script to check a specific document ID

# Document ID from the screenshot
DOCUMENT_ID="doc-9a11651a-4c56-49a7-8d17-4d048326226c"

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
echo -e "\nChecking document status for ID: $DOCUMENT_ID"
STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents/$DOCUMENT_ID)

echo "Status response:"
echo $STATUS_RESPONSE | jq

# Try to get document content
echo -e "\nTrying to get document content..."
CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents/$DOCUMENT_ID/content)

echo "Content response:"
echo $CONTENT_RESPONSE | jq

# Try a query on this document
echo -e "\nTrying to query this document..."
QUERY_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"message\": \"Summarize this document\", \"document_ids\": [\"$DOCUMENT_ID\"]}" \
  https://doztra-research.onrender.com/api/documents/query)

echo "Query response:"
echo $QUERY_RESPONSE | jq
