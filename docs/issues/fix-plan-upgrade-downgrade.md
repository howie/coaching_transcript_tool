# Fix: Subscription Plan Upgrade/Downgrade 500 Error

## Issue Description

**Problem**: Subscription upgrade/downgrade operations fail with HTTP 500 Internal Server Error

**Error in Browser Console**:
```
POST /api/v1/subscriptions/upgrade error: Error: Failed to upgrade subscription.
💥 升級流程錯誤: Error: Failed to upgrade subscription.
```

**Error in Backend Logs (initial)**:
```
ValueError: Invalid plan_id: PRO
```

**Error in Backend Logs (current)**:
```
AttributeError: 'PlanConfiguration' object has no attribute 'annual_price_twd_cents'
```

## Root Cause Analysis

The issue stems from a **case sensitivity mismatch** between frontend and backend plan ID handling:

- **Frontend** sends plan IDs in uppercase: `"PRO"`, `"ENTERPRISE"`, `"FREE"`
- **Backend** expects plan IDs in lowercase: `"pro"`, `"enterprise"`, `"free"`
- The `UserPlan` enum in `src/coaching_assistant/core/models/user.py` defines values in lowercase

### Affected Code Locations

1. **Frontend Service**: `apps/web/lib/services/subscription.service.ts:122-126`
   - Sends uppercase plan IDs from hardcoded frontend constants

2. **Backend Use Case**: `src/coaching_assistant/core/services/subscription_management_use_case.py:456-464`
   - Only handled exact enum matches, not case variations

3. **Plan Enum Definition**: `src/coaching_assistant/core/models/user.py:10-17`
   - Defines lowercase enum values

## Solution Implemented

### 1. Backend Plan ID Handling Enhancement

**File**: `src/coaching_assistant/core/services/subscription_management_use_case.py`

**Changes Made**:
- Updated `_modify_subscription()` method to handle case-insensitive plan IDs
- Updated `calculate_proration()` method with same logic
- Added triple-fallback strategy:
  1. Try exact enum match
  2. Try lowercase conversion
  3. Try explicit uppercase-to-enum mapping for legacy compatibility

```python
# Handle legacy uppercase plan IDs from frontend
if new_plan_id.upper() == "PRO":
    new_plan_type = UserPlan.PRO
elif new_plan_id.upper() == "ENTERPRISE":
    new_plan_type = UserPlan.ENTERPRISE
# ... etc for all plan types
```

### 2. Plan Configuration Validation Improvements

**Enhanced Validation Logic**:
- Better error messages for invalid pricing configurations
- Special handling for FREE plan (allows 0 amount)
- Improved validation for paid plans (must have non-zero pricing)
- Added logging for configuration inconsistencies

```python
# FREE plan should have 0 amount, which is valid
if new_plan_type == UserPlan.FREE:
    if new_amount_cents != 0:
        logger.warning(f"FREE plan has non-zero amount: {new_amount_cents}, setting to 0")
        new_amount_cents = 0
elif new_amount_cents == 0:
    raise ValueError(f"Paid plan {new_plan_id} cannot have zero pricing for {new_billing_cycle} billing cycle")
```

### 3. Backward Compatibility

**Ensured Compatibility**:
- Existing lowercase plan IDs continue to work
- New uppercase plan IDs from frontend are handled
- No changes required to frontend code
- No migration needed for existing subscriptions

## New Follow-up Issue (2025-09-27)

While the case-insensitive plan handling fix removed the original `Invalid plan_id` 500s, the `preview-change` and `upgrade` endpoints still return 500 because the backend now expects plan pricing on `PlanConfiguration.pricing` (nested dataclass) but our use cases still read legacy flat attributes (`annual_price_twd_cents`, `monthly_price_twd_cents`).

### Current Symptoms

- `POST /api/v1/subscriptions/preview-change` → 500 with `AttributeError: 'PlanConfiguration' object has no attribute 'annual_price_twd_cents'`
- `POST /api/v1/subscriptions/upgrade` → same AttributeError
- SQL logs show valid `plan_configurations` row loaded; failure happens when accessing pricing fields.

### Root Cause

- Domain object `PlanConfiguration` stores prices in nested `PlanPricing` (`plan_config.pricing.monthly_price_twd_cents`, etc.).
- Our subscription use case still references the flattened ORM field names from before the domain refactor.
- Unit tests mocked plan configs with flat attributes, hiding the bug.

### Recovery Plan

1. Introduce a helper in `SubscriptionManagementUseCase` to extract pricing from either the nested `PlanPricing` dataclass or legacy flat attributes (for mocks/backwards compatibility).
2. Update `create_subscription`, `_modify_subscription`, `calculate_proration`, and authorization flow to use the helper.
3. Adjust unit tests to mock `PlanConfiguration.pricing` structure (or leverage helper) so the regression is covered.
4. Add a focused test for `preview-change` to ensure the helper handles domain objects.
5. Re-run targeted pytest suite.
6. Ensure repository updates existing subscription rows instead of inserting duplicates when upgrading/downgrading.

### Fixes Implemented (2025-09-27 PM)

- Added `_extract_plan_amount_cents` helper and updated subscription use cases to consume nested pricing values.
- Updated unit tests with domain-shaped plan configuration mocks to cover the new pricing helper.
- Changed `SubscriptionRepository.save_subscription` to perform an update when the primary key already exists (uses SQLAlchemy `Session.get` + `update_from_domain`), preventing duplicate key violations during plan upgrades.

## Testing Strategy

### Manual Testing

1. **Test Upgrade Operations**:
   ```bash
   # Test with uppercase plan ID (as sent by frontend)
   curl -X POST http://localhost:8000/api/v1/subscriptions/upgrade \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <token>" \
     -d '{"plan_id": "PRO", "billing_cycle": "monthly"}'
   ```

2. **Test Downgrade Operations**:
   ```bash
   # Test downgrade from PRO to FREE
   curl -X POST http://localhost:8000/api/v1/subscriptions/downgrade \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <token>" \
     -d '{"plan_id": "FREE", "billing_cycle": "monthly"}'
   ```

3. **Test Proration Preview**:
   ```bash
   # Test proration calculation with uppercase plan ID
   curl -X POST http://localhost:8000/api/v1/subscriptions/preview-change \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <token>" \
     -d '{"plan_id": "ENTERPRISE", "billing_cycle": "annual"}'
   ```

### Expected Results

- ✅ All subscription operations accept both uppercase and lowercase plan IDs
- ✅ Upgrade from FREE to PRO works seamlessly
- ✅ Downgrade from PRO to FREE works correctly
- ✅ Proration calculations work with any case
- ✅ Clear error messages for invalid operations
- ✅ No breaking changes to existing functionality

## Impact Assessment

### Before Fix
- Subscription upgrades/downgrades failed with 500 errors
- Frontend users could not change their plans
- Revenue impact from blocked conversions

### After Fix
- Seamless plan changes in both directions
- Improved user experience
- Better error handling and logging
- Future-proof case handling

## Migration Notes

**No Migration Required**: This fix is backward compatible and requires no data migration or frontend changes.

**Deployment Steps**:
1. Deploy backend changes
2. Restart API server
3. Test subscription operations
4. Monitor logs for any issues

## Future Improvements

1. **Frontend Standardization**: Consider standardizing frontend to use lowercase plan IDs
2. **API Documentation**: Update API docs to specify case-insensitive plan ID handling
3. **Validation Enhancement**: Add OpenAPI schema validation for plan IDs
4. **Monitoring**: Add metrics for plan change operations

## Related Files

- `src/coaching_assistant/core/services/subscription_management_use_case.py` - Main fix
- `src/coaching_assistant/core/models/user.py` - Plan enum definition
- `apps/web/lib/services/subscription.service.ts` - Frontend service
- `src/coaching_assistant/api/v1/subscriptions.py` - API endpoints

## Date

Created: 2025-09-27
Fixed: 2025-09-27
