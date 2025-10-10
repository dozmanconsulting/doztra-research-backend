#!/bin/bash

# Use the token we got from the previous request
ACCESS_TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI0ODQzMDc5ZS0xODIyLTRjMTItYTYyZC1mNmVjNWM1ZDMzNmQiLCJleHAiOjE3NjA2Mzc0NDh9.lt_Rt6hgHvwc7WrC0P---UmKvKGub-hcySAzMOkRxSc"

# Test Netlify proxy for research projects endpoint with auth token
echo "Testing Netlify proxy for research projects endpoint with auth token..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-ai.netlify.app/api/research/projects/

# Test Netlify proxy for research content generate-section endpoint with auth token
echo -e "\n\nTesting Netlify proxy for research content generate-section endpoint with auth token..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"project_id": "test-id", "section_title": "Introduction"}' \
  https://doztra-ai.netlify.app/api/research/content/generate-section
