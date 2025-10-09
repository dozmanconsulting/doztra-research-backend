#!/bin/bash

# Get token
echo "Getting token..."
TOKEN=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:20}..."

# Create a new research project with the form data from the screenshot
echo -e "\nCreating a new dissertation project..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "New Dissertation",
    "description": "Dissertation project",
    "type": "dissertation",
    "metadata": {
      "academic_level": "Masters",
      "target_audience": "Practitioners",
      "research_methodology": "Qualitative",
      "country": "American Samoa"
    }
  }' \
  https://doztra-research.onrender.com/api/research/projects/
