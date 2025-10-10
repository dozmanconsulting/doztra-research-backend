#!/bin/bash

# Test research projects endpoint
echo "Testing research projects endpoint..."
curl -i -X GET \
  https://doztra-research.onrender.com/api/research/projects/

echo -e "\n\nTesting research content generate-section endpoint..."
curl -i -X POST \
  -H "Content-Type: application/json" \
  -d '{"project_id": "test-id", "section_title": "Introduction"}' \
  https://doztra-research.onrender.com/api/research/content/generate-section
