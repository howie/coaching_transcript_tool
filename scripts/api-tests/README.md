# API Testing Scripts

This directory contains comprehensive curl-based API testing scripts for the Coaching Transcript Tool backend API.

## Quick Start

1. **Start the API server** (if not already running):
   ```bash
   cd /path/to/your/project
   make run-api
   ```

2. **Run all tests**:
   ```bash
   chmod +x scripts/api-tests/*.sh
   ./scripts/api-tests/run_all_tests.sh
   ```

3. **Or test individual APIs**:
   ```bash
   ./scripts/api-tests/test_auth.sh
   ./scripts/api-tests/test_dashboard.sh
   ```

## Available Test Scripts

### 🔐 `test_auth.sh` - Authentication Tests
Tests user registration, login, and token-based authentication.

**Usage:**
```bash
./test_auth.sh [base_url]
```

**What it tests:**
- User signup
- User login  
- Token extraction
- Protected endpoint access
- Unauthorized access (should fail)

### 🧑‍💼 `test_clients.sh` - Client Management Tests  
Tests all client CRUD operations and options.

**Usage:**
```bash
./test_clients.sh [base_url] [token]
```

**What it tests:**
- Get client sources/types options
- Create new client
- List all clients
- Get specific client
- Update client
- Search clients

### 📅 `test_sessions.sh` - Coaching Sessions Tests
Tests coaching session management and filtering.

**Usage:**
```bash
./test_sessions.sh [base_url] [token]
```

**What it tests:**
- Get currency options
- Create coaching session
- List all sessions
- Get specific session
- Update session
- Filter by date range
- Filter by client

### 📊 `test_dashboard.sh` - Dashboard Summary Tests
Tests dashboard statistics and proves the data is being returned correctly.

**Usage:**
```bash
./test_dashboard.sh [base_url] [token]
```

**What it tests:**
- Dashboard summary (current month)
- Dashboard summary (specific month)
- Invalid month format (should fail)
- Unauthorized access (should fail)

**Key metrics verified:**
- Total hours (from total_minutes)
- Monthly hours (from current_month_minutes)
- Total transcripts converted
- Total unique clients
- Monthly revenue by currency

### 🚀 `run_all_tests.sh` - Main Test Runner
Executes all test scripts in sequence with proper setup and cleanup.

**Usage:**
```bash
./run_all_tests.sh [base_url] [skip_cleanup]
```

**Features:**
- Health check before testing
- Token management across tests  
- Comprehensive test summary
- Automatic cleanup (optional)

## Authentication Flow

The scripts follow this authentication pattern:

1. `test_auth.sh` creates a user and gets a JWT token
2. Token is saved to `/tmp/api_test_*/token.txt`
3. Other scripts automatically find and use this token
4. Token is cleaned up after tests (unless `skip_cleanup=true`)

## Environment Configuration

**Default settings:**
- Base URL: `http://localhost:8000`
- Token auto-discovery from temp files
- JSON pretty-printing with `jq`

**Override base URL:**
```bash
./run_all_tests.sh https://your-api-domain.com
```

**Use existing token:**
```bash
export API_TOKEN="your-jwt-token-here"
./test_dashboard.sh
```

## Expected Dashboard Numbers

The `test_dashboard.sh` script will show you the exact numbers that should appear in your Dashboard UI:

```
🎯 Key Dashboard Numbers (for frontend verification):
====================================================
Total Hours (rounded): 4
Monthly Hours (rounded): 2  
Total Transcripts: 0
Total Clients: 2
```

These numbers should match exactly what you see in the web interface.

## Troubleshooting

**API server not responding:**
```bash
# Check if server is running
curl http://localhost:8000/api/health

# Start the server
make run-api
```

**Permission denied:**
```bash
chmod +x scripts/api-tests/*.sh
```

**jq not found (optional):**
```bash
# Install jq for pretty JSON formatting
# macOS: brew install jq
# Ubuntu: sudo apt-get install jq
```

## Test Data

The scripts create test data during execution:
- Test user: `testuser@example.com`
- Test client: `Test Client API`
- Test coaching session with current date

**Cleanup:** Test data is left in the database for manual verification. Clean up manually if needed.

## Script Dependencies

- `curl` (required)
- `jq` (optional, for pretty JSON output)
- `bc` (for mathematical calculations)
- Standard Unix tools: `sed`, `grep`, `date`

## Exit Codes

- `0` - All tests passed
- `1` - Some tests failed or setup issues
- Check script output for detailed error information