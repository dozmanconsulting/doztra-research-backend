#!/bin/bash

# Test Netlify proxy endpoints with correct paths
echo "Testing Netlify proxy for research projects endpoint..."
curl -i -X GET \
  https://doztra-ai.netlify.app/api/research/projects/

echo -e "\n\nTesting Netlify proxy for research content generate-section endpoint..."
curl -i -X POST \
  -H "Content-Type: application/json" \
  -d '{"project_id": "test-id", "section_title": "Introduction"}' \
  https://doztra-ai.netlify.app/api/research/content/generate-section
