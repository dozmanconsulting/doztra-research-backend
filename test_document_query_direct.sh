#!/bin/bash

# Script to test the document query fix
# This script will:
# 1. Get an access token
# 2. Test querying a non-existent document
# 3. Test querying a valid document

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== TESTING DOCUMENT QUERY FIX ===${NC}"

# Get token
echo -e "\n${YELLOW}1. Getting access token...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrackaji.aji@gmail.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Extract token
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}Failed to get access token. Response:${NC}"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo -e "${GREEN}Access Token: ${ACCESS_TOKEN:0:20}...${NC}"

# Test querying a non-existent document
echo -e "\n${YELLOW}2. Testing query with non-existent document...${NC}"
NON_EXISTENT_ID="doc-00000000-0000-0000-0000-000000000000"
NON_EXISTENT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"message\": \"Summarize this document\", \"document_ids\": [\"$NON_EXISTENT_ID\"]}" \
  https://doztra-research.onrender.com/api/documents/query)

echo -e "${GREEN}Response for non-existent document:${NC}"
echo $NON_EXISTENT_RESPONSE | jq

# List available documents
echo -e "\n${YELLOW}3. Listing available documents...${NC}"
DOCUMENTS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents)

echo -e "${GREEN}Available documents:${NC}"
echo $DOCUMENTS_RESPONSE | jq

# Extract a document ID if available
DOCUMENT_IDS=$(echo $DOCUMENTS_RESPONSE | jq -r '.documents[].document_id')
if [ -z "$DOCUMENT_IDS" ]; then
  echo -e "${RED}No documents found. Creating a test document...${NC}"
  
  # Create a test document
  echo "Creating test document..."
  cat > test_document.txt << EOL
# Test Document

This is a test document for querying.
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
  DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)
  
  if [ -z "$DOCUMENT_ID" ]; then
    echo -e "${RED}Failed to extract document ID. Response:${NC}"
    echo $UPLOAD_RESPONSE
    exit 1
  fi
  
  echo -e "${GREEN}Created document with ID: $DOCUMENT_ID${NC}"
  
  # Wait for processing
  echo -e "\nWaiting for document processing (5 seconds)..."
  sleep 5
else
  # Use the first document ID
  DOCUMENT_ID=$(echo $DOCUMENT_IDS | head -n 1)
  echo -e "${GREEN}Using existing document with ID: $DOCUMENT_ID${NC}"
fi

# Test querying a valid document
echo -e "\n${YELLOW}4. Testing query with valid document...${NC}"
VALID_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"message\": \"Summarize this document\", \"document_ids\": [\"$DOCUMENT_ID\"]}" \
  https://doztra-research.onrender.com/api/documents/query)

echo -e "${GREEN}Response for valid document:${NC}"
echo $VALID_RESPONSE | jq

# Clean up
echo -e "\n${YELLOW}5. Cleaning up...${NC}"
rm -f test_document.txt

echo -e "\n${YELLOW}=== TEST COMPLETE ===${NC}"
echo -e "Check the responses above to verify that the document query fix is working correctly."
echo -e "Expected behavior:"
echo -e "1. Non-existent document: Clear error message indicating document not found"
echo -e "2. Valid document: Proper response with document content"
