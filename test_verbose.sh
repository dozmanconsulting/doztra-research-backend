#!/bin/bash

# First, get an access token with verbose output
echo "Getting access token with verbose output..."
curl -v -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login

# Now let's try to get a simple health check
echo -e "\n\nGetting health check..."
curl -v https://doztra-research.onrender.com/health

# Let's try a different endpoint that doesn't require authentication
echo -e "\n\nGetting API version..."
curl -v https://doztra-research.onrender.com/api/version
