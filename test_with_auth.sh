#!/bin/bash

# First, get an access token with the provided credentials
echo "Getting access token..."
TOKEN_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=shedrack.aji@outlook.com&password=Password123!" \
  https://doztra-research.onrender.com/api/auth/login)

# Extract the token using grep and cut (this is a simple approach, consider using jq for better JSON parsing)
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "Failed to get access token. Response:"
  echo $TOKEN_RESPONSE
  exit 1
fi

echo "Access token obtained successfully."

# 1. List existing research projects
echo -e "\n1. Listing existing research projects..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/

# 2. Create a new research project
echo -e "\n\n2. Creating a new research project..."
PROJECT_RESPONSE=$(curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"title": "Test Research Project", "description": "This is a test project", "type": "academic"}' \
  https://doztra-research.onrender.com/api/research/projects/ 2>&1)

echo $PROJECT_RESPONSE

# Extract project ID (this is a simple approach, consider using jq for better JSON parsing)
PROJECT_ID=$(echo $PROJECT_RESPONSE | grep -o '"id":"[^"]*"' | cut -d'"' -f4)

if [ -z "$PROJECT_ID" ]; then
  echo "Failed to create project or extract project ID. Using a valid UUID instead."
  PROJECT_ID="1ab2aa37-2e2e-4537-bb81-7afe87c6a675"
else
  echo "Created project with ID: $PROJECT_ID"
fi

# 3. List projects again to see the new project
echo -e "\n\n3. Listing projects again to see the new project..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/

# 4. Generate content for the project
echo -e "\n\n4. Generating content for the project..."
curl -v -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"project_id": "'$PROJECT_ID'", "section_title": "Introduction"}' \
  https://doztra-research.onrender.com/api/research/content/generate-section

# 5. Get project details
echo -e "\n\n5. Getting project details..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/$PROJECT_ID

# 6. Update project
echo -e "\n\n6. Updating project..."
curl -v -X PUT \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"title": "Updated Test Project", "description": "This project has been updated"}' \
  https://doztra-research.onrender.com/api/research/projects/$PROJECT_ID

# 7. Get updated project details
echo -e "\n\n7. Getting updated project details..."
curl -v -X GET \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  https://doztra-research.onrender.com/api/research/projects/$PROJECT_ID
