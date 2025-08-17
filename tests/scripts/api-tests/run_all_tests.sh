#!/bin/bash

# Main API Test Runner
# Usage: ./run_all_tests.sh [base_url] [skip_cleanup]

BASE_URL=${1:-"http://localhost:8000"}
SKIP_CLEANUP=${2:-"false"}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMP_DIR="/tmp/api_test_$(date +%s)"

echo "🚀 Running All API Tests"
echo "========================"
echo "Base URL: $BASE_URL"
echo "Script Dir: $SCRIPT_DIR"
echo "Temp Dir: $TEMP_DIR"
echo "Skip Cleanup: $SKIP_CLEANUP"
echo ""

# Check if API server is running
echo "🏥 Checking API server health..."
HEALTH_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" "$BASE_URL/api/health" 2>/dev/null)
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

if [[ "$HEALTH_STATUS" != "200" ]]; then
    echo "❌ API server is not responding at $BASE_URL"
    echo "Please make sure the API server is running:"
    echo "  cd /path/to/your/project"
    echo "  make run-api"
    echo ""
    echo "Or check if it's running on a different port."
    exit 1
else
    echo "✅ API server is healthy"
fi
echo ""

# Make scripts executable
chmod +x "$SCRIPT_DIR"/*.sh

# Test 1: Authentication
echo "🔐 Running Authentication Tests..."
echo "=================================="
if [[ -f "$SCRIPT_DIR/test_auth.sh" ]]; then
    bash "$SCRIPT_DIR/test_auth.sh" "$BASE_URL"
    AUTH_EXIT_CODE=$?
else
    echo "❌ test_auth.sh not found"
    AUTH_EXIT_CODE=1
fi
echo ""

# Check if we got a token
TOKEN=""
TEMP_TOKEN_FILE=$(ls /tmp/api_test_*/token.txt 2>/dev/null | head -1)
if [[ -f "$TEMP_TOKEN_FILE" ]]; then
    TOKEN=$(cat "$TEMP_TOKEN_FILE")
    echo "✅ Token acquired for subsequent tests"
else
    echo "❌ No token found. Cannot proceed with authenticated tests."
    exit 1
fi
echo ""

# Test 2: Client Management
echo "🧑‍💼 Running Client Management Tests..."
echo "====================================="
if [[ -f "$SCRIPT_DIR/test_clients.sh" ]]; then
    bash "$SCRIPT_DIR/test_clients.sh" "$BASE_URL" "$TOKEN"
    CLIENT_EXIT_CODE=$?
else
    echo "❌ test_clients.sh not found"
    CLIENT_EXIT_CODE=1
fi
echo ""

# Test 3: Coaching Sessions
echo "📅 Running Coaching Sessions Tests..."
echo "===================================="
if [[ -f "$SCRIPT_DIR/test_sessions.sh" ]]; then
    bash "$SCRIPT_DIR/test_sessions.sh" "$BASE_URL" "$TOKEN"
    SESSIONS_EXIT_CODE=$?
else
    echo "❌ test_sessions.sh not found"
    SESSIONS_EXIT_CODE=1
fi
echo ""

# Test 4: Dashboard Summary
echo "📊 Running Dashboard Summary Tests..."
echo "===================================="
if [[ -f "$SCRIPT_DIR/test_dashboard.sh" ]]; then
    bash "$SCRIPT_DIR/test_dashboard.sh" "$BASE_URL" "$TOKEN"
    DASHBOARD_EXIT_CODE=$?
else
    echo "❌ test_dashboard.sh not found"
    DASHBOARD_EXIT_CODE=1
fi
echo ""

# Summary
echo "📝 Test Results Summary"
echo "======================"
echo "Authentication Tests: $([ $AUTH_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Client Management Tests: $([ $CLIENT_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Coaching Sessions Tests: $([ $SESSIONS_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo "Dashboard Summary Tests: $([ $DASHBOARD_EXIT_CODE -eq 0 ] && echo "✅ PASSED" || echo "❌ FAILED")"
echo ""

# Count overall results
TOTAL_TESTS=4
PASSED_TESTS=0
[ $AUTH_EXIT_CODE -eq 0 ] && ((PASSED_TESTS++))
[ $CLIENT_EXIT_CODE -eq 0 ] && ((PASSED_TESTS++))
[ $SESSIONS_EXIT_CODE -eq 0 ] && ((PASSED_TESTS++))
[ $DASHBOARD_EXIT_CODE -eq 0 ] && ((PASSED_TESTS++))

echo "Overall Results: $PASSED_TESTS/$TOTAL_TESTS tests passed"

# Cleanup
if [[ "$SKIP_CLEANUP" != "true" ]]; then
    echo ""
    echo "🧹 Cleaning up temporary files..."
    rm -rf /tmp/api_test_*
    echo "✅ Cleanup completed"
else
    echo ""
    echo "🔒 Skipping cleanup. Token file preserved at:"
    echo "$TEMP_TOKEN_FILE"
fi

# Exit with appropriate code
if [[ $PASSED_TESTS -eq $TOTAL_TESTS ]]; then
    echo ""
    echo "🎉 All tests passed! Your API is working correctly."
    exit 0
else
    echo ""
    echo "⚠️  Some tests failed. Please check the output above for details."
    exit 1
fi