# Test Authentication Setup Guide

This guide explains how to set up authentication tokens for running payment system tests.

## Quick Setup

### 1. Create Test User and Generate Tokens

```bash
# Create test user and generate JWT tokens
python scripts/setup_test_auth.py --create-test-user --export-env
```

This will:
- Create a test user in your database with PRO plan
- Generate valid JWT access and refresh tokens  
- Output environment variable export commands

### 2. Set Environment Variables

Copy and run the export commands from step 1:

```bash
export TEST_JWT_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
export TEST_REFRESH_TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
export TEST_USER_ID='12345678-1234-1234-1234-123456789abc'
export TEST_AUTH_HEADER='Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...'
```

### 3. Verify Authentication

```bash
# Test that your token works
curl -H "Authorization: Bearer $TEST_JWT_TOKEN" \
     http://localhost:8000/api/v1/auth/me
```

You should see your test user data returned.

### 4. Run Payment Tests

```bash
# Run all payment tests with authentication
python tests/run_payment_qa_tests.py --suite e2e --verbose

# Or run the working subset
python tests/run_working_payment_tests.py
```

## Advanced Usage

### Generate Tokens for Existing User

```bash
# If you already have a test user
python scripts/setup_test_auth.py --generate-token --user-id=<your-user-uuid> --export-env
```

### Validate Existing Token

```bash
# Check if a token is still valid
python scripts/setup_test_auth.py --validate "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### Create Custom Test User

```bash
# Create user with custom email and name
python scripts/setup_test_auth.py --create-test-user \
    --email "custom@test.com" \
    --name "Custom Test User" \
    --export-env
```

## Troubleshooting

### "SECRET_KEY not configured"
Make sure your `.env` file has the SECRET_KEY set:
```env
SECRET_KEY=your_secret_key_here
```

### "Database connection error"
Ensure your database is running and DATABASE_URL is configured:
```bash
# Start local PostgreSQL
make run-db

# Or check connection
python -c "from coaching_assistant.core.database import get_db; print('DB OK')"
```

### "Token validation failed"
Your token may have expired. Generate a new one:
```bash
python scripts/setup_test_auth.py --generate-token --user-id=$TEST_USER_ID --export-env
```

### "User not found"
The test user may not exist in your database. Create one:
```bash
python scripts/setup_test_auth.py --create-test-user --export-env
```

## Test Categories

With authentication set up, you can run different test categories:

### 1. End-to-End Tests (Require Auth)
```bash
python tests/run_payment_qa_tests.py --suite e2e
```
- Complete subscription authorization flows
- Payment failure scenarios
- Webhook processing

### 2. API Compatibility Tests (No Auth Required)
```bash
python tests/run_payment_qa_tests.py --suite browser  
```
- CORS headers validation
- Content-type compatibility
- Character encoding

### 3. Regression Tests (Mixed)
```bash
python tests/run_payment_qa_tests.py --suite regression
```
- CheckMacValue calculation fixes
- Security vulnerability prevention
- Payment amount precision

## Environment Variables Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `TEST_JWT_TOKEN` | Access token for API calls | `eyJhbGciOiJIUzI1NiIs...` |
| `TEST_REFRESH_TOKEN` | Refresh token for token renewal | `eyJhbGciOiJIUzI1NiIs...` |
| `TEST_USER_ID` | UUID of test user | `12345678-1234-1234...` |
| `TEST_AUTH_HEADER` | Full Authorization header | `Bearer eyJhbGciOiJIUzI1...` |

## One-Line Setup

For convenience, you can set up everything in one command:

```bash
# Complete authentication setup and test run
python scripts/setup_test_auth.py --create-test-user --export-env && \
eval $(python scripts/setup_test_auth.py --generate-token --user-id=$(python scripts/setup_test_auth.py --create-test-user | grep "ID:" | cut -d' ' -f4 | tr -d ')') --export-env | grep export) && \
python tests/run_working_payment_tests.py
```

## Success Indicators

When authentication is working correctly, you should see:

- ✅ Token validation passed
- ✅ API Server: Connected and healthy  
- ✅ GET /api/v1/auth/me → 200 OK
- ✅ Multiple tests passing in test runner

## Next Steps

Once authentication is set up:

1. **Run Full Test Suite**: `python tests/run_payment_qa_tests.py`
2. **Check Coverage**: `python tests/run_payment_qa_tests.py --coverage`
3. **Generate Report**: `python tests/run_payment_qa_tests.py --report`
4. **Production Deploy**: Tests validate system is ready

Your payment system testing framework is now fully operational! 🚀