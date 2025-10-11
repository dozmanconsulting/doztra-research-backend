#!/bin/bash

# Document API Integration Test
# This script tests the document details and content APIs

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== DOCUMENT API INTEGRATION TEST ===${NC}"
echo ""

# Wait for deployment to be ready
echo "Waiting for deployment to complete (5 seconds)..."
sleep 5

# Step 1: Get authentication token
echo -e "${YELLOW}1. Getting authentication token...${NC}"
AUTH_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}')

# Extract token from response
ACCESS_TOKEN=$(echo $AUTH_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo -e "${RED}Failed to get authentication token${NC}"
  echo "Full authentication response:"
  echo $AUTH_RESPONSE
  exit 1
fi

echo -e "${GREEN}Authentication successful${NC}"
echo ""

# Step 2: Upload a test document
echo -e "${YELLOW}2. Uploading test document...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v2/documents/upload" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "file=@./tests/test_files/sample.pdf")

# Extract document ID from response
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*' | cut -d'"' -f4)

if [ -z "$DOCUMENT_ID" ]; then
  echo -e "${RED}Failed to upload document${NC}"
  echo "Upload response:"
  echo $UPLOAD_RESPONSE
  exit 1
fi

echo "Response: $UPLOAD_RESPONSE"
echo -e "${GREEN}Document uploaded with ID: $DOCUMENT_ID${NC}"
echo ""

# Step 3: Wait for document processing to complete
echo -e "${YELLOW}3. Waiting for document processing...${NC}"
STATUS="pending"
MAX_ATTEMPTS=20
ATTEMPT=1

while [ "$STATUS" = "pending" ] && [ $ATTEMPT -le $MAX_ATTEMPTS ]; do
  echo "Checking document status (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
  
  # Get document details
  DOCUMENT_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v2/documents/$DOCUMENT_ID" \
    -H "Authorization: Bearer $ACCESS_TOKEN")
  
  # Extract status from response
  STATUS=$(echo $DOCUMENT_RESPONSE | grep -o '"status":"[^"]*' | cut -d'"' -f4)
  
  if [ "$STATUS" = "completed" ]; then
    echo -e "${GREEN}Document processing completed${NC}"
    break
  elif [ "$STATUS" = "failed" ]; then
    echo -e "${RED}Document processing failed${NC}"
    echo "Document response:"
    echo $DOCUMENT_RESPONSE
    exit 1
  else
    echo "Status: $STATUS. Waiting 2 seconds..."
    sleep 2
    ATTEMPT=$((ATTEMPT + 1))
  fi
done

if [ "$STATUS" != "completed" ]; then
  echo -e "${RED}Document processing timed out${NC}"
  exit 1
fi

echo ""

# Step 4: Test document details API
echo -e "${YELLOW}4. Testing document details API...${NC}"
DETAILS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v2/documents/$DOCUMENT_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Response: $DETAILS_RESPONSE"

# Verify response contains expected fields
if [[ $DETAILS_RESPONSE == *"document_id"* && $DETAILS_RESPONSE == *"file_name"* && $DETAILS_RESPONSE == *"status"* ]]; then
  echo -e "${GREEN}Document details API test passed${NC}"
else
  echo -e "${RED}Document details API test failed${NC}"
  exit 1
fi

echo ""

# Step 5: Test document content API
echo -e "${YELLOW}5. Testing document content API...${NC}"
CONTENT_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v2/documents/$DOCUMENT_ID/content" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Response: $CONTENT_RESPONSE"

# Verify response contains expected fields
if [[ $CONTENT_RESPONSE == *"document_id"* && $CONTENT_RESPONSE == *"content"* ]]; then
  echo -e "${GREEN}Document content API test passed${NC}"
else
  echo -e "${RED}Document content API test failed${NC}"
  exit 1
fi

echo ""

# Step 6: Clean up - delete the document
echo -e "${YELLOW}6. Cleaning up - deleting document...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE "http://localhost:8000/api/v2/documents/$DOCUMENT_ID" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "Response: $DELETE_RESPONSE"

# Verify document was deleted
if [[ $DELETE_RESPONSE == *"deleted successfully"* ]]; then
  echo -e "${GREEN}Document deleted successfully${NC}"
else
  echo -e "${RED}Document deletion failed${NC}"
  exit 1
fi

echo ""
echo -e "${GREEN}=== TEST COMPLETED SUCCESSFULLY ===${NC}"
