#!/bin/bash

# Use the token we got from the previous request
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ODQzMDc5ZS0xODIyLTRjMTItYTYyZC1mNmVjNWM1ZDMzNmQiLCJleHAiOjE3NjA2Mzc0NDh9.lt_Rt6hgHvwc7WrC0P---UmKvKGub-hcySAzMOkRxSc"

# Test research projects endpoint with auth token and verbose output
echo "Testing research projects endpoint with auth token and verbose output..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/

# Test research content generate-section endpoint with auth token and verbose output
echo -e "\n\nTesting research content generate-section endpoint with auth token and verbose output..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"project_id": "test-id", "section_title": "Introduction"}' \
  https://doztra-research.onrender.com/api/research/content/generate-section
