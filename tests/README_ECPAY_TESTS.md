# ECPay Integration Test Suite

This directory contains comprehensive tests for the ECPay SaaS subscription integration, designed to prevent regression bugs and ensure reliable payment processing.

## Test Structure

### Unit Tests (`tests/unit/`)
- `test_merchant_trade_no_generation.py` - MerchantTradeNo generation logic
- `test_ecpay_api_response_validation.py` - API response handling and validation
- `test_ecpay_merchant_trade_no.py` - Utility test script

### Integration Tests (`tests/integration/`)
- `test_ecpay_integration.py` - Field validation and service integration
- `test_ecpay_flow.py` - End-to-end flow validation

### E2E Tests (`tests/e2e/`)
- `test_ecpay_authorization_flow.py` - Complete authorization workflow

## Running Tests

### Quick Test Run
```bash
# From project root
python tests/run_ecpay_tests.py
```

### Test Categories
```bash
# Unit tests only
python tests/run_ecpay_tests.py --unit-only

# Integration tests only  
python tests/run_ecpay_tests.py --integration-only

# With verbose output
python tests/run_ecpay_tests.py --verbose

# With coverage report
python tests/run_ecpay_tests.py --coverage
```

### Individual Test Files
```bash
# Unit tests
python -m pytest tests/unit/test_merchant_trade_no_generation.py -v
python -m pytest tests/unit/test_ecpay_api_response_validation.py -v

# Integration tests
python -m pytest tests/integration/test_ecpay_integration.py -v

# E2E tests
python -m pytest tests/e2e/test_ecpay_authorization_flow.py -v
```

## Bug Prevention

### Original Bug Fixed: MerchantTradeNo Length Limit
**Problem**: ECPay API error 10200052 - "MerchantTradeNo Error"
**Root Cause**: Generated MerchantTradeNo was 21 characters, exceeding ECPay's 20-character limit
**Solution**: Changed format from `SUB{full_timestamp}{user_prefix}` to `SUB{timestamp_6}{user_prefix}`

### Tests That Prevent This Bug
- `test_merchant_trade_no_length_constraint()` - Ensures length never exceeds 20 chars
- `test_regression_original_bug_scenario()` - Specifically tests the original bug scenario
- `test_merchant_trade_no_character_safety()` - Validates character sanitization

## Key Test Scenarios

### 1. MerchantTradeNo Generation
- ✅ Length compliance (≤ 20 characters)
- ✅ Character safety (alphanumeric only)
- ✅ Uniqueness over time
- ✅ Various user ID formats
- ✅ Edge cases (empty, long, special chars)

### 2. Field Validation
- ✅ All required ECPay fields present
- ✅ Correct field values and formats
- ✅ CheckMacValue generation and verification
- ✅ Date format compliance
- ✅ Amount conversion accuracy

### 3. API Integration
- ✅ Successful authorization callbacks
- ✅ Failed authorization handling
- ✅ Payment webhook processing
- ✅ Security verification
- ✅ Error response handling

### 4. End-to-End Flow
- ✅ Health check endpoints
- ✅ Authentication requirements
- ✅ Database table creation
- ✅ ECPay API connectivity
- ✅ Complete authorization workflow

## Test Results Summary

When all tests pass, you'll see:
```
🎉 ALL TESTS PASSED!
✅ ECPay integration is protected against regression bugs.
✅ MerchantTradeNo length validation is working correctly.
✅ All required fields are properly validated.
```

## Integration with CI/CD

Add to your CI pipeline:
```yaml
# .github/workflows/test.yml
- name: Run ECPay Integration Tests
  run: python tests/run_ecpay_tests.py --coverage
  
- name: Check ECPay Test Coverage
  run: |
    if [ -f htmlcov/index.html ]; then
      echo "✅ ECPay tests completed with coverage report"
    fi
```

## Error Scenarios Tested

1. **MerchantTradeNo Too Long**: Prevents ECPay API error 10200052
2. **Missing Required Fields**: Prevents incomplete API requests
3. **Invalid CheckMacValue**: Prevents security verification failures
4. **Character Encoding Issues**: Prevents problematic characters in IDs
5. **Database Migration Issues**: Ensures all tables exist
6. **Authentication Failures**: Proper error handling for unauthorized access

## Maintenance

- Run tests after any ECPay service changes
- Update tests when adding new ECPay features
- Review test coverage reports regularly
- Add new test cases for discovered edge cases

## Troubleshooting

### Tests Fail with Database Errors
```bash
# Check if backend is running
python tests/integration/test_ecpay_flow.py

# Verify database migrations
alembic upgrade head
```

### Tests Fail with Import Errors
```bash
# Ensure you're in project root
ls src/coaching_assistant/  # Should exist

# Run from project root
python tests/run_ecpay_tests.py
```

### ECPay API Connectivity Issues
Tests include network connectivity checks and will skip gracefully if ECPay sandbox is unreachable.