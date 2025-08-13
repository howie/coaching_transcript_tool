#!/bin/bash

# Test script for get client last session API

API_URL="http://localhost:8000/api/v1"
EMAIL="test@example.com"
PASSWORD="test123"

echo "Testing Client Last Session API..."
echo "=================================="

# 1. Login to get token
echo "1. Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ]; then
  echo "❌ Failed to login. Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful"

# 2. Get clients
echo -e "\n2. Getting clients..."
CLIENTS_RESPONSE=$(curl -s -X GET "$API_URL/clients" \
  -H "Authorization: Bearer $TOKEN")

FIRST_CLIENT_ID=$(echo $CLIENTS_RESPONSE | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['items'][0]['id'] if data.get('items') else '')")

if [ -z "$FIRST_CLIENT_ID" ]; then
  echo "❌ No clients found. Response: $CLIENTS_RESPONSE"
  echo "Creating a test client..."
  
  CREATE_CLIENT_RESPONSE=$(curl -s -X POST "$API_URL/clients" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test Client","email":"client@test.com"}')
  
  FIRST_CLIENT_ID=$(echo $CREATE_CLIENT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")
  
  if [ -z "$FIRST_CLIENT_ID" ]; then
    echo "❌ Failed to create client. Response: $CREATE_CLIENT_RESPONSE"
    exit 1
  fi
  echo "✅ Created test client with ID: $FIRST_CLIENT_ID"
else
  echo "✅ Found client with ID: $FIRST_CLIENT_ID"
fi

# 3. Test get last session (should be null initially)
echo -e "\n3. Getting last session for client..."
LAST_SESSION_RESPONSE=$(curl -s -X GET "$API_URL/coaching-sessions/clients/$FIRST_CLIENT_ID/last-session" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $LAST_SESSION_RESPONSE"

# 4. Create a coaching session
echo -e "\n4. Creating a coaching session..."
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/coaching-sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"session_date\": \"2024-01-15\",
    \"client_id\": \"$FIRST_CLIENT_ID\",
    \"duration_min\": 90,
    \"fee_currency\": \"USD\",
    \"fee_amount\": 150
  }")

SESSION_ID=$(echo $SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))")

if [ -z "$SESSION_ID" ]; then
  echo "❌ Failed to create session. Response: $SESSION_RESPONSE"
else
  echo "✅ Created session with ID: $SESSION_ID"
fi

# 5. Test get last session again (should return the session we just created)
echo -e "\n5. Getting last session again..."
LAST_SESSION_RESPONSE=$(curl -s -X GET "$API_URL/coaching-sessions/clients/$FIRST_CLIENT_ID/last-session" \
  -H "Authorization: Bearer $TOKEN")

echo "Response: $LAST_SESSION_RESPONSE"

# Parse and verify the response
DURATION=$(echo $LAST_SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('duration_min', ''))")
CURRENCY=$(echo $LAST_SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('fee_currency', ''))")
AMOUNT=$(echo $LAST_SESSION_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('fee_amount', ''))")

if [ "$DURATION" = "90" ] && [ "$CURRENCY" = "USD" ] && [ "$AMOUNT" = "150" ]; then
  echo "✅ Last session data matches expected values!"
  echo "   Duration: $DURATION min"
  echo "   Currency: $CURRENCY"
  echo "   Amount: $AMOUNT"
else
  echo "❌ Last session data does not match expected values"
  echo "   Expected: 90 min, USD, 150"
  echo "   Got: $DURATION min, $CURRENCY, $AMOUNT"
fi

echo -e "\n=================================="
echo "Test completed!"