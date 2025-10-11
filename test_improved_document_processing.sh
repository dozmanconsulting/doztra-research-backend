#!/bin/bash

# Script to test improved document upload and processing functionality
# This script will:
# 1. Get an access token
# 2. Upload a test document using the improved API
# 3. Monitor the processing status
# 4. Measure processing time
# 5. Verify document content is accessible

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

echo -e "${YELLOW}=== IMPROVED DOCUMENT PROCESSING TEST ===${NC}"

# Set API base URL
API_BASE_URL="http://localhost:8000"  # Change this to your API URL

# Get token
echo -e "\n${YELLOW}1. Getting access token...${NC}"
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=password123" \
  ${API_BASE_URL}/api/auth/login)

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
cat > test_document.txt << EOL
# Test Document for Improved Processing

This is a test document to verify the improved document processing functionality.

## Features Being Tested

1. Async file upload
2. Database storage
3. Optimized chunk size
4. Parallel embedding generation
5. Proper status tracking

## Expected Results

- Faster upload time
- More reliable processing
- Better error handling
- Improved status tracking
EOL

# Upload document using improved API
echo -e "\n${YELLOW}3. Uploading document using improved API...${NC}"
UPLOAD_START_TIME=$(date +%s.%N)
UPLOAD_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_document.txt" \
  -F "title=Improved Processing Test" \
  ${API_BASE_URL}/api/v2/documents/upload)
UPLOAD_END_TIME=$(date +%s.%N)
UPLOAD_TIME=$(echo "$UPLOAD_END_TIME - $UPLOAD_START_TIME" | bc)

echo -e "${GREEN}Upload response:${NC}"
echo $UPLOAD_RESPONSE | jq
echo -e "${GREEN}Upload time: ${UPLOAD_TIME} seconds${NC}"

# Extract document ID
DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | grep -o '"document_id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$DOCUMENT_ID" ]; then
  echo -e "${RED}Failed to extract document ID. Response:${NC}"
  echo $UPLOAD_RESPONSE
  exit 1
fi

echo -e "${GREEN}Document ID: $DOCUMENT_ID${NC}"

# Monitor processing status
echo -e "\n${YELLOW}4. Monitoring processing status...${NC}"
PROCESSING_START=$(date +%s.%N)
PROCESSED=false
ATTEMPTS=0
MAX_ATTEMPTS=30  # 30 seconds timeout

while [ "$PROCESSED" = false ] && [ $ATTEMPTS -lt $MAX_ATTEMPTS ]; do
  STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
    ${API_BASE_URL}/api/v2/documents/$DOCUMENT_ID)
  
  STATUS=$(echo $STATUS_RESPONSE | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
  
  if [ "$STATUS" = "completed" ]; then
    PROCESSED=true
    PROCESSING_END=$(date +%s.%N)
    PROCESSING_TIME=$(echo "$PROCESSING_END - $PROCESSING_START" | bc)
    echo -e "${GREEN}Document processed successfully in ${PROCESSING_TIME} seconds${NC}"
  elif [ "$STATUS" = "failed" ]; then
    echo -e "${RED}Document processing failed:${NC}"
    echo $STATUS_RESPONSE | jq
    exit 1
  else
    echo -e "${BLUE}Document status: $STATUS (attempt $ATTEMPTS)${NC}"
    ATTEMPTS=$((ATTEMPTS + 1))
    sleep 1
  fi
done

if [ "$PROCESSED" = false ]; then
  echo -e "${RED}Document processing timed out after $MAX_ATTEMPTS seconds${NC}"
  exit 1
fi

# Verify document content is accessible
echo -e "\n${YELLOW}5. Verifying document content is accessible...${NC}"
CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  ${API_BASE_URL}/api/v2/documents/$DOCUMENT_ID/content)

if [[ $CONTENT_RESPONSE == *"content"* ]]; then
  echo -e "${GREEN}Document content is accessible${NC}"
  echo -e "${BLUE}Content preview:${NC}"
  CONTENT=$(echo $CONTENT_RESPONSE | jq -r '.content' | head -n 5)
  echo "$CONTENT..."
else
  echo -e "${RED}Failed to access document content:${NC}"
  echo $CONTENT_RESPONSE | jq
  exit 1
fi

# Test document deletion
echo -e "\n${YELLOW}6. Testing document deletion...${NC}"
DELETE_RESPONSE=$(curl -s -X DELETE \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  ${API_BASE_URL}/api/v2/documents/$DOCUMENT_ID)

if [[ $DELETE_RESPONSE == *"success"* ]]; then
  echo -e "${GREEN}Document deleted successfully${NC}"
else
  echo -e "${RED}Failed to delete document:${NC}"
  echo $DELETE_RESPONSE | jq
  exit 1
fi

# Clean up
echo -e "\n${YELLOW}7. Cleaning up...${NC}"
rm -f test_document.txt

# Check storage type from response
STORAGE_TYPE=$(echo $UPLOAD_RESPONSE | grep -o '"storage_type":"[^"]*"' | cut -d'"' -f4)

echo -e "\n${YELLOW}=== TEST SUMMARY ===${NC}"
echo -e "Upload time: ${UPLOAD_TIME} seconds"
echo -e "Processing time: ${PROCESSING_TIME} seconds"
echo -e "Storage backend: ${BLUE}${STORAGE_TYPE}${NC}"
echo -e "Status: ${GREEN}SUCCESS${NC}"

echo -e "\n${YELLOW}=== STORAGE VERIFICATION ===${NC}"

if [ "$STORAGE_TYPE" = "gcs" ]; then
    echo -e "${BLUE}Document was stored in Google Cloud Storage${NC}"
    echo -e "To verify, check your GCS bucket using the Google Cloud Console or run:"
    echo -e "${BLUE}gsutil ls gs://YOUR_BUCKET_NAME/${NC}"
    
    # If GOOGLE_APPLICATION_CREDENTIALS is set, try to list the bucket
    if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ] && [ -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo -e "\n${YELLOW}Attempting to verify GCS storage...${NC}"
        
        # Try to extract bucket name from response
        GCS_PATH=$(echo $UPLOAD_RESPONSE | grep -o '"file_path":"[^"]*"' | cut -d'"' -f4)
        BUCKET_NAME=$(echo $GCS_PATH | sed 's|gs://\([^/]*\)/.*|\1|')
        
        if [ -n "$BUCKET_NAME" ]; then
            echo -e "Checking bucket: $BUCKET_NAME"
            gsutil ls "gs://$BUCKET_NAME/" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}Successfully connected to GCS bucket${NC}"
            else
                echo -e "${RED}Could not connect to GCS bucket. Check your credentials.${NC}"
            fi
        fi
    fi
elif [ "$STORAGE_TYPE" = "s3" ]; then
    echo -e "${BLUE}Document was stored in AWS S3${NC}"
    echo -e "To verify, check your S3 bucket using the AWS Console or run:"
    echo -e "${BLUE}aws s3 ls s3://YOUR_BUCKET_NAME/${NC}"
else
    echo -e "${BLUE}Document was stored in local storage${NC}"
    echo -e "To verify, check the uploads directory:"
    echo -e "${BLUE}ls -la ./uploads/${NC}"
fi

echo -e "\n${YELLOW}=== PERFORMANCE COMPARISON ===${NC}"
echo -e "To compare with the original implementation, run:"
echo -e "${BLUE}./test_document_upload_processing.sh${NC}"
