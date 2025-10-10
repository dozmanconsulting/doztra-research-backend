#!/bin/bash

# Script to test the document query fix
# This script will:
# 1. Get an access token
# 2. Test querying a non-existent document
# 3. Test querying a document that's still processing
# 4. Test querying a valid document

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

# Test querying a document that's still processing
echo -e "\n${YELLOW}3. Testing query with processing document...${NC}"
# Create a new document to simulate one that's still processing
echo "Creating test document..."
cat > test_document.txt << EOL
# Test Document for Processing

This is a test document that will be used to simulate a document that's still processing.
EOL

# Upload the document
echo -e "\nUploading test document..."
UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document.txt" \
  -F "title=Test Processing Document" \
  https://doztra-research.onrender.com/api/documents/upload)

echo "Upload response:"
echo $UPLOAD_RESPONSE | jq

# Extract document ID
PROCESSING_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$PROCESSING_ID" ]; then
  echo -e "${RED}Failed to extract document ID. Response:${NC}"
  echo $UPLOAD_RESPONSE
  exit 1
fi

echo -e "${GREEN}Processing Document ID: $PROCESSING_ID${NC}"

# Immediately query the document (before it's processed)
PROCESSING_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"message\": \"Summarize this document\", \"document_ids\": [\"$PROCESSING_ID\"]}" \
  https://doztra-research.onrender.com/api/documents/query)

echo -e "${GREEN}Response for processing document:${NC}"
echo $PROCESSING_RESPONSE | jq

# Test querying a valid document
echo -e "\n${YELLOW}4. Testing query with valid document...${NC}"
# Wait for the document to be processed
echo "Waiting for document processing (10 seconds)..."
sleep 10

# Query the document again (after processing)
VALID_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"message\": \"Summarize this document\", \"document_ids\": [\"$PROCESSING_ID\"]}" \
  https://doztra-research.onrender.com/api/documents/query)

echo -e "${GREEN}Response for valid document:${NC}"
echo $VALID_RESPONSE | jq

echo -e "\n${YELLOW}=== TEST COMPLETE ===${NC}"
echo -e "Check the responses above to verify that the document query fix is working correctly."
echo -e "Expected behavior:"
echo -e "1. Non-existent document: Clear error message indicating document not found"
echo -e "2. Processing document: Message indicating document is still being processed"
echo -e "3. Valid document: Proper response with document content"
