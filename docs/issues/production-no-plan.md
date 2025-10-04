# Production Issue: No Plan Visible & Subscription Endpoint Error

**Status**: 🔴 Critical
**Created**: 2025-10-04
**Environment**: Production (Render.com)
**Affected Users**: All users

## Problem Summary

Two related issues in production:

1. Plans are not visible to users in the UI
2. `/api/v1/subscriptions/current` endpoint returning 500 errors

## Error Details

### Frontend Errors (Browser Console)

```text
Failed to load subscription status: Error: GET /v1/subscriptions/current failed
    at n.get (358-40f0ddce91d0661f.js:1:3342)
    at async u (page-89a09e8ecb82707c.js:1:38069)

Failed to load resource: the server responded with a status of 500 ()
/api/proxy/v1/subscriptions/current:1

GET /v1/subscriptions/current error: Error: GET /v1/subscriptions/current failed

Failed to get current subscription: Error: GET /v1/subscriptions/current failed
```

### Backend Errors (Render.com API Server Logs)

```text
[2025-10-04 06:37:51,807: ERROR/MainProcess] Failed to get current subscription: 2 validation errors for CurrentSubscriptionResponse
subscription
  Input should be a valid dictionary [type=dict_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.11/v/dict_type
payment_method
  Input should be a valid dictionary [type=dict_type, input_value=None, input_type=NoneType]
    For further information visit https://errors.pydantic.dev/2.11/v/dict_type

INFO: 10.210.182.220:58174 - "GET /api/v1/subscriptions/current HTTP/1.1" 500 Internal Server Error
```

### Additional Context

```text
[2025-10-04 06:37:53,297: INFO/MainProcess] Retrieved 0 plans for user 11b42904-8a9e-472d-9452-cf4dbfeae6cd
INFO: 10.210.139.102:60936 - "GET /api/v1/plans HTTP/1.1" 200 OK
```

## Root Cause Analysis

### Primary Issue: Pydantic Validation Failure

The `CurrentSubscriptionResponse` schema expects `subscription` and `payment_method` to be dictionaries, but is receiving `None` values.

**Schema Location**: Likely in `src/coaching_assistant/api/schemas/subscription.py`

**Possible Causes**:

1. User has no active subscription in database
2. Service layer returning `None` instead of proper empty/default objects
3. Schema not handling nullable fields correctly
4. Missing data migration or seed data in production

### Secondary Issue: No Plans Retrieved

```text
Retrieved 0 plans for user 11b42904-8a9e-472d-9452-cf4dbfeae6cd
```

This suggests:

1. Plans table is empty in production database
2. Data migration not run on production
3. Seed data not loaded

## Impact

- **User Experience**: Users cannot see available plans or subscription status
- **Feature Availability**: Subscription-related features completely broken
- **Severity**: High - affects core functionality

## Investigation Steps

1. **Check Production Database**:
   - Verify `plans` table has data
   - Check `subscriptions` table for user records
   - Verify `payment_methods` table structure

2. **Review Schema Definition**:
   - Check `CurrentSubscriptionResponse` in API schemas
   - Verify if fields should be `Optional[dict]` or have defaults
   - Look at serialization logic in service/use case layer

3. **Check Data Migrations**:
   - Verify all Alembic migrations ran successfully
   - Check if seed data script was executed
   - Compare local vs production database schema

4. **Review Service Layer**:
   - Check `get_current_subscription` use case
   - Verify how it handles users without subscriptions
   - Look for improper `None` returns

## Temporary Workaround

**Option A**: Make fields optional in response schema

```python
class CurrentSubscriptionResponse(BaseModel):
    subscription: Optional[dict] = None
    payment_method: Optional[dict] = None
```

**Option B**: Return empty objects instead of None

```python
# In service layer
return {
    "subscription": {},
    "payment_method": {}
}
```

## Permanent Fix Requirements

1. **Database Seeding**:
   - Run plan seeding script in production
   - Verify subscription and payment method tables

2. **Schema Fixes**:
   - Update `CurrentSubscriptionResponse` to handle null cases
   - Add proper default values
   - Update frontend to handle empty subscription state

3. **Error Handling**:
   - Add graceful fallback when no subscription exists
   - Improve error messages
   - Add proper 404 vs 500 status codes

## Related Files

- `src/coaching_assistant/api/schemas/subscription.py` - Response schema
- `src/coaching_assistant/api/controllers/subscription.py` - API endpoint
- `src/coaching_assistant/core/services/subscription_*.py` - Business logic
- `apps/web/src/lib/api.ts` - Frontend API client
- `apps/web/src/hooks/*.tsx` - Subscription hooks

## Next Actions

- [ ] Check production database for plans and subscriptions data
- [ ] Review `CurrentSubscriptionResponse` schema definition
- [ ] Identify where `None` values originate
- [ ] Fix schema to handle null/empty subscription state
- [ ] Run database migrations/seeds if missing
- [ ] Add integration tests for "no subscription" scenario
- [ ] Deploy fix and verify in production

## Deployment Checklist

Before marking as resolved:

- [ ] Database contains plan data
- [ ] Subscription endpoint returns 200 with valid data or proper empty state
- [ ] Frontend displays plans correctly
- [ ] No 500 errors in production logs
- [ ] User can view and select plans
