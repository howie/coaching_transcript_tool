# API Testing & Verification Standards

## 🚫 CRITICAL RULE: Never Claim API Fixes Without Real Verification

### 🔥 MANDATORY AUTHENTICATION TESTING (User Requirement)
- **NEVER ACCEPTABLE**: Claiming API fixes based only on 401 authentication responses
- **ALWAYS REQUIRED**: Use real JWT tokens with proper authentication for ALL testing
- **User Quote**: "任何 API 測試，回覆 Now we're getting 401 (authentication required) 都是不能接受的，要測試就必須取得 token 測試!!!"

**FORBIDDEN Claims:**
- ❌ "The API now returns 401 instead of 500, so the fix works"
- ❌ "Both endpoints correctly respond with authentication required"
- ❌ "The enum bug is fixed" (based only on status code changes)
- ❌ "Now we're getting 401 (authentication required)" (without real token testing)

**REQUIRED Verification for API Fix Claims:**

#### 1. **Authenticate with Real Tokens** (MANDATORY)
```bash
# MUST create and use real JWT tokens for testing
# NEVER test without proper authentication
# Example with real token:
curl -H "Authorization: Bearer <actual_jwt_token>" http://localhost:8000/api/v1/sessions/{session_id}

# Required token format:
{
  "sub": "user_id",
  "exp": timestamp,
  "type": "access",
  "email": "user@example.com"
}
```

#### 2. **Verify Real Data Responses**
```bash
# Must show actual JSON response data, not just status codes
# Example acceptable evidence:
{
  "currentPlan": {
    "display_name": "學習方案",
    "id": "STUDENT"
  },
  "usageStatus": {
    "plan": "student",
    "planLimits": {...}
  }
}
```

#### 3. **Test Multiple User Types**
- Test with users having different plans (FREE, STUDENT, PRO)
- Verify each plan type returns correct data
- Document which users were tested and their plan types

#### 4. **Evidence-Based Claims Only**
```markdown
✅ ACCEPTABLE: "Tested with user howie.yu@gmail.com (STUDENT plan) - API returns complete plan data with display_name '學習方案'"

❌ UNACCEPTABLE: "Both endpoints now correctly return 401 instead of 500 errors"
```

#### 5. **Use Test Automation When Possible**
```python
# Create temporary auth tokens in test scripts
# Verify complete request/response cycles
# Test actual business logic, not just HTTP status
```

### Testing Token Management

**For API Testing:**
- Create temporary test tokens with limited scope
- Use test user accounts with known plan types
- Document which authentication method was used
- Clean up test tokens after verification

**Authentication Testing Levels:**
1. **Unauthenticated**: Should return 401
2. **Authenticated but wrong plan**: Should return appropriate data/limits
3. **Authenticated with test plan**: Should return real plan configuration data

### Mandatory Documentation for API Claims

When claiming an API fix works, provide:
```markdown
## API Fix Verification

**Endpoint Tested**: `/api/v1/plans/current`
**User Tested**: test.user@example.com (STUDENT plan)
**Authentication**: JWT token (expires: 2025-01-17T10:00:00Z)
**Response Status**: 200 OK
**Response Data**:
{
  "currentPlan": {...actual data...},
  "usageStatus": {...actual limits...}
}

**Before Fix**: 500 Internal Server Error "UserPlan.STUDENT not in enum"
**After Fix**: 200 OK with complete plan data
```

This ensures all API fix claims are backed by real evidence, not assumptions.

## Third-Party API Integration Guidelines

### Parameter Format Consistency

**Critical Rule**: Signature-based APIs (e.g., payment gateways) depend on exact string representation.

```python
# ✅ Force string types to ensure consistency
auth_data = {
    "TotalAmount": str(amount),        # Explicit string conversion
    "ExecTimes": str(exec_times),      # Prevents type conversion issues
    "PeriodAmount": str(period_amt),   # Frontend/backend consistency
    "MerchantID": str(merchant_id),    # Avoid integer/string mismatches
}
```

**Why This Matters**:
- JavaScript `String(123)` vs Python `123` produces different signatures
- Payment APIs reject requests with incorrect CheckMacValue/signatures
- Frontend form submission may convert types during transmission

### Next.js API Route Design for Third-Party Callbacks

**Problem**: Next.js page components cannot handle POST requests from third-party services.

**Solution**: Use API routes for callbacks, then redirect to pages for UI.

```typescript
// ✅ API Route handles POST callback
// /app/api/payment/callback/route.ts
export async function POST(request: NextRequest) {
  const formData = await request.formData()

  // Process callback data
  const status = formData.get('RtnCode')
  const tradeNo = formData.get('TradeNo')

  // Store results in database/session
  await processPaymentResult(status, tradeNo)

  // Redirect to page for UI display
  const params = new URLSearchParams({
    status: status as string,
    tradeNo: tradeNo as string
  })

  return NextResponse.redirect(
    new URL(`/payment/result?${params}`, request.url)
  )
}

// ❌ Page Component - Cannot handle POST
// /app/payment/result/page.tsx
// This only works for GET requests, will fail for POST
```

**Architecture Principles**:
- **API Routes**: Handle third-party POST callbacks
- **Page Components**: Display UI based on query parameters (GET)
- **Clear Separation**: Avoid mixing request handling types

### API Integration Testing Strategy

**Layered Testing Approach**:

1. **Backend Logic Testing**
   ```python
   def test_parameter_generation():
       """Test that backend generates correct parameters."""
       service = PaymentService()
       params = service.generate_payment_params(amount=1000)

       assert params['TotalAmount'] == '1000'  # String type
       assert 'CheckMacValue' in params
       assert len(params['MerchantTradeNo']) <= 20  # Length limit
   ```

2. **Frontend Integration Testing**
   ```typescript
   test('form submission preserves parameter types', () => {
       const params = { TotalAmount: '1000', ExecTimes: '12' }
       const form = createPaymentForm(params)

       // Verify no type conversion occurs
       expect(form.get('TotalAmount')).toBe('1000')
       expect(typeof form.get('TotalAmount')).toBe('string')
   })
   ```

3. **Real API Testing (Sandbox)**
   ```python
   @pytest.mark.integration
   def test_payment_api_real_call():
       """Test with real API in sandbox environment."""
       service = PaymentService(environment='sandbox')
       result = service.create_payment(amount=1000)

       # Should succeed with sandbox credentials
       assert result.status_code == 200
       assert 'TradeNo' in result.response
   ```

4. **End-to-End Testing**
   ```python
   @pytest.mark.e2e
   async def test_complete_payment_flow(test_client, browser):
       # 1. Backend generates form
       response = await test_client.post('/api/payment/init')
       form_url = response.json()['form_url']

       # 2. Simulate browser form submission
       result = await browser.submit_form(form_url)

       # 3. Verify callback received
       assert await test_client.get('/api/payment/status') == 'completed'
   ```

### Development Phase Checklist

**Before Integration**:
- [ ] Read API documentation thoroughly (check version differences)
- [ ] Identify signature/checksum requirements
- [ ] Note parameter format requirements (string vs number)
- [ ] Check character length limits
- [ ] Understand callback/webhook mechanisms

**During Development**:
- [ ] Standardize all parameters as strings for signature-based APIs
- [ ] Log complete request/response data
- [ ] Create API route for POST callbacks (Next.js)
- [ ] Implement proper error handling with user-friendly messages
- [ ] Add comprehensive parameter validation

**Testing Phase**:
- [ ] Unit test parameter generation and format
- [ ] Integration test with sandbox environment
- [ ] Test callback/webhook handling
- [ ] Verify signature/checksum calculation
- [ ] Test error scenarios (timeout, invalid params, etc.)

**Deployment Phase**:
- [ ] Set up monitoring for API responses
- [ ] Prepare fallback workflows for API failures
- [ ] Document integration details and gotchas
- [ ] Create runbook for troubleshooting common issues

### Common Pitfalls and Solutions

**Pitfall 1: Parameter Type Conversion**
```python
# ❌ Type may change during transmission
params = {'amount': 1000}  # Integer

# ✅ Force string to prevent conversion
params = {'amount': str(1000)}  # String
```

**Pitfall 2: Character Encoding Issues**
```python
# ❌ Special characters may break signatures
description = "訂閱方案-學生版 $299/月"

# ✅ URL encode or sanitize special characters
description = urllib.parse.quote("訂閱方案-學生版")
```

**Pitfall 3: Timezone Mismatches**
```python
# ❌ Assuming local timezone
timestamp = datetime.now().isoformat()

# ✅ Use explicit timezone
from datetime import timezone
timestamp = datetime.now(timezone.utc).isoformat()
```

**Pitfall 4: Inadequate Error Handling**
```python
# ❌ Generic error, user confused
try:
    result = payment_api.call()
except Exception:
    raise HTTPException(500, "Payment failed")

# ✅ Specific error with context
try:
    result = payment_api.call()
except PaymentAPIException as e:
    logger.error(f"Payment API error: {e.code} - {e.message}")
    raise HTTPException(400, detail={
        "error": "payment_failed",
        "message": "無法處理付款，請稍後再試",
        "support_code": e.code  # For customer support
    })
```

### Debugging Tips

**Enable Request Logging**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Log complete request before sending
logger.debug(f"API Request: {json.dumps(params, indent=2)}")
logger.debug(f"Signature: {signature}")

# Log complete response
logger.debug(f"API Response: {response.text}")
```

**Compare with Working Examples**:
```python
# Create a known-working example for comparison
known_good_params = {...}
known_good_signature = calculate_signature(known_good_params)

# Compare your parameters
your_params = generate_params()
your_signature = calculate_signature(your_params)

# Identify differences
diff = compare_params(known_good_params, your_params)
logger.info(f"Parameter differences: {diff}")
```

**Use API Sandbox Testing Tools**:
- Many payment APIs provide official testing/validation tools
- Test parameter format and signature calculation
- Verify before attempting real integration

## Key API Endpoints

```
Authentication:
POST /auth/google - Google SSO authentication

Sessions:
POST /sessions - Create transcription session
GET /sessions - List user sessions
GET /sessions/{id} - Get session details
POST /sessions/{id}/upload-url - Get signed upload URL
POST /sessions/{id}/start-transcription - Start processing
GET /sessions/{id}/transcript - Download transcript
PATCH /sessions/{id}/speaker-roles - Update speaker assignments

LeMUR Optimization:
POST /lemur-speaker-identification - Optimize speaker identification
POST /lemur-punctuation-optimization - Optimize punctuation
POST /session/{session_id}/lemur-speaker-identification - Database-based speaker optimization
POST /session/{session_id}/lemur-punctuation-optimization - Database-based punctuation optimization

Coaching Management:
GET /api/v1/clients - List clients
POST /api/v1/clients - Create client
GET /api/v1/coaching-sessions - List coaching sessions
POST /api/v1/coaching-sessions - Create session
```

## Plan Limitations & Features

The platform enforces different limits based on user subscription plans:

### File Size Limits
- **FREE Plan**: 60MB per file
- **PRO Plan**: 200MB per file
- **ENTERPRISE Plan**: 500MB per file

### Session & Transcription Limits
- **Database-driven**: All plan limits are stored in PostgreSQL and dynamically loaded
- **API Integration**: `/api/v1/plans/current` endpoint provides real-time limit information
- **Frontend Validation**: File upload component shows dynamic size limits based on user's plan
- **Backend Enforcement**: Plan validation occurs before processing to prevent overuse

### Dynamic Limit Display
The frontend automatically adapts to show the correct limits:
- AudioUploader component displays plan-specific file size limits
- Error messages include current plan context
- Billing pages show accurate feature comparisons per plan