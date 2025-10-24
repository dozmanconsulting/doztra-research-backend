#!/bin/bash

# Test new Knowledge Base endpoints once deployed
BASE_URL="https://doztra-research.onrender.com"
TEST_EMAIL="test-$(date +%s)@example.com"

echo "🧪 Testing New Knowledge Base Endpoints"
echo "======================================="

# 1. Register and login
echo "1. Getting access token..."
register_response=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"TestPassword123!\",\"name\":\"Test User\"}")

ACCESS_TOKEN=$(echo "$register_response" | jq -r '.access_token // empty')

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    exit 1
fi

echo "✅ Access token obtained"

# 2. Test Conversation Sessions
echo -e "\n2. Testing Conversation Sessions..."

# Create session
echo "  Creating conversation session..."
session_response=$(curl -s -X POST "$BASE_URL/api/conversations/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "title": "Test Knowledge Base Session",
    "settings": {"model": "gpt-4", "temperature": 0.7},
    "session_metadata": {"test": true}
  }')

echo "  Response: $(echo "$session_response" | jq .)"

# Get sessions
echo "  Getting conversation sessions..."
sessions_response=$(curl -s -X GET "$BASE_URL/api/conversations/sessions" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "  Response: $(echo "$sessions_response" | jq .)"

# 3. Test Content Items
echo -e "\n3. Testing Content Items..."

# Create content item
echo "  Creating content item..."
content_response=$(curl -s -X POST "$BASE_URL/api/content/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "title": "Test Document",
    "content_type": "text",
    "content": "This is a test document for the knowledge base system.",
    "content_metadata": {"source": "test"}
  }')

echo "  Response: $(echo "$content_response" | jq .)"

# Get content items
echo "  Getting content items..."
content_list_response=$(curl -s -X GET "$BASE_URL/api/content/items" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "  Response: $(echo "$content_list_response" | jq .)"

# 4. Test Podcasts
echo -e "\n4. Testing Podcasts..."

# Create podcast
echo "  Creating podcast..."
podcast_response=$(curl -s -X POST "$BASE_URL/api/podcasts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "title": "Test AI Podcast",
    "topic": "Artificial Intelligence in Healthcare",
    "description": "A test podcast about AI applications in healthcare",
    "podcast_metadata": {"test": true}
  }')

echo "  Response: $(echo "$podcast_response" | jq .)"

# Get podcasts
echo "  Getting podcasts..."
podcasts_response=$(curl -s -X GET "$BASE_URL/api/podcasts" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

echo "  Response: $(echo "$podcasts_response" | jq .)"

echo -e "\n🎉 Knowledge Base endpoint testing complete!"
echo "If you see JSON responses above, the endpoints are working! 🚀"
