#!/bin/bash

# Script to check document processing status
# Usage: ./check_document_status.sh <document_id> <access_token>

# Colors for better readability
GREEN="\033[0;32m"
RED="\033[0;31m"
YELLOW="\033[0;33m"
NC="\033[0m" # No Color

# Check if document ID and access token are provided
if [ $# -lt 2 ]; then
  echo -e "${RED}Error: Missing parameters${NC}"
  echo "Usage: $0 <document_id> <access_token>"
  exit 1
fi

DOCUMENT_ID=$1
ACCESS_TOKEN=$2
API_BASE_URL="https://doztra-research.onrender.com"

echo -e "${YELLOW}=== DOCUMENT STATUS CHECK ===${NC}"
echo -e "Checking status of document: ${YELLOW}$DOCUMENT_ID${NC}"

# Check document status
echo -e "\n${YELLOW}1. Checking document status...${NC}"
STATUS_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$API_BASE_URL/api/documents/$DOCUMENT_ID")

# Check if the document exists
if [[ $STATUS_RESPONSE == *"not found"* ]]; then
  echo -e "${RED}Document not found!${NC}"
  echo "Response: $STATUS_RESPONSE"
  exit 1
fi

# Display document status
echo -e "${GREEN}Document status:${NC}"
echo $STATUS_RESPONSE | jq

# Check document content
echo -e "\n${YELLOW}2. Checking document content...${NC}"
CONTENT_RESPONSE=$(curl -s -H "Authorization: Bearer $ACCESS_TOKEN" \
  "$API_BASE_URL/api/documents/$DOCUMENT_ID/content")

# Check if content is available
if [[ $CONTENT_RESPONSE == *"not found"* || $CONTENT_RESPONSE == *"still being processed"* ]]; then
  echo -e "${RED}Document content not available:${NC}"
  echo "Response: $CONTENT_RESPONSE"
else
  echo -e "${GREEN}Document content available:${NC}"
  echo $CONTENT_RESPONSE | jq
fi

# Try a simple query on the document
echo -e "\n${YELLOW}3. Testing document query...${NC}"
QUERY_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d "{\"message\": \"Summarize this document\", \"document_ids\": [\"$DOCUMENT_ID\"]}" \
  "$API_BASE_URL/api/documents/query")

echo -e "${GREEN}Query response:${NC}"
echo $QUERY_RESPONSE | jq

echo -e "\n${YELLOW}=== STATUS CHECK COMPLETE ===${NC}"
echo -e "If the document is still being processed, wait a few minutes and try again."
echo -e "If the issue persists, use the document_processing_debug.py script to investigate further."
