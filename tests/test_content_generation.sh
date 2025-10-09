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

# First, let's get the user's research projects to find a project ID
echo "Fetching research projects..."
PROJECTS_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/research/projects/?skip=0&limit=10" \
  -H "Authorization: Bearer $AUTH_TOKEN")

# Extract the first project ID from the response
PROJECT_ID=$(echo $PROJECTS_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$PROJECT_ID" ]; then
  echo "No projects found. Creating a new research project..."
  
  # Create a new research project
  PROJECT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/research/projects/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "title": "AI Applications in Healthcare: A Comprehensive Analysis",
      "description": "This dissertation explores the current and future applications of artificial intelligence in healthcare, focusing on diagnostic tools, treatment planning, and patient care optimization.",
      "type": "dissertation",
      "metadata": {
        "academic_level": "doctoral",
        "target_audience": "researchers",
        "research_methodology": "mixed_methods",
        "discipline": "computer_science",
        "keywords": ["artificial intelligence", "healthcare", "machine learning", "medical diagnosis", "patient care"]
      }
    }')
  
  # Extract the project ID from the response
  PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*"' | head -1 | cut -d'"' -f4)
  
  if [ -z "$PROJECT_ID" ]; then
    echo "Failed to create a project. Exiting."
    exit 1
  fi
  
  echo "Created new project with ID: $PROJECT_ID"
else
  echo "Using existing project with ID: $PROJECT_ID"
fi

# Generate content for the Introduction section
echo "Generating content for the Introduction section..."
CONTENT_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/research/content/generate-section" \
  -H "Authorization: Bearer $AUTH_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"project_id\": \"$PROJECT_ID\",
    \"section_title\": \"Introduction\",
    \"context\": \"Focus on the transformative potential of AI in healthcare, including recent breakthroughs in diagnostic accuracy and patient care optimization. Discuss the ethical considerations and challenges of implementing AI in healthcare settings.\"
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
