#!/bin/bash

# Test CORS configuration
echo "Testing CORS configuration..."

# Test OPTIONS request with Origin header
echo "Sending OPTIONS request with Origin header..."
curl -v -X OPTIONS \
  -H "Origin: https://doztra-ai.netlify.app" \
  -H "Access-Control-Request-Method: GET" \
  -H "Access-Control-Request-Headers: Authorization,Content-Type" \
  https://doztra-research.onrender.com/api/research/projects/

echo -e "\n\nTesting actual GET request with Origin header..."
curl -v -X GET \
  -H "Origin: https://doztra-ai.netlify.app" \
  https://doztra-research.onrender.com/api/research/projects/
