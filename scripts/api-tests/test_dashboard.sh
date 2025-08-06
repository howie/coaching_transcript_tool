#!/bin/bash

# Dashboard Summary API Tests
# Usage: ./test_dashboard.sh [base_url] [token]

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

echo "📊 Testing Dashboard Summary API"
echo "Base URL: $BASE_URL"
echo "Token: ${TOKEN:0:20}..."
echo "================================"

# Test dashboard summary without month parameter (current month)
echo "📈 Testing dashboard summary (current month)..."
SUMMARY_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/dashboard/summary" \
  -H "Authorization: Bearer $TOKEN")

SUMMARY_BODY=$(echo "$SUMMARY_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
SUMMARY_STATUS=$(echo "$SUMMARY_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Summary Status: $SUMMARY_STATUS"
echo "Summary Response: $SUMMARY_BODY" | jq '.' 2>/dev/null || echo "$SUMMARY_BODY"
echo ""

# Parse and display the summary data in a more readable format
if [[ $SUMMARY_STATUS == "200" ]]; then
    echo "📊 Dashboard Statistics Summary:"
    echo "================================"
    
    TOTAL_MINUTES=$(echo "$SUMMARY_BODY" | jq -r '.total_minutes' 2>/dev/null)
    CURRENT_MONTH_MINUTES=$(echo "$SUMMARY_BODY" | jq -r '.current_month_minutes' 2>/dev/null)
    TRANSCRIPTS_COUNT=$(echo "$SUMMARY_BODY" | jq -r '.transcripts_converted_count' 2>/dev/null)
    UNIQUE_CLIENTS=$(echo "$SUMMARY_BODY" | jq -r '.unique_clients_total' 2>/dev/null)
    REVENUE=$(echo "$SUMMARY_BODY" | jq -r '.current_month_revenue_by_currency' 2>/dev/null)
    
    if [[ "$TOTAL_MINUTES" != "null" && "$TOTAL_MINUTES" != "" ]]; then
        TOTAL_HOURS=$(echo "scale=1; $TOTAL_MINUTES / 60" | bc 2>/dev/null || echo "N/A")
        echo "⏱️  Total Hours: $TOTAL_HOURS hours ($TOTAL_MINUTES minutes)"
    fi
    
    if [[ "$CURRENT_MONTH_MINUTES" != "null" && "$CURRENT_MONTH_MINUTES" != "" ]]; then
        MONTHLY_HOURS=$(echo "scale=1; $CURRENT_MONTH_MINUTES / 60" | bc 2>/dev/null || echo "N/A")
        echo "📅 Monthly Hours: $MONTHLY_HOURS hours ($CURRENT_MONTH_MINUTES minutes)"
    fi
    
    if [[ "$TRANSCRIPTS_COUNT" != "null" && "$TRANSCRIPTS_COUNT" != "" ]]; then
        echo "📄 Total Transcripts: $TRANSCRIPTS_COUNT"
    fi
    
    if [[ "$UNIQUE_CLIENTS" != "null" && "$UNIQUE_CLIENTS" != "" ]]; then
        echo "👥 Total Clients: $UNIQUE_CLIENTS"
    fi
    
    if [[ "$REVENUE" != "null" && "$REVENUE" != "{}" ]]; then
        echo "💰 Monthly Revenue by Currency:"
        echo "$REVENUE" | jq -r 'to_entries[] | "   \(.key): \(.value)"' 2>/dev/null || echo "   $REVENUE"
    else
        echo "💰 Monthly Revenue: No revenue data"
    fi
    echo ""
fi

# Test dashboard summary with specific month parameter
SPECIFIC_MONTH=$(date -d '1 month ago' '+%Y-%m')
echo "📈 Testing dashboard summary for specific month ($SPECIFIC_MONTH)..."
MONTHLY_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/dashboard/summary?month=$SPECIFIC_MONTH" \
  -H "Authorization: Bearer $TOKEN")

MONTHLY_BODY=$(echo "$MONTHLY_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
MONTHLY_STATUS=$(echo "$MONTHLY_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Monthly Summary Status: $MONTHLY_STATUS"
echo "Monthly Summary Response: $MONTHLY_BODY" | jq '.' 2>/dev/null || echo "$MONTHLY_BODY"
echo ""

# Test with invalid month format (should fail)
echo "❌ Testing dashboard summary with invalid month format (should fail)..."
INVALID_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/dashboard/summary?month=invalid-date" \
  -H "Authorization: Bearer $TOKEN")

INVALID_BODY=$(echo "$INVALID_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
INVALID_STATUS=$(echo "$INVALID_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Invalid Month Status: $INVALID_STATUS"
echo "Invalid Month Response: $INVALID_BODY" | jq '.' 2>/dev/null || echo "$INVALID_BODY"
echo ""

# Test without authentication (should fail)
echo "🚫 Testing dashboard summary without authentication (should fail)..."
UNAUTH_RESPONSE=$(curl -s -w "HTTPSTATUS:%{http_code}" \
  -X GET "$BASE_URL/api/v1/dashboard/summary")

UNAUTH_BODY=$(echo "$UNAUTH_RESPONSE" | sed -E 's/HTTPSTATUS:[0-9]{3}$//')
UNAUTH_STATUS=$(echo "$UNAUTH_RESPONSE" | tr -d '\n' | sed -E 's/.*HTTPSTATUS:([0-9]{3})$/\1/')

echo "Unauthorized Status: $UNAUTH_STATUS"
echo "Unauthorized Response: $UNAUTH_BODY" | jq '.' 2>/dev/null || echo "$UNAUTH_BODY"
echo ""

echo "📊 Dashboard Summary API tests completed!"

# If we got valid summary data, show a final summary
if [[ $SUMMARY_STATUS == "200" ]]; then
    echo ""
    echo "🎯 Key Dashboard Numbers (for frontend verification):"
    echo "===================================================="
    
    TOTAL_MINUTES=$(echo "$SUMMARY_BODY" | jq -r '.total_minutes' 2>/dev/null)
    CURRENT_MONTH_MINUTES=$(echo "$SUMMARY_BODY" | jq -r '.current_month_minutes' 2>/dev/null)
    TRANSCRIPTS_COUNT=$(echo "$SUMMARY_BODY" | jq -r '.transcripts_converted_count' 2>/dev/null)
    UNIQUE_CLIENTS=$(echo "$SUMMARY_BODY" | jq -r '.unique_clients_total' 2>/dev/null)
    
    if [[ "$TOTAL_MINUTES" != "null" ]]; then
        TOTAL_HOURS_ROUNDED=$(echo "($TOTAL_MINUTES + 30) / 60" | bc 2>/dev/null || echo "0")
        echo "Total Hours (rounded): $TOTAL_HOURS_ROUNDED"
    fi
    
    if [[ "$CURRENT_MONTH_MINUTES" != "null" ]]; then
        MONTHLY_HOURS_ROUNDED=$(echo "($CURRENT_MONTH_MINUTES + 30) / 60" | bc 2>/dev/null || echo "0")
        echo "Monthly Hours (rounded): $MONTHLY_HOURS_ROUNDED"
    fi
    
    echo "Total Transcripts: ${TRANSCRIPTS_COUNT:-0}"
    echo "Total Clients: ${UNIQUE_CLIENTS:-0}"
    
    echo ""
    echo "✅ These numbers should match what you see in the Dashboard UI!"
fi