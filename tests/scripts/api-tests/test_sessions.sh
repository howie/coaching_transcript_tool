#!/bin/bash

# Coaching Sessions API Tests
# Usage: ./test_sessions.sh [base_url] [token]

BASE_URL=${1:-"http://localhost:8000"}
TOKEN=${2:-""}

# Try to read token from temp file if not provided
if [[ -z "$TOKEN" ]]; then
    TEMP_TOKEN_FILE=$(ls /tmp/api_test_*/token.txt 2>/dev/null | head -1)
    if [[ -f "$TEMP_TOKEN_FILE" ]]; then
        TOKEN=$(cat "$TEMP_TOKEN_FILE")
        echo "📖 Using token from: $TEMP_TOKEN_FILE"
    fi
fi

if [[ -z "$TOKEN" ]]; then
    echo "❌ No token provided. Run ./test_auth.sh first to get a token."
    echo "Usage: $0 [base_url] [token]"
    echo "Or set API_TOKEN environment variable"
    exit 1
fi

echo "📅 Testing Coaching Sessions APIs"
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo "================================"

# Get session options - currencies
echo "💱 Testing get session currencies..."
CURRENCIES_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/sessions/options/currencies" \
  -H "Authorization: Bearer $TOKEN")

CURRENCIES_BODY=$(echo "$CURRENCIES_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
CURRENCIES_STATUS=$(echo "$CURRENCIES_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Currencies Status: $CURRENCIES_STATUS"
echo "Currencies Response: $CURRENCIES_BODY" | jq '.' 2>/dev/null || echo "$CURRENCIES_BODY"
echo ""

# Get all clients first to get a client ID for session creation
echo "👥 Getting client list for session creation..."
CLIENTS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/clients?page=1&page_size=5" \
  -H "Authorization: Bearer $TOKEN")

CLIENTS_BODY=$(echo "$CLIENTS_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
CLIENTS_STATUS=$(echo "$CLIENTS_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

CLIENT_ID=""
if [[ $CLIENTS_STATUS == "200" ]]; then
    CLIENT_ID=$(echo "$CLIENTS_BODY" | jq -r '.items[0].id' 2>/dev/null)
    if [[ "$CLIENT_ID" != "null" && "$CLIENT_ID" != "" ]]; then
        echo "✅ Found client ID: $CLIENT_ID"
    else
        echo "⚠️ No clients found, session tests may be limited"
    fi
else
    echo "❌ Failed to get clients"
fi
echo ""

# Create a test session (if we have a client)
SESSION_ID=""
if [[ -n "$CLIENT_ID" ]]; then
    echo "➕ Testing create coaching session..."
    CREATE_SESSION_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
      -X POST "$BASE_URL/api/v1/sessions" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "session_date": "'$(date -I)'",
        "client_id": "'$CLIENT_ID'",
        "duration_min": 60,
        "fee_currency": "NTD",
        "fee_amount": 2000,
        "notes": "Test session created via API test script"
      }')

    CREATE_SESSION_BODY=$(echo "$CREATE_SESSION_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    CREATE_SESSION_STATUS=$(echo "$CREATE_SESSION_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

    echo "Create Session Status: $CREATE_SESSION_STATUS"
    echo "Create Session Response: $CREATE_SESSION_BODY" | jq '.' 2>/dev/null || echo "$CREATE_SESSION_BODY"

    # Extract session ID for subsequent tests
    if [[ $CREATE_SESSION_STATUS == "200" || $CREATE_SESSION_STATUS == "201" ]]; then
        SESSION_ID=$(echo "$CREATE_SESSION_BODY" | jq -r '.id' 2>/dev/null)
        if [[ "$SESSION_ID" != "null" && "$SESSION_ID" != "" ]]; then
            echo "✅ Created session ID: $SESSION_ID"
        else
            echo "❌ Failed to extract session ID"
        fi
    else
        echo "❌ Failed to create session"
    fi
    echo ""
fi

# Get all sessions
echo "📋 Testing get all sessions..."
GET_SESSIONS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/sessions?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN")

GET_SESSIONS_BODY=$(echo "$GET_SESSIONS_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
GET_SESSIONS_STATUS=$(echo "$GET_SESSIONS_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Get Sessions Status: $GET_SESSIONS_STATUS"
echo "Get Sessions Response: $GET_SESSIONS_BODY" | jq '.' 2>/dev/null || echo "$GET_SESSIONS_BODY"

# If no SESSION_ID from creation, try to get one from the list
if [[ -z "$SESSION_ID" && $GET_SESSIONS_STATUS == "200" ]]; then
    SESSION_ID=$(echo "$GET_SESSIONS_BODY" | jq -r '.items[0].id' 2>/dev/null)
    if [[ "$SESSION_ID" != "null" && "$SESSION_ID" != "" ]]; then
        echo "📝 Using existing session ID: $SESSION_ID"
    fi
fi
echo ""

# Test get specific session (if we have an ID)
if [[ -n "$SESSION_ID" ]]; then
    echo "📅 Testing get specific session..."
    GET_SESSION_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
      -X GET "$BASE_URL/api/v1/sessions/$SESSION_ID" \
      -H "Authorization: Bearer $TOKEN")

    GET_SESSION_BODY=$(echo "$GET_SESSION_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    GET_SESSION_STATUS=$(echo "$GET_SESSION_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

    echo "Get Session Status: $GET_SESSION_STATUS"
    echo "Get Session Response: $GET_SESSION_BODY" | jq '.' 2>/dev/null || echo "$GET_SESSION_BODY"
    echo ""

    # Test update session
    echo "✏️ Testing update session..."
    UPDATE_SESSION_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
      -X PATCH "$BASE_URL/api/v1/sessions/$SESSION_ID" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "duration_min": 90,
        "notes": "Updated via API test script at '$(date)'"
      }')

    UPDATE_SESSION_BODY=$(echo "$UPDATE_SESSION_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    UPDATE_SESSION_STATUS=$(echo "$UPDATE_SESSION_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

    echo "Update Session Status: $UPDATE_SESSION_STATUS"
    echo "Update Session Response: $UPDATE_SESSION_BODY" | jq '.' 2>/dev/null || echo "$UPDATE_SESSION_BODY"
    echo ""
fi

# Test filter sessions by date range
echo "📅 Testing filter sessions by date range..."
FILTER_SESSIONS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/sessions?page=1&page_size=10&from_date=$(date -d '30 days ago' -I)&to_date=$(date -I)" \
  -H "Authorization: Bearer $TOKEN")

FILTER_SESSIONS_BODY=$(echo "$FILTER_SESSIONS_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
FILTER_SESSIONS_STATUS=$(echo "$FILTER_SESSIONS_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Filter Sessions Status: $FILTER_SESSIONS_STATUS"
echo "Filter Sessions Response: $FILTER_SESSIONS_BODY" | jq '.' 2>/dev/null || echo "$FILTER_SESSIONS_BODY"
echo ""

# Test filter sessions by client (if we have a client ID)
if [[ -n "$CLIENT_ID" ]]; then
    echo "👤 Testing filter sessions by client..."
    CLIENT_FILTER_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
      -X GET "$BASE_URL/api/v1/sessions?page=1&page_size=10&client_id=$CLIENT_ID" \
      -H "Authorization: Bearer $TOKEN")

    CLIENT_FILTER_BODY=$(echo "$CLIENT_FILTER_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    CLIENT_FILTER_STATUS=$(echo "$CLIENT_FILTER_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

    echo "Client Filter Status: $CLIENT_FILTER_STATUS"
    echo "Client Filter Response: $CLIENT_FILTER_BODY" | jq '.' 2>/dev/null || echo "$CLIENT_FILTER_BODY"
    echo ""
fi

echo "📅 Coaching Sessions API tests completed!"
if [[ -n "$SESSION_ID" ]]; then
    echo "Test session ID: $SESSION_ID"
    echo "Note: Test session was created. You may want to clean up manually."
fi