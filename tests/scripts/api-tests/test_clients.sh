#!/bin/bash

# Client Management API Tests
# Usage: ./test_clients.sh [base_url] [token]

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

echo "🧑‍💼 Testing Client Management APIs"
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo "================================"

# Get client options - sources
echo "📋 Testing get client sources..."
SOURCES_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/clients/options/sources" \
  -H "Authorization: Bearer $TOKEN")

SOURCES_BODY=$(echo "$SOURCES_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
SOURCES_STATUS=$(echo "$SOURCES_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Sources Status: $SOURCES_STATUS"
echo "Sources Response: $SOURCES_BODY" | jq '.' 2>/dev/null || echo "$SOURCES_BODY"
echo ""

# Get client options - types
echo "📋 Testing get client types..."
TYPES_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/clients/options/types" \
  -H "Authorization: Bearer $TOKEN")

TYPES_BODY=$(echo "$TYPES_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
TYPES_STATUS=$(echo "$TYPES_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Types Status: $TYPES_STATUS"
echo "Types Response: $TYPES_BODY" | jq '.' 2>/dev/null || echo "$TYPES_BODY"
echo ""

# Create a test client
echo "➕ Testing create client..."
CREATE_CLIENT_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X POST "$BASE_URL/api/v1/clients" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "name": "Test Client API",
    "email": "testclient@example.com",
    "phone": "+1234567890",
    "memo": "Created via API test script",
    "source": "網路搜尋",
    "client_type": "個人",
    "issue_types": "職涯發展, 人際關係"
  }')

CREATE_CLIENT_BODY=$(echo "$CREATE_CLIENT_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
CREATE_CLIENT_STATUS=$(echo "$CREATE_CLIENT_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Create Client Status: $CREATE_CLIENT_STATUS"
echo "Create Client Response: $CREATE_CLIENT_BODY" | jq '.' 2>/dev/null || echo "$CREATE_CLIENT_BODY"

# Extract client ID for subsequent tests
CLIENT_ID=""
if [[ $CREATE_CLIENT_STATUS == "200" || $CREATE_CLIENT_STATUS == "201" ]]; then
    CLIENT_ID=$(echo "$CREATE_CLIENT_BODY" | jq -r '.id' 2>/dev/null)
    if [[ "$CLIENT_ID" != "null" && "$CLIENT_ID" != "" ]]; then
        echo "✅ Created client ID: $CLIENT_ID"
    else
        echo "❌ Failed to extract client ID"
    fi
else
    echo "❌ Failed to create client"
fi
echo ""

# Get all clients
echo "📋 Testing get all clients..."
GET_CLIENTS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/clients?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN")

GET_CLIENTS_BODY=$(echo "$GET_CLIENTS_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
GET_CLIENTS_STATUS=$(echo "$GET_CLIENTS_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Get Clients Status: $GET_CLIENTS_STATUS"
echo "Get Clients Response: $GET_CLIENTS_BODY" | jq '.' 2>/dev/null || echo "$GET_CLIENTS_BODY"

# If no CLIENT_ID from creation, try to get one from the list
if [[ -z "$CLIENT_ID" && $GET_CLIENTS_STATUS == "200" ]]; then
    CLIENT_ID=$(echo "$GET_CLIENTS_BODY" | jq -r '.items[0].id' 2>/dev/null)
    if [[ "$CLIENT_ID" != "null" && "$CLIENT_ID" != "" ]]; then
        echo "📝 Using existing client ID: $CLIENT_ID"
    fi
fi
echo ""

# Test get specific client (if we have an ID)
if [[ -n "$CLIENT_ID" ]]; then
    echo "👤 Testing get specific client..."
    GET_CLIENT_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
      -X GET "$BASE_URL/api/v1/clients/$CLIENT_ID" \
      -H "Authorization: Bearer $TOKEN")

    GET_CLIENT_BODY=$(echo "$GET_CLIENT_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    GET_CLIENT_STATUS=$(echo "$GET_CLIENT_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

    echo "Get Client Status: $GET_CLIENT_STATUS"
    echo "Get Client Response: $GET_CLIENT_BODY" | jq '.' 2>/dev/null || echo "$GET_CLIENT_BODY"
    echo ""

    # Test update client
    echo "✏️ Testing update client..."
    UPDATE_CLIENT_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
      -X PATCH "$BASE_URL/api/v1/clients/$CLIENT_ID" \
      -H "Content-Type: application/json" \
      -H "Authorization: Bearer $TOKEN" \
      -d '{
        "memo": "Updated via API test script at '$(date)'",
        "phone": "+9876543210"
      }')

    UPDATE_CLIENT_BODY=$(echo "$UPDATE_CLIENT_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
    UPDATE_CLIENT_STATUS=$(echo "$UPDATE_CLIENT_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

    echo "Update Client Status: $UPDATE_CLIENT_STATUS"
    echo "Update Client Response: $UPDATE_CLIENT_BODY" | jq '.' 2>/dev/null || echo "$UPDATE_CLIENT_BODY"
    echo ""
fi

# Test search clients
echo "🔍 Testing search clients..."
SEARCH_CLIENTS_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/clients?page=1&page_size=10&query=Test" \
  -H "Authorization: Bearer $TOKEN")

SEARCH_CLIENTS_BODY=$(echo "$SEARCH_CLIENTS_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
SEARCH_CLIENTS_STATUS=$(echo "$SEARCH_CLIENTS_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Search Clients Status: $SEARCH_CLIENTS_STATUS"
echo "Search Clients Response: $SEARCH_CLIENTS_BODY" | jq '.' 2>/dev/null || echo "$SEARCH_CLIENTS_BODY"
echo ""

echo "🧑‍💼 Client Management API tests completed!"
if [[ -n "$CLIENT_ID" ]]; then
    echo "Test client ID: $CLIENT_ID"
    echo "Note: Test client was created. You may want to clean up manually."
fi