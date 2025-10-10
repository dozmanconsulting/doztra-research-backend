#!/bin/bash

# Script to upload a test document and check its status

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

# Create a test document file
echo "Creating test document..."
cat > test_document.txt << EOL
# Test Document

This is a test document for the Doztra system.

## Features
- Document processing
- Document querying
- AI-powered analysis

## Testing
This document is being used to test the document processing system.
EOL

# Upload the document
echo -e "\nUploading test document..."
UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document.txt" \
  -F "title=Test Document" \
  https://doztra-research.onrender.com/api/documents/upload)

echo "Upload response:"
echo $UPLOAD_RESPONSE | jq

# Extract document ID
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$DOCUMENT_ID" ]; then
  echo "Failed to extract document ID. Response:"
  echo $UPLOAD_RESPONSE
  exit 1
fi

echo "Document ID: $DOCUMENT_ID"

# Wait for processing
echo -e "\nWaiting for document processing (10 seconds)..."
sleep 10

# Check document status
echo -e "\nChecking document status..."
./check_document_status.sh $DOCUMENT_ID "$ACCESS_TOKEN"
