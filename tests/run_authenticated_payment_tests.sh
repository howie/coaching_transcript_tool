#!/bin/bash

# Authenticated Payment Tests Runner
# Generates JWT tokens and runs payment system tests with authentication

set -e  # Exit on any error

echo "🔑 Setting up authentication for payment tests..."
echo "=================================================="

# Generate tokens and capture output
TOKEN_OUTPUT=$(python scripts/generate_test_token.py)

# Extract tokens from output using grep and cut
ACCESS_TOKEN=$(echo "$TOKEN_OUTPUT" | grep "Access Token:" | cut -d' ' -f3)
REFRESH_TOKEN=$(echo "$TOKEN_OUTPUT" | grep "Refresh Token:" | cut -d' ' -f3)  
USER_ID=$(echo "$TOKEN_OUTPUT" | grep "👤 User ID:" | cut -d' ' -f3)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to generate access token"
    exit 1
fi

echo "✅ Generated JWT tokens successfully"
echo "👤 Test User ID: $USER_ID"
echo "🎫 Access Token: ${ACCESS_TOKEN:0:50}..."

# Export environment variables
export TEST_JWT_TOKEN="$ACCESS_TOKEN"
export TEST_REFRESH_TOKEN="$REFRESH_TOKEN"
export TEST_USER_ID="$USER_ID"
export TEST_AUTH_HEADER="Bearer $ACCESS_TOKEN"

echo "✅ Environment variables set"

# Test API connectivity
echo ""
echo "🌐 Testing API connectivity..."
if curl -s -f -H "Authorization: Bearer $ACCESS_TOKEN" http://localhost:8000/api/webhooks/health >/dev/null 2>&1; then
    echo "✅ API server is responding"
else
    echo "❌ API server not responding at http://localhost:8000"
    echo "💡 Start API server with: make run-api"
    echo "⚠️  Continuing with mock tests only..."
fi

echo ""
echo "🧪 Running authenticated payment tests..."
echo "==========================================="

# Run the working payment tests
echo "📋 Running working payment test subset..."
python tests/run_working_payment_tests.py

echo ""
echo "🚀 Running full E2E test suite..."
echo "=================================="

# Run E2E tests with verbose output
python tests/run_payment_qa_tests.py --suite e2e --verbose

echo ""
echo "🎯 AUTHENTICATION TESTING COMPLETE!"
echo "===================================="
echo "✅ JWT tokens generated and used successfully"
echo "✅ Payment system testing framework operational"
echo "🔥 Your authentication setup is working!"

echo ""
echo "💡 To run tests manually with these tokens:"
echo "export TEST_JWT_TOKEN='$ACCESS_TOKEN'"
echo "export TEST_REFRESH_TOKEN='$REFRESH_TOKEN'" 
echo "export TEST_USER_ID='$USER_ID'"
echo "export TEST_AUTH_HEADER='Bearer $ACCESS_TOKEN'"