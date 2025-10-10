#!/bin/bash

# Script to test document deletion functionality
# This script will:
# 1. Get an access token
# 2. Upload a test document
# 3. Try to delete the document
# 4. Check if deletion was successful

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DOCUMENT DELETION TEST ===${NC}"

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

# Create test document
echo -e "\n${YELLOW}2. Creating test document...${NC}"
cat > test_document_for_deletion.txt << EOL
# Test Document for Deletion

This is a test document that will be used to test the document deletion functionality.
EOL

# Upload the document
echo -e "\n${YELLOW}3. Uploading test document...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document_for_deletion.txt" \
  -F "title=Test Document for Deletion" \
  https://doztra-research.onrender.com/api/documents/upload)

echo -e "${GREEN}Upload response:${NC}"
echo $UPLOAD_RESPONSE | jq

# Extract document ID
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$DOCUMENT_ID" ]; then
  echo -e "${RED}Failed to extract document ID. Response:${NC}"
  echo $UPLOAD_RESPONSE
  exit 1
fi

echo -e "${GREEN}Document ID: $DOCUMENT_ID${NC}"

# List documents before deletion
echo -e "\n${YELLOW}4. Listing documents before deletion...${NC}"
BEFORE_LIST_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents)

echo -e "${GREEN}Documents before deletion:${NC}"
echo $BEFORE_LIST_RESPONSE | jq

# Try to delete the document
echo -e "\n${YELLOW}5. Attempting to delete document...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE -v \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents/$DOCUMENT_ID)

echo -e "${GREEN}Delete response:${NC}"
echo $DELETE_RESPONSE | jq

# List documents after deletion
echo -e "\n${YELLOW}6. Listing documents after deletion...${NC}"
AFTER_LIST_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents)

echo -e "${GREEN}Documents after deletion:${NC}"
echo $AFTER_LIST_RESPONSE | jq

# Check if document still exists
echo -e "\n${YELLOW}7. Checking if document still exists...${NC}"
CHECK_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/documents/$DOCUMENT_ID)

echo -e "${GREEN}Check response:${NC}"
echo $CHECK_RESPONSE | jq

# Clean up
echo -e "\n${YELLOW}8. Cleaning up...${NC}"
rm -f test_document_for_deletion.txt

echo -e "\n${YELLOW}=== TEST COMPLETE ===${NC}"
if [[ $CHECK_RESPONSE == *"not found"* ]]; then
  echo -e "${GREEN}Document deletion was successful!${NC}"
else
  echo -e "${RED}Document deletion failed!${NC}"
fi
