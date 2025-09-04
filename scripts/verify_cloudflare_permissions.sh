#!/bin/bash

# Cloudflare API Token Permission Verification Script
# This script tests the required permissions for Terraform Cloudflare provider

API_TOKEN="tWV93B5h7dOy4c8bNti3yZuSzmouJ3px7e2_dfA8"
ZONE_ID="bc739ceadc7d4178226190705bc3ca21"
ACCOUNT_ID="4c63dd410022db83feece48b04d68976"

echo "🔍 Verifying Cloudflare API Token Permissions"
echo "============================================="
echo ""

# Function to test API endpoint
test_endpoint() {
    local description="$1"
    local method="$2"
    local endpoint="$3"
    local expected_permission="$4"
    
    echo -n "Testing: $description... "
    
    response=$(curl -s -X "$method" "$endpoint" \
        -H "Authorization: Bearer $API_TOKEN" \
        -H "Content-Type: application/json")
    
    if echo "$response" | grep -q '"success":true'; then
        echo "✅ PASS"
        return 0
    elif echo "$response" | grep -q '"code":9109'; then
        echo "❌ FAIL - Unauthorized (Missing: $expected_permission)"
        return 1
    elif echo "$response" | grep -q '"code":10000'; then
        echo "❌ FAIL - Authentication Error"
        return 1
    else
        echo "⚠️  UNKNOWN - $(echo "$response" | jq -r '.errors[0].message' 2>/dev/null || echo "$response")"
        return 1
    fi
}

echo "## Core Permissions"
echo "-------------------"

# Test Zone access
test_endpoint "Zone Access" "GET" "https://api.cloudflare.com/client/v4/zones/$ZONE_ID" "Zone:Zone:Read"

# Test DNS Records
test_endpoint "DNS Records Read" "GET" "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" "Zone:DNS:Read"

# Test Zone Settings
test_endpoint "Zone Settings Read" "GET" "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/settings" "Zone:Zone Settings:Read"

# Test Page Rules
test_endpoint "Page Rules Read" "GET" "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/pagerules" "Zone:Page Rules:Read"

# Test Account Access
test_endpoint "Account Access" "GET" "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID" "Account:Account Settings:Read"

# Test Pages Projects
test_endpoint "Pages Projects Read" "GET" "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/pages/projects" "Account:Cloudflare Pages:Read"

# Test Rulesets (WAF)
test_endpoint "Rulesets Read" "GET" "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/rulesets" "Zone:WAF:Read"

echo ""
echo "## Required Token Permissions"
echo "=============================="
echo ""
echo "To fix the authentication issues, update your Cloudflare API token with these permissions:"
echo ""
echo "📋 **Account Permissions:**"
echo "   • Account Settings:Read"
echo "   • Cloudflare Pages:Edit"
echo ""
echo "🌐 **Zone Permissions (for zone: doxa.com.tw):**"
echo "   • Zone:Read"
echo "   • Zone Settings:Edit"
echo "   • DNS:Edit" 
echo "   • Page Rules:Edit"
echo "   • WAF:Edit"
echo ""
echo "🔗 **Update Token:** https://dash.cloudflare.com/profile/api-tokens"
echo ""
echo "Token ID: 4f7d4266902024d77456ebf9dfdcf222"
echo "Current Status: Valid but limited permissions"