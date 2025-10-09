#!/bin/bash

# Get a fresh authentication token
echo "Getting authentication token..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -F "username=admin@doztra.ai" \
  -F "password=AdminPassword123!")

# Extract the token from the response
AUTH_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$AUTH_TOKEN" ]; then
  echo "Failed to get authentication token. Response:"
  echo "$TOKEN_RESPONSE"
  exit 1
fi

echo "Authentication token obtained successfully."

# Create a new Doc Assist research project
echo "Creating a new Doc Assist research project..."
PROJECT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/research/projects/" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Doc Assist: A Domain-Specific Question-Answering System for Software Industry Documentation",
    "description": "This project develops a specialized question-answering system that helps software developers quickly find relevant information in technical documentation, improving productivity and reducing search time.",
    "type": "technical_report",
    "metadata": {
      "academic_level": "masters",
      "target_audience": "software_engineers",
      "research_methodology": "design_science",
      "discipline": "computer_science",
      "country": "global",
      "keywords": ["question-answering", "natural language processing", "software documentation", "information retrieval", "domain-specific AI"]
    }
  }')

# Extract the project ID from the response
PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$PROJECT_ID" ]; then
  echo "Failed to create a project. Exiting."
  exit 1
fi

echo "Created new project with ID: $PROJECT_ID"

# Generate content for the Title Page section
echo "Generating content for the Title Page section..."
CONTENT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/research/content/generate-section" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"section_title\": \"Title Page\",
    \"context\": \"Create a professional title page for a technical report on a domain-specific question-answering system for software documentation. Include appropriate author details, institution, and other relevant information.\"
  }")

# Check if content generation was successful
if echo "$CONTENT_RESPONSE" | grep -q "content"; then
  echo "Content generation successful!"
  echo "Preview of generated content:"
  echo "$CONTENT_RESPONSE" | grep -o '"content":"[^"]*"' | sed 's/"content":"\(.*\)"/\1/' | head -20 | sed 's/\\n/\n/g'
else
  echo "Content generation failed. Response:"
  echo "$CONTENT_RESPONSE"
fi

# Generate content for the Introduction section
echo "Generating content for the Introduction section..."
CONTENT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/research/content/generate-section" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"section_title\": \"Introduction\",
    \"context\": \"Focus on the challenges software developers face when searching through documentation, the need for efficient information retrieval in technical contexts, and how domain-specific question-answering systems can address these challenges.\"
  }")

# Check if content generation was successful
if echo "$CONTENT_RESPONSE" | grep -q "content"; then
  echo "Content generation successful!"
  echo "Preview of generated content:"
  echo "$CONTENT_RESPONSE" | grep -o '"content":"[^"]*"' | sed 's/"content":"\(.*\)"/\1/' | head -20 | sed 's/\\n/\n/g'
else
  echo "Content generation failed. Response:"
  echo "$CONTENT_RESPONSE"
fi

echo "Done!"
