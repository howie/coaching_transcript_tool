#!/bin/bash

# API Authentication Tests
# Usage: ./test_auth.sh [base_url]

BASE_URL=${1:-"http://localhost:8000"}
TEMP_DIR="/tmp/api_test_$(date +%s)"
mkdir -p "$TEMP_DIR"

echo "🔐 Testing Authentication APIs"
echo "Base URL: $BASE_URL"
echo "Temp dir: $TEMP_DIR"
echo "================================"

# Test user signup
echo "📝 Testing user signup..."
SIGNUP_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X POST "$BASE_URL/api/v1/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "testuser@example.com",
    "password": "testpassword123"
  }')

SIGNUP_BODY=$(echo "$SIGNUP_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
SIGNUP_STATUS=$(echo "$SIGNUP_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Signup Status: $SIGNUP_STATUS"
echo "Signup Response: $SIGNUP_BODY" | jq '.' 2>/dev/null || echo "$SIGNUP_BODY"
echo ""

# Test user login
echo "🔑 Testing user login..."
LOGIN_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser@example.com&password=testpassword123")

LOGIN_BODY=$(echo "$LOGIN_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
LOGIN_STATUS=$(echo "$LOGIN_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Login Status: $LOGIN_STATUS"
echo "Login Response: $LOGIN_BODY" | jq '.' 2>/dev/null || echo "$LOGIN_BODY"

# Extract token for subsequent requests
if [[ $LOGIN_STATUS == "200" ]]; then
    TOKEN=$(echo "$LOGIN_BODY" | jq -r '.access_token' 2>/dev/null)
    if [[ "$TOKEN" != "null" && "$TOKEN" != "" ]]; then
        echo "$TOKEN" > "$TEMP_DIR/token.txt"
        echo "✅ Token saved: ${TOKEN:0:20}..."
    else
        echo "❌ Failed to extract token"
        TOKEN=""
    fi
else
    echo "❌ Login failed"
    TOKEN=""
fi
echo ""

# Test protected endpoint - get user profile
if [[ -n "$TOKEN" ]]; then
    echo "👤 Testing protected endpoint - get user profile..."
    PROFILE_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
      -X GET "$BASE_URL/api/v1/user/profile" \
      -H "Authorization: Bearer $TOKEN")

    PROFILE_BODY=$(echo "$PROFILE_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    PROFILE_STATUS=$(echo "$PROFILE_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

    echo "Profile Status: $PROFILE_STATUS"
    echo "Profile Response: $PROFILE_BODY" | jq '.' 2>/dev/null || echo "$PROFILE_BODY"
    echo ""
fi

# Test authentication without token (should fail)
echo "🚫 Testing endpoint without authentication (should fail)..."
UNAUTH_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/user/profile")

UNAUTH_BODY=$(echo "$UNAUTH_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
UNAUTH_STATUS=$(echo "$UNAUTH_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Unauthorized Status: $UNAUTH_STATUS"
echo "Unauthorized Response: $UNAUTH_BODY" | jq '.' 2>/dev/null || echo "$UNAUTH_BODY"
echo ""

echo "🔐 Authentication tests completed!"
echo "Token file: $TEMP_DIR/token.txt"
echo "Use this token for other API tests:"
echo "export API_TOKEN=\$(cat $TEMP_DIR/token.txt)"