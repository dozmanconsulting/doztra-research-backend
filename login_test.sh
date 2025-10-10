#!/bin/bash

# Test login endpoint
echo "Testing login endpoint..."
curl -i -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login
