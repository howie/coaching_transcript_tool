#!/bin/bash

# Test script for Coach Profile API endpoints
# Usage: ./test_coach_profile.sh [API_BASE_URL]

set -e

# Configuration
API_BASE_URL="${1:-http://localhost:8000}"
TEST_EMAIL="coach.test@example.com"
TEST_PASSWORD="testpass123"
AUTH_TOKEN=""

echo "======================================"
echo "Testing Coach Profile API Endpoints"
echo "======================================"
echo "API Base URL: $API_BASE_URL"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_test() {
    echo -e "${YELLOW}Testing: $1${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
    echo ""
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
    echo ""
}

# Helper function to check if response is valid JSON
check_json() {
    local response="$1"
    if ! echo "$response" | jq . > /dev/null 2>&1; then
        print_error "Invalid JSON response: $response"
        exit 1
    fi
}

# Test 1: Register/Login to get auth token
print_test "User Authentication"
if command -v jq >/dev/null 2>&1; then
    # Try to register first (ignore if user already exists)
    REGISTER_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/auth/signup" \
        -H "Content-Type: application/json" \
        -d "{
            \"email\": \"$TEST_EMAIL\",
            \"name\": \"Test Coach\",
            \"password\": \"$TEST_PASSWORD\"
        }" || echo '{"error": "Registration failed"}')
    
    # Try to login
    LOGIN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/v1/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        -d "username=$TEST_EMAIL&password=$TEST_PASSWORD" || echo '{"error": "Login failed"}')
    
    check_json "$LOGIN_RESPONSE"
    
    # Extract token
    AUTH_TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // .token // .access // empty')
    
    if [ -n "$AUTH_TOKEN" ] && [ "$AUTH_TOKEN" != "null" ]; then
        print_success "Authentication successful"
    else
        print_error "Failed to get auth token. Response: $LOGIN_RESPONSE"
        exit 1
    fi
else
    print_error "jq command not found. Please install jq to run tests."
    exit 1
fi

# Test 2: Get coach profile (should be empty initially)
print_test "Get empty coach profile"
PROFILE_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/coach-profile/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json")

if [ "$PROFILE_RESPONSE" = "null" ] || [ -z "$PROFILE_RESPONSE" ]; then
    print_success "Coach profile is empty as expected"
else
    echo "Response: $PROFILE_RESPONSE"
    print_error "Expected empty profile, got response"
fi

# Test 3: Create coach profile
print_test "Create coach profile"
CREATE_PROFILE_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/coach-profile/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "display_name": "Test Coach",
        "public_email": "public.coach@example.com",
        "phone_country_code": "+1",
        "phone_number": "555-0123",
        "country": "USA",
        "city": "San Francisco",
        "timezone": "America/Los_Angeles",
        "coaching_languages": ["english", "spanish"],
        "communication_tools": {
            "zoom": true,
            "google_meet": true,
            "line": false,
            "ms_teams": false
        },
        "line_id": "testcoach",
        "coach_experience": "advanced",
        "training_institution": "ICF",
        "certifications": ["ACC", "PCC"],
        "linkedin_url": "https://linkedin.com/in/testcoach",
        "personal_website": "https://testcoach.com",
        "bio": "Experienced executive coach specializing in leadership development.",
        "specialties": ["Leadership", "Executive Coaching", "Team Building"],
        "is_public": true
    }')

check_json "$CREATE_PROFILE_RESPONSE"

# Check if creation was successful
if echo "$CREATE_PROFILE_RESPONSE" | jq -e '.id' > /dev/null; then
    PROFILE_ID=$(echo "$CREATE_PROFILE_RESPONSE" | jq -r '.id')
    print_success "Coach profile created successfully with ID: $PROFILE_ID"
else
    print_error "Failed to create coach profile: $CREATE_PROFILE_RESPONSE"
fi

# Test 4: Get coach profile (should exist now)
print_test "Get existing coach profile"
GET_PROFILE_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/coach-profile/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json")

check_json "$GET_PROFILE_RESPONSE"

if echo "$GET_PROFILE_RESPONSE" | jq -e '.display_name' > /dev/null; then
    DISPLAY_NAME=$(echo "$GET_PROFILE_RESPONSE" | jq -r '.display_name')
    print_success "Retrieved coach profile: $DISPLAY_NAME"
else
    print_error "Failed to get coach profile: $GET_PROFILE_RESPONSE"
fi

# Test 5: Update coach profile
print_test "Update coach profile"
UPDATE_PROFILE_RESPONSE=$(curl -s -X PUT "$API_BASE_URL/api/coach-profile/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "display_name": "Updated Test Coach",
        "country": "Canada",
        "city": "Toronto",
        "coaching_languages": ["english", "spanish", "french"],
        "is_public": false
    }')

check_json "$UPDATE_PROFILE_RESPONSE"

if echo "$UPDATE_PROFILE_RESPONSE" | jq -e '.display_name' > /dev/null; then
    UPDATED_NAME=$(echo "$UPDATE_PROFILE_RESPONSE" | jq -r '.display_name')
    print_success "Coach profile updated: $UPDATED_NAME"
else
    print_error "Failed to update coach profile: $UPDATE_PROFILE_RESPONSE"
fi

# Test 6: Get coaching plans (should be empty initially)
print_test "Get empty coaching plans"
PLANS_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/coach-profile/plans" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json")

check_json "$PLANS_RESPONSE"

if [ "$PLANS_RESPONSE" = "[]" ]; then
    print_success "Coaching plans are empty as expected"
else
    print_error "Expected empty plans array, got: $PLANS_RESPONSE"
fi

# Test 7: Create coaching plan
print_test "Create coaching plan"
CREATE_PLAN_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/coach-profile/plans" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "plan_type": "single_session",
        "title": "Executive Coaching Session",
        "description": "One-on-one executive coaching focused on leadership skills",
        "duration_minutes": 90,
        "number_of_sessions": 1,
        "price": 250.0,
        "currency": "USD",
        "is_active": true,
        "max_participants": 1,
        "booking_notice_hours": 24,
        "cancellation_notice_hours": 24
    }')

check_json "$CREATE_PLAN_RESPONSE"

if echo "$CREATE_PLAN_RESPONSE" | jq -e '.id' > /dev/null; then
    PLAN_ID=$(echo "$CREATE_PLAN_RESPONSE" | jq -r '.id')
    PLAN_TITLE=$(echo "$CREATE_PLAN_RESPONSE" | jq -r '.title')
    print_success "Coaching plan created: $PLAN_TITLE (ID: $PLAN_ID)"
else
    print_error "Failed to create coaching plan: $CREATE_PLAN_RESPONSE"
fi

# Test 8: Get coaching plans (should have one now)
print_test "Get existing coaching plans"
GET_PLANS_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/coach-profile/plans" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json")

check_json "$GET_PLANS_RESPONSE"

PLAN_COUNT=$(echo "$GET_PLANS_RESPONSE" | jq 'length')
if [ "$PLAN_COUNT" -gt 0 ]; then
    print_success "Retrieved $PLAN_COUNT coaching plan(s)"
else
    print_error "Failed to get coaching plans: $GET_PLANS_RESPONSE"
fi

# Test 9: Update coaching plan
if [ -n "$PLAN_ID" ] && [ "$PLAN_ID" != "null" ]; then
    print_test "Update coaching plan"
    UPDATE_PLAN_RESPONSE=$(curl -s -X PUT "$API_BASE_URL/api/coach-profile/plans/$PLAN_ID" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -H "Content-Type: application/json" \
        -d '{
            "title": "Updated Executive Coaching Session",
            "price": 300.0,
            "duration_minutes": 120,
            "is_active": false
        }')
    
    check_json "$UPDATE_PLAN_RESPONSE"
    
    if echo "$UPDATE_PLAN_RESPONSE" | jq -e '.title' > /dev/null; then
        UPDATED_TITLE=$(echo "$UPDATE_PLAN_RESPONSE" | jq -r '.title')
        UPDATED_PRICE=$(echo "$UPDATE_PLAN_RESPONSE" | jq -r '.price')
        print_success "Coaching plan updated: $UPDATED_TITLE (Price: $UPDATED_PRICE)"
    else
        print_error "Failed to update coaching plan: $UPDATE_PLAN_RESPONSE"
    fi
fi

# Test 10: Create package plan
print_test "Create package coaching plan"
CREATE_PACKAGE_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/coach-profile/plans" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "plan_type": "package",
        "title": "4-Session Leadership Package",
        "description": "Comprehensive leadership development package over 4 sessions",
        "duration_minutes": 90,
        "number_of_sessions": 4,
        "price": 900.0,
        "currency": "USD",
        "is_active": true,
        "max_participants": 1
    }')

check_json "$CREATE_PACKAGE_RESPONSE"

if echo "$CREATE_PACKAGE_RESPONSE" | jq -e '.id' > /dev/null; then
    PACKAGE_ID=$(echo "$CREATE_PACKAGE_RESPONSE" | jq -r '.id')
    PACKAGE_TITLE=$(echo "$CREATE_PACKAGE_RESPONSE" | jq -r '.title')
    PRICE_PER_SESSION=$(echo "$CREATE_PACKAGE_RESPONSE" | jq -r '.price_per_session')
    TOTAL_DURATION=$(echo "$CREATE_PACKAGE_RESPONSE" | jq -r '.total_duration_minutes')
    print_success "Package plan created: $PACKAGE_TITLE (Price per session: $PRICE_PER_SESSION, Total duration: $TOTAL_DURATION min)"
else
    print_error "Failed to create package plan: $CREATE_PACKAGE_RESPONSE"
fi

# Test 11: Get final coaching plans count
print_test "Get final coaching plans count"
FINAL_PLANS_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/coach-profile/plans" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json")

check_json "$FINAL_PLANS_RESPONSE"

FINAL_PLAN_COUNT=$(echo "$FINAL_PLANS_RESPONSE" | jq 'length')
print_success "Final coaching plans count: $FINAL_PLAN_COUNT"

# Test 12: Error handling - Try to create duplicate profile
print_test "Error handling - Duplicate profile creation"
DUPLICATE_RESPONSE=$(curl -s -X POST "$API_BASE_URL/api/coach-profile/" \
    -H "Authorization: Bearer $AUTH_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "display_name": "Duplicate Coach",
        "is_public": false
    }')

if echo "$DUPLICATE_RESPONSE" | jq -e '.detail' > /dev/null; then
    ERROR_MESSAGE=$(echo "$DUPLICATE_RESPONSE" | jq -r '.detail')
    if [[ "$ERROR_MESSAGE" == *"already exists"* ]]; then
        print_success "Duplicate profile creation properly rejected: $ERROR_MESSAGE"
    else
        print_error "Unexpected error message: $ERROR_MESSAGE"
    fi
else
    print_error "Expected error response, got: $DUPLICATE_RESPONSE"
fi

# Test 13: Delete a coaching plan
if [ -n "$PLAN_ID" ] && [ "$PLAN_ID" != "null" ]; then
    print_test "Delete coaching plan"
    DELETE_PLAN_RESPONSE=$(curl -s -X DELETE "$API_BASE_URL/api/coach-profile/plans/$PLAN_ID" \
        -H "Authorization: Bearer $AUTH_TOKEN" \
        -w "HTTP_%{http_code}")
    
    if [[ "$DELETE_PLAN_RESPONSE" == *"HTTP_204"* ]]; then
        print_success "Coaching plan deleted successfully"
        
        # Verify deletion
        VERIFY_DELETE_RESPONSE=$(curl -s -X GET "$API_BASE_URL/api/coach-profile/plans" \
            -H "Authorization: Bearer $AUTH_TOKEN" \
            -H "Content-Type: application/json")
        
        check_json "$VERIFY_DELETE_RESPONSE"
        REMAINING_COUNT=$(echo "$VERIFY_DELETE_RESPONSE" | jq 'length')
        print_success "Remaining coaching plans: $REMAINING_COUNT"
    else
        print_error "Failed to delete coaching plan: $DELETE_PLAN_RESPONSE"
    fi
fi

echo "======================================"
echo -e "${GREEN}All Coach Profile API tests completed!${NC}"
echo "======================================"