# Payment Testing Guide

This document describes the testing tools and scripts available for the ECPay payment integration.

## Test Files Location

### Integration Tests
- **Location**: `/tests/integration/test_ecpay_basic.py`
- **Purpose**: Basic ECPay connectivity and CheckMacValue validation
- **Type**: Integration test for payment system

## Test Scripts Overview

### test_ecpay_basic.py

**Purpose**: Comprehensive ECPay integration testing and diagnosis tool

**Key Features**:
- ECPay connectivity testing to staging environment
- CheckMacValue calculation verification
- Simple test order creation with minimal parameters
- Error analysis and troubleshooting guidance
- Solution recommendations for common issues

**Test Data**:
```python
MERCHANT_ID = "3002607"          # ECPay test merchant
HASH_KEY = "pwFHCqoQZGmho4w6"    # Test hash key
HASH_IV = "EkRm7iFT261dpevs"     # Test hash IV
```

**Functions**:
- `create_simple_test_order()` - Creates minimal test order with 100 TWD
- `generate_check_mac_value()` - Standard CheckMacValue calculation
- `test_ecpay_connectivity()` - Tests connection to ECPay staging
- `analyze_error_possibilities()` - Analyzes potential error causes
- `recommended_solutions()` - Provides troubleshooting steps

## Usage Instructions

### Running ECPay Basic Test

```bash
cd tests/integration
python test_ecpay_basic.py
```

**Expected Output**:
- Connectivity test results to ECPay staging environment
- Generated test order parameters with proper CheckMacValue
- Error analysis and recommendations if issues occur
- Manual testing instructions for ECPay staging portal

### Troubleshooting Common Issues

The script provides automated analysis for:

1. **CheckMacValue Errors** (Most common)
   - Test merchant store status verification
   - Hash Key/IV validation
   - Parameter encoding verification

2. **Connection Issues**
   - Network connectivity to ECPay staging
   - URL and endpoint validation

3. **Transaction Limitations**
   - Amount restrictions for test merchant
   - Payment method availability

## Integration with Main System

### Environment Requirements

```env
# Required for payment testing
ECPAY_MERCHANT_ID=3002607
ECPAY_HASH_KEY=pwFHCqoQZGmho4w6
ECPAY_HASH_IV=EkRm7iFT261dpevs
ECPAY_STAGING_URL=https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
```

### Test Coverage

- ✅ Basic connectivity to ECPay staging
- ✅ CheckMacValue calculation accuracy
- ✅ Minimal order parameter generation
- ✅ Error diagnosis and troubleshooting
- ❌ End-to-end payment flow (requires manual testing)
- ❌ Webhook callback verification (requires running server)

## Known Issues & Solutions

### Issue: CheckMacValue Validation Fails

**Symptoms**: ECPay returns "CheckMacValue驗證失敗"

**Most Likely Causes**:
1. Test merchant store 3002607 not activated
2. Hash Key/IV credentials outdated
3. Parameter encoding differences

**Solutions**:
1. Contact ECPay support to verify test merchant status
2. Confirm latest test credentials from ECPay documentation
3. Use smaller test amounts (100 TWD instead of 8999 TWD)

### Issue: Network Connection Fails

**Symptoms**: Connection timeout or network errors

**Solutions**:
1. Verify internet connectivity
2. Check if ECPay staging is accessible
3. Consider firewall restrictions

## Future Enhancements

### Planned Test Additions
- [ ] Webhook callback simulation
- [ ] Production environment connectivity test
- [ ] Payment flow state machine testing
- [ ] Subscription billing scenario tests

### Integration with CI/CD
- [ ] Add to automated test suite
- [ ] Mock ECPay responses for unit testing
- [ ] Environment-specific test configuration

## References

- **ECPay Documentation**: Official API documentation and test credentials
- **Payment Feature Guide**: `@docs/features/payment/ecpay-integration-guide.md`
- **Troubleshooting Guide**: `@docs/features/payment/ecpay-troubleshooting-guide.md`
- **Main Payment Implementation**: `@src/coaching_assistant/api/billing.py`