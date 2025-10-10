#!/bin/bash

# Script to list all documents and check their processing status

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
DOCUMENTS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents/)

echo "Documents response:"
echo $DOCUMENTS_RESPONSE | jq

# Extract document IDs
echo -e "\nExtracting document IDs..."
DOCUMENT_IDS=$(echo $DOCUMENTS_RESPONSE | jq -r '.items[].document_id')

if [ -z "$DOCUMENT_IDS" ]; then
  echo "No documents found."
  exit 0
fi

# Check each document's status
echo -e "\nChecking status of each document..."
for DOC_ID in $DOCUMENT_IDS; do
  echo -e "\n=== Document ID: $DOC_ID ==="
  
  # Get document status
  STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$DOC_ID)
  
  echo "Status:"
  echo $STATUS_RESPONSE | jq
  
  # Get document content
  CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$DOC_ID/content)
  
  echo "Content availability:"
  if [[ $CONTENT_RESPONSE == *"still being processed"* ]]; then
    echo "Document is still being processed"
  elif [[ $CONTENT_RESPONSE == *"content"* ]]; then
    echo "Content is available"
  else
    echo "Unknown content status:"
    echo $CONTENT_RESPONSE | jq
  fi
done
