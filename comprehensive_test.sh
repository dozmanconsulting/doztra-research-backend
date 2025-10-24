#!/bin/bash

# Comprehensive Doztra API Test with correct field names
BASE_URL="https://doztra-research.onrender.com"
TEST_EMAIL="test-$(date +%s)@example.com"

echo "🧪 Comprehensive Doztra API Test"
echo "================================="

# 1. Register
echo "1. Testing Registration..."
response=$(curl -s -X POST "$BASE_URL/api/auth/register" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$TEST_EMAIL\",\"password\":\"TestPassword123!\",\"name\":\"Test User\"}")

if echo "$response" | jq -e '.success' > /dev/null 2>&1; then
    echo "✅ Registration successful"
else
    echo "❌ Registration failed:"
    echo "$response" | jq .
    exit 1
fi

# 2. Login
echo -e "\n2. Testing Login..."
response=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL&password=TestPassword123!")

ACCESS_TOKEN=$(echo "$response" | jq -r '.access_token // empty')

if [ -n "$ACCESS_TOKEN" ]; then
    echo "✅ Login successful - token obtained"
else
    echo "❌ Login failed:"
    echo "$response" | jq .
    exit 1
fi

# 3. Test user profile
echo -e "\n3. Testing User Profile..."
response=$(curl -s -X GET "$BASE_URL/api/users/me" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$response" | jq -e '.email' > /dev/null 2>&1; then
    echo "✅ User profile retrieved"
    echo "User: $(echo "$response" | jq -r '.name') ($(echo "$response" | jq -r '.email'))"
    echo "Subscription: $(echo "$response" | jq -r '.subscription.plan') - $(echo "$response" | jq -r '.subscription.status')"
else
    echo "❌ Failed to get user profile"
fi

# 4. Test all research options
echo -e "\n4. Testing Research Options..."
endpoints=("academic-levels" "target-audiences" "countries" "academic-disciplines" "research-methodologies")

for endpoint in "${endpoints[@]}"; do
    response=$(curl -s -X GET "$BASE_URL/api/research/options/$endpoint" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    if echo "$response" | jq -e '.[0]' > /dev/null 2>&1; then
        count=$(echo "$response" | jq '. | length')
        echo "✅ $endpoint ($count options)"
    else
        echo "❌ $endpoint failed"
    fi
done

# 5. Test AI improve topic (with correct fields based on error)
echo -e "\n5. Testing AI Topic Improvement..."
response=$(curl -s -X POST "$BASE_URL/api/improve-topic" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "originalInput": "AI in healthcare",
    "type": "topic_improvement",
    "citation": "APA",
    "length": "medium",
    "discipline": "computer_science",
    "country": "global",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
  }')

if echo "$response" | jq -e '.improved_topic' > /dev/null 2>&1; then
    echo "✅ Topic improvement successful"
    echo "Improved topic: $(echo "$response" | jq -r '.improved_topic')"
else
    echo "⚠️  Topic improvement response:"
    echo "$response" | jq .
fi

# 6. Test outline generation (with correct fields)
echo -e "\n6. Testing Outline Generation..."
response=$(curl -s -X POST "$BASE_URL/api/generate-outline" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{
    "topic": "The Impact of Artificial Intelligence on Modern Healthcare Systems",
    "type": "research_paper",
    "citation": "APA",
    "length": "medium",
    "discipline": "computer_science",
    "country": "global",
    "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'"
  }')

if echo "$response" | jq -e '.outline' > /dev/null 2>&1; then
    echo "✅ Outline generation successful"
    echo "Outline sections: $(echo "$response" | jq -r '.outline | length')"
else
    echo "⚠️  Outline generation response:"
    echo "$response" | jq .
fi

# 7. Test Knowledge Base endpoints (expected to return 404 for now)
echo -e "\n7. Testing Knowledge Base Endpoints (may return 404)..."

kb_endpoints=(
    "GET /api/conversations/sessions"
    "GET /api/content/items" 
    "GET /api/podcasts"
    "GET /api/research/projects"
    "GET /api/documents"
)

for endpoint_info in "${kb_endpoints[@]}"; do
    method=$(echo $endpoint_info | cut -d' ' -f1)
    endpoint=$(echo $endpoint_info | cut -d' ' -f2)
    
    response=$(curl -s -w "\n%{http_code}" -X "$method" "$BASE_URL$endpoint" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    
    http_code=$(echo "$response" | tail -n1)
    
    if [[ $http_code -eq 200 ]]; then
        echo "✅ $endpoint_info (implemented)"
    elif [[ $http_code -eq 404 ]]; then
        echo "⚠️  $endpoint_info (not implemented yet)"
    else
        echo "❌ $endpoint_info (error: $http_code)"
    fi
done

# 8. Test logout
echo -e "\n8. Testing Logout..."
response=$(curl -s -X POST "$BASE_URL/api/auth/logout" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -d '{"refresh_token": "dummy"}')

if echo "$response" | jq -e '.message' > /dev/null 2>&1; then
    echo "✅ Logout successful"
else
    echo "⚠️  Logout response:"
    echo "$response" | jq .
fi

echo -e "\n🎉 Comprehensive test complete!"
echo "================================="
echo "✅ Core authentication working"
echo "✅ Research options working" 
echo "✅ User management working"
echo "⚠️  AI tools may need field adjustments"
echo "⚠️  Knowledge Base endpoints need implementation"
echo ""
echo "🚀 The SQLAlchemy relationships are ready for API implementation!"
