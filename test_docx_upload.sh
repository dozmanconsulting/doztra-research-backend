#!/bin/bash

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

API_URL="https://doztra-research.onrender.com"
DOCX_FILE="Doc Assist_Project-Proposal.docx"

echo -e "${YELLOW}=== DOCX UPLOAD TEST ===${NC}"

# Wait for deployment to complete
echo -e "\n${YELLOW}Waiting for deployment to complete (10 seconds)...${NC}"
sleep 10

# Step 1: Get authentication token
echo -e "\n${YELLOW}1. Getting authentication token...${NC}"

# Use hardcoded credentials (same as test_with_auth.sh)
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  $API_URL/api/auth/login)

# Show full response for debugging
echo "Full authentication response:"
echo "$TOKEN_RESPONSE"

# Extract the token
TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}Failed to get authentication token${NC}"
  exit 1
fi

echo -e "${GREEN}Authentication successful${NC}"

# Step 2: Upload DOCX file
echo -e "\n${YELLOW}2. Uploading DOCX file...${NC}"
UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@\"$DOCX_FILE\";type=application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
  -F "title=Doc Assist Project Proposal" \
  $API_URL/api/v2/documents/upload)

echo "Response: $UPLOAD_RESPONSE"

# Extract document ID from response
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$DOCUMENT_ID" ]; then
  echo -e "${RED}Failed to extract document ID from response${NC}"
  exit 1
fi

echo -e "${GREEN}Document uploaded with ID: $DOCUMENT_ID${NC}"

# Step 3: Wait for document processing
echo -e "\n${YELLOW}3. Waiting for document processing...${NC}"
PROCESSING_COMPLETE=false
MAX_ATTEMPTS=20  # More attempts for DOCX processing
ATTEMPT=0

while [ "$PROCESSING_COMPLETE" = false ] && [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
  ATTEMPT=$((ATTEMPT + 1))
  echo -e "Checking document status (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
  
  DOCUMENT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
    $API_URL/api/v2/documents/$DOCUMENT_ID)
  
  STATUS=$(echo $DOCUMENT_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  if [ "$STATUS" = "completed" ]; then
    PROCESSING_COMPLETE=true
    echo -e "${GREEN}Document processing completed${NC}"
  elif [ "$STATUS" = "failed" ]; then
    echo -e "${RED}Document processing failed${NC}"
    echo "Response: $DOCUMENT_RESPONSE"
    exit 1
  else
    echo -e "${BLUE}Document status: $STATUS${NC}"
    sleep 3  # Longer sleep for DOCX processing
  fi
done

if [ "$PROCESSING_COMPLETE" = false ]; then
  echo -e "${YELLOW}Document processing taking longer than expected, continuing anyway${NC}"
fi

# Step 4: Get document content
echo -e "\n${YELLOW}4. Getting document content...${NC}"
CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  $API_URL/api/v2/documents/$DOCUMENT_ID/content)

echo "Response: $CONTENT_RESPONSE"
echo -e "${GREEN}Document content retrieved successfully${NC}"

# Step 5: Delete document (optional, comment out if you want to keep it)
echo -e "\n${YELLOW}5. Deleting document...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE \
  -H "Authorization: Bearer $TOKEN" \
  $API_URL/api/v2/documents/$DOCUMENT_ID)

echo "Response: $DELETE_RESPONSE"
echo -e "${GREEN}Document deleted successfully${NC}"

echo -e "\n${GREEN}=== TEST COMPLETED SUCCESSFULLY ===${NC}"
