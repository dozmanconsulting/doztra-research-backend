#!/bin/bash

# Script to test document upload and processing functionality
# This script will:
# 1. Get an access token
# 2. Upload a test document
# 3. Monitor the processing status
# 4. Measure processing time
# 5. Verify document content is accessible

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== DOCUMENT UPLOAD AND PROCESSING TEST ===${NC}"

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

# Create test documents of different sizes
echo -e "\n${YELLOW}2. Creating test documents...${NC}"

# Small document (1KB)
echo -e "${BLUE}Creating small test document (1KB)...${NC}"
cat > small_document.txt << EOL
# Small Test Document

This is a small test document for the Doztra system.

## Features
- Document processing
- Document querying
- AI-powered analysis

## Testing
This document is being used to test the document processing system.
EOL

# Medium document (10KB)
echo -e "${BLUE}Creating medium test document (10KB)...${NC}"
cat > medium_document.txt << EOL
# Medium Test Document

This is a medium-sized test document for the Doztra system.
$(for i in {1..50}; do echo "Line $i: This is test content to increase the file size of the document."; done)

## Features
- Document processing
- Document querying
- AI-powered analysis

## Testing
This document is being used to test the document processing system.
EOL

# Large document (100KB)
echo -e "${BLUE}Creating large test document (100KB)...${NC}"
cat > large_document.txt << EOL
# Large Test Document

This is a large test document for the Doztra system.
$(for i in {1..500}; do echo "Line $i: This is test content to increase the file size of the document. Adding more text to make it larger."; done)

## Features
- Document processing
- Document querying
- AI-powered analysis

## Testing
This document is being used to test the document processing system.
EOL

# Upload small document and measure time
echo -e "\n${YELLOW}3. Uploading small document...${NC}"
SMALL_START_TIME=$(date +%s.%N)
SMALL_UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@small_document.txt" \
  -F "title=Small Test Document" \
  https://doztra-research.onrender.com/api/documents/upload)
SMALL_END_TIME=$(date +%s.%N)
SMALL_UPLOAD_TIME=$(echo "$SMALL_END_TIME - $SMALL_START_TIME" | bc)

echo -e "${GREEN}Small document upload response:${NC}"
echo $SMALL_UPLOAD_RESPONSE | jq
echo -e "${GREEN}Small document upload time: ${SMALL_UPLOAD_TIME} seconds${NC}"

# Extract document ID
SMALL_DOC_ID=$(echo $SMALL_UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$SMALL_DOC_ID" ]; then
  echo -e "${RED}Failed to extract document ID. Response:${NC}"
  echo $SMALL_UPLOAD_RESPONSE
  exit 1
fi

echo -e "${GREEN}Small Document ID: $SMALL_DOC_ID${NC}"

# Upload medium document and measure time
echo -e "\n${YELLOW}4. Uploading medium document...${NC}"
MEDIUM_START_TIME=$(date +%s.%N)
MEDIUM_UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@medium_document.txt" \
  -F "title=Medium Test Document" \
  https://doztra-research.onrender.com/api/documents/upload)
MEDIUM_END_TIME=$(date +%s.%N)
MEDIUM_UPLOAD_TIME=$(echo "$MEDIUM_END_TIME - $MEDIUM_START_TIME" | bc)

echo -e "${GREEN}Medium document upload response:${NC}"
echo $MEDIUM_UPLOAD_RESPONSE | jq
echo -e "${GREEN}Medium document upload time: ${MEDIUM_UPLOAD_TIME} seconds${NC}"

# Extract document ID
MEDIUM_DOC_ID=$(echo $MEDIUM_UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$MEDIUM_DOC_ID" ]; then
  echo -e "${RED}Failed to extract document ID. Response:${NC}"
  echo $MEDIUM_UPLOAD_RESPONSE
  exit 1
fi

echo -e "${GREEN}Medium Document ID: $MEDIUM_DOC_ID${NC}"

# Upload large document and measure time
echo -e "\n${YELLOW}5. Uploading large document...${NC}"
LARGE_START_TIME=$(date +%s.%N)
LARGE_UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@large_document.txt" \
  -F "title=Large Test Document" \
  https://doztra-research.onrender.com/api/documents/upload)
LARGE_END_TIME=$(date +%s.%N)
LARGE_UPLOAD_TIME=$(echo "$LARGE_END_TIME - $LARGE_START_TIME" | bc)

echo -e "${GREEN}Large document upload response:${NC}"
echo $LARGE_UPLOAD_RESPONSE | jq
echo -e "${GREEN}Large document upload time: ${LARGE_UPLOAD_TIME} seconds${NC}"

# Extract document ID
LARGE_DOC_ID=$(echo $LARGE_UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$LARGE_DOC_ID" ]; then
  echo -e "${RED}Failed to extract document ID. Response:${NC}"
  echo $LARGE_UPLOAD_RESPONSE
  exit 1
fi

echo -e "${GREEN}Large Document ID: $LARGE_DOC_ID${NC}"

# Monitor processing status for small document
echo -e "\n${YELLOW}6. Monitoring processing status for small document...${NC}"
SMALL_PROCESSING_START=$(date +%s.%N)
SMALL_PROCESSED=false
SMALL_ATTEMPTS=0
SMALL_MAX_ATTEMPTS=30  # 30 seconds timeout

while [ "$SMALL_PROCESSED" = false ] && [ $SMALL_ATTEMPTS -lt $SMALL_MAX_ATTEMPTS ]; do
  SMALL_STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$SMALL_DOC_ID)
  
  SMALL_STATUS=$(echo $SMALL_STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  if [ "$SMALL_STATUS" = "ready" ]; then
    SMALL_PROCESSED=true
    SMALL_PROCESSING_END=$(date +%s.%N)
    SMALL_PROCESSING_TIME=$(echo "$SMALL_PROCESSING_END - $SMALL_PROCESSING_START" | bc)
    echo -e "${GREEN}Small document processed successfully in ${SMALL_PROCESSING_TIME} seconds${NC}"
  else
    echo -e "${BLUE}Small document status: $SMALL_STATUS (attempt $SMALL_ATTEMPTS)${NC}"
    SMALL_ATTEMPTS=$((SMALL_ATTEMPTS + 1))
    sleep 1
  fi
done

if [ "$SMALL_PROCESSED" = false ]; then
  echo -e "${RED}Small document processing timed out after $SMALL_MAX_ATTEMPTS seconds${NC}"
fi

# Monitor processing status for medium document
echo -e "\n${YELLOW}7. Monitoring processing status for medium document...${NC}"
MEDIUM_PROCESSING_START=$(date +%s.%N)
MEDIUM_PROCESSED=false
MEDIUM_ATTEMPTS=0
MEDIUM_MAX_ATTEMPTS=60  # 60 seconds timeout

while [ "$MEDIUM_PROCESSED" = false ] && [ $MEDIUM_ATTEMPTS -lt $MEDIUM_MAX_ATTEMPTS ]; do
  MEDIUM_STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$MEDIUM_DOC_ID)
  
  MEDIUM_STATUS=$(echo $MEDIUM_STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  if [ "$MEDIUM_STATUS" = "ready" ]; then
    MEDIUM_PROCESSED=true
    MEDIUM_PROCESSING_END=$(date +%s.%N)
    MEDIUM_PROCESSING_TIME=$(echo "$MEDIUM_PROCESSING_END - $MEDIUM_PROCESSING_START" | bc)
    echo -e "${GREEN}Medium document processed successfully in ${MEDIUM_PROCESSING_TIME} seconds${NC}"
  else
    echo -e "${BLUE}Medium document status: $MEDIUM_STATUS (attempt $MEDIUM_ATTEMPTS)${NC}"
    MEDIUM_ATTEMPTS=$((MEDIUM_ATTEMPTS + 1))
    sleep 1
  fi
done

if [ "$MEDIUM_PROCESSED" = false ]; then
  echo -e "${RED}Medium document processing timed out after $MEDIUM_MAX_ATTEMPTS seconds${NC}"
fi

# Monitor processing status for large document
echo -e "\n${YELLOW}8. Monitoring processing status for large document...${NC}"
LARGE_PROCESSING_START=$(date +%s.%N)
LARGE_PROCESSED=false
LARGE_ATTEMPTS=0
LARGE_MAX_ATTEMPTS=120  # 120 seconds timeout

while [ "$LARGE_PROCESSED" = false ] && [ $LARGE_ATTEMPTS -lt $LARGE_MAX_ATTEMPTS ]; do
  LARGE_STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$LARGE_DOC_ID)
  
  LARGE_STATUS=$(echo $LARGE_STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  if [ "$LARGE_STATUS" = "ready" ]; then
    LARGE_PROCESSED=true
    LARGE_PROCESSING_END=$(date +%s.%N)
    LARGE_PROCESSING_TIME=$(echo "$LARGE_PROCESSING_END - $LARGE_PROCESSING_START" | bc)
    echo -e "${GREEN}Large document processed successfully in ${LARGE_PROCESSING_TIME} seconds${NC}"
  else
    echo -e "${BLUE}Large document status: $LARGE_STATUS (attempt $LARGE_ATTEMPTS)${NC}"
    LARGE_ATTEMPTS=$((LARGE_ATTEMPTS + 1))
    sleep 1
  fi
done

if [ "$LARGE_PROCESSED" = false ]; then
  echo -e "${RED}Large document processing timed out after $LARGE_MAX_ATTEMPTS seconds${NC}"
fi

# Verify document content is accessible
echo -e "\n${YELLOW}9. Verifying document content is accessible...${NC}"

if [ "$SMALL_PROCESSED" = true ]; then
  echo -e "${BLUE}Checking small document content...${NC}"
  SMALL_CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$SMALL_DOC_ID/content)
  
  if [[ $SMALL_CONTENT_RESPONSE == *"content"* ]]; then
    echo -e "${GREEN}Small document content is accessible${NC}"
  else
    echo -e "${RED}Failed to access small document content:${NC}"
    echo $SMALL_CONTENT_RESPONSE | jq
  fi
fi

if [ "$MEDIUM_PROCESSED" = true ]; then
  echo -e "${BLUE}Checking medium document content...${NC}"
  MEDIUM_CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$MEDIUM_DOC_ID/content)
  
  if [[ $MEDIUM_CONTENT_RESPONSE == *"content"* ]]; then
    echo -e "${GREEN}Medium document content is accessible${NC}"
  else
    echo -e "${RED}Failed to access medium document content:${NC}"
    echo $MEDIUM_CONTENT_RESPONSE | jq
  fi
fi

if [ "$LARGE_PROCESSED" = true ]; then
  echo -e "${BLUE}Checking large document content...${NC}"
  LARGE_CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    https://doztra-research.onrender.com/api/documents/$LARGE_DOC_ID/content)
  
  if [[ $LARGE_CONTENT_RESPONSE == *"content"* ]]; then
    echo -e "${GREEN}Large document content is accessible${NC}"
  else
    echo -e "${RED}Failed to access large document content:${NC}"
    echo $LARGE_CONTENT_RESPONSE | jq
  fi
fi

# Test document query
echo -e "\n${YELLOW}10. Testing document query...${NC}"

if [ "$SMALL_PROCESSED" = true ]; then
  echo -e "${BLUE}Querying small document...${NC}"
  SMALL_QUERY_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $ACCESS_TOKEN" \
    -d "{\"message\": \"Summarize this document\", \"document_ids\": [\"$SMALL_DOC_ID\"]}" \
    https://doztra-research.onrender.com/api/documents/query)
  
  if [[ $SMALL_QUERY_RESPONSE == *"answer"* ]]; then
    echo -e "${GREEN}Small document query successful${NC}"
  else
    echo -e "${RED}Failed to query small document:${NC}"
    echo $SMALL_QUERY_RESPONSE | jq
  fi
fi

# Clean up
echo -e "\n${YELLOW}11. Cleaning up...${NC}"
rm -f small_document.txt medium_document.txt large_document.txt

echo -e "\n${YELLOW}=== TEST SUMMARY ===${NC}"
echo -e "${BLUE}Small document:${NC}"
echo -e "  Upload time: ${SMALL_UPLOAD_TIME} seconds"
if [ "$SMALL_PROCESSED" = true ]; then
  echo -e "  Processing time: ${SMALL_PROCESSING_TIME} seconds"
  echo -e "  Status: ${GREEN}SUCCESS${NC}"
else
  echo -e "  Status: ${RED}FAILED${NC}"
fi

echo -e "${BLUE}Medium document:${NC}"
echo -e "  Upload time: ${MEDIUM_UPLOAD_TIME} seconds"
if [ "$MEDIUM_PROCESSED" = true ]; then
  echo -e "  Processing time: ${MEDIUM_PROCESSING_TIME} seconds"
  echo -e "  Status: ${GREEN}SUCCESS${NC}"
else
  echo -e "  Status: ${RED}FAILED${NC}"
fi

echo -e "${BLUE}Large document:${NC}"
echo -e "  Upload time: ${LARGE_UPLOAD_TIME} seconds"
if [ "$LARGE_PROCESSED" = true ]; then
  echo -e "  Processing time: ${LARGE_PROCESSING_TIME} seconds"
  echo -e "  Status: ${GREEN}SUCCESS${NC}"
else
  echo -e "  Status: ${RED}FAILED${NC}"
fi
