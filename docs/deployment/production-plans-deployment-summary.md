# Production Plans Deployment Summary

**Date**: 2025-10-04
**Issue**: Empty plans on billing page
**Status**: In Progress - Ready for Database Seeding

## What We Fixed ✅

### 1. Pydantic Validation Bug (Resolved)

**Problem**: `/api/v1/subscriptions/current` returning 500 errors

**Root Cause**: Pydantic v2 schema validation
```python
# ❌ Before (Pydantic v1 syntax)
subscription: Dict[str, Any] = None

# ✅ After (Pydantic v2 syntax)
subscription: Optional[Dict[str, Any]] = None
```

**Fix Applied**:
- Updated schema in `src/coaching_assistant/api/v1/subscriptions.py`
- Added integration tests: `tests/integration/api/test_subscription_endpoints_pydantic.py`
- Added schema unit tests: `tests/unit/api/test_subscription_schemas.py`
- Updated testing docs: `docs/claude/testing.md` (new "Testing Gaps" section)
- **Commit**: `cbad2b0` on branch `fix/production-subscription-pydantic-validation`

**Result**: ✅ No more Pydantic ValidationError in production logs

### 2. API Proxy Understanding (Clarified)

**Question**: Why `/api/proxy/v1/plans` instead of `/api/v1/plans`?

**Answer**: Next.js Reverse Proxy Pattern
- **Frontend**: `https://coachly.doxa.com.tw` (Cloudflare Pages)
- **Backend**: `https://api.doxa.com.tw` (Render.com)
- **Proxy**: Avoids CORS issues between different domains

**Configuration** (`next.config.js:62-64`):
```javascript
{
  source: '/api/proxy/v1/:path*',
  destination: `${backendApiUrl}/api/v1/:path*`
}
```

**Flow**:
```
Frontend calls → /api/proxy/v1/plans
     ↓
Next.js rewrites → https://api.doxa.com.tw/api/v1/plans
     ↓
Backend handles → /api/v1/plans
     ↓
Response via proxy → Frontend (same-origin, no CORS!)
```

## What's Pending 🔄

### Root Cause: Empty Database

**Confirmed**: Production `plan_configurations` table is **EMPTY**

**Evidence**:
- Logs show: "Retrieved 0 plans for user..."
- API returns: `{ plans: [], total: 0 }`
- Frontend displays: No plan cards

**Production Database**:
- **Service ID**: `dpg-d27igr7diees73cla8og-a`
- **Name**: `Coachly-db-production`
- **Database**: `coachly`
- **Region**: Singapore

### Solution: Database Seeding

**Files Created**:

1. **Deployment Script**: `scripts/deployment/seed_production_plans.sh`
   - Automated seeding with safety checks
   - Backup existing data before seeding
   - Verification steps included
   - Usage: `./scripts/deployment/seed_production_plans.sh`

2. **MCP Setup Guide**: `docs/deployment/render-mcp-setup.md`
   - Instructions for Render MCP installation
   - Database query examples
   - Troubleshooting guide

3. **Deployment Summary**: This document

**Seed Data** (from `seed_plan_configurations_v2.py`):
- FREE: 免費試用方案 (200 min/month)
- STUDENT: 學習方案 (500 min/month)
- PRO: 專業方案 (1000 min/month)
- COACHING_SCHOOL: 認證學校方案 (unlimited)

## Next Steps 📋

### Step 1: Install Render MCP (You're doing this now)

```bash
claude mcp add render-mcp
```

### Step 2: Verify Database State via MCP

```sql
-- Check current state
SELECT COUNT(*) FROM plan_configurations;
-- Expected: 0

-- Verify table structure
\d plan_configurations
```

### Step 3: Run Seed Script

**Option A: Using deployment script** (Recommended):
```bash
# Get DATABASE_URL from Render dashboard
export DATABASE_URL="postgresql://coachly_user:password@dpg-xxx.singapore.render.com/coachly"

# Run deployment script with safety checks
chmod +x scripts/deployment/seed_production_plans.sh
./scripts/deployment/seed_production_plans.sh
```

**Option B: Direct seed script**:
```bash
export DATABASE_URL="postgresql://..."
python scripts/database/seed_plan_configurations_v2.py
```

### Step 4: Verify Success

```bash
# Check API endpoint
curl -s "https://coachly.doxa.com.tw/api/proxy/v1/plans" \
  -H "Authorization: Bearer <your-token>" | jq '.total'
# Expected: 4

# Check production logs
render logs srv-d2sndkh5pdvs739lqq0g --limit 50 --text "Retrieved"
# Expected: "Retrieved 4 plans for user..."

# Open frontend
open https://coachly.doxa.com.tw/dashboard/billing
# Expected: 4 plan cards visible
```

### Step 5: Update Issue Status

Once verified:
- Update `docs/issues/production-no-plan.md` status to "Resolved"
- Mark all checklist items as complete
- Document lessons learned

## Production Services Reference

### API Server
- **ID**: `srv-d2sndkh5pdvs739lqq0g`
- **Name**: `Coachly-api-production`
- **URL**: https://api.doxa.com.tw

### Database
- **ID**: `dpg-d27igr7diees73cla8og-a`
- **Name**: `Coachly-db-production`
- **Database**: `coachly`
- **User**: `coachly_user`

### Frontend
- **URL**: https://coachly.doxa.com.tw
- **Billing Page**: https://coachly.doxa.com.tw/dashboard/billing

## Resolution Checklist

- [x] Pydantic schema bug fixed
- [x] Integration tests added
- [x] Testing documentation updated
- [x] Deployment script created
- [x] MCP setup guide created
- [x] Root cause identified (empty database)
- [ ] **Render MCP installed** ← You're here
- [ ] Database state verified
- [ ] Seed script executed successfully
- [ ] 4 plans visible in database
- [ ] API returns 4 plans
- [ ] Frontend displays plans correctly
- [ ] Production logs show "Retrieved 4 plans"
- [ ] Users can select and subscribe to plans

## Files Modified/Created

### Code Changes
- ✅ `src/coaching_assistant/api/v1/subscriptions.py` - Fixed Pydantic schema
- ✅ `tests/integration/api/test_subscription_endpoints_pydantic.py` - New integration tests
- ✅ `tests/unit/api/test_subscription_schemas.py` - New schema tests
- ✅ `docs/claude/testing.md` - Added "Testing Gaps" section

### Deployment Files
- ✅ `scripts/deployment/seed_production_plans.sh` - Automated deployment script
- ✅ `docs/deployment/render-mcp-setup.md` - MCP setup guide
- ✅ `docs/deployment/production-plans-deployment-summary.md` - This summary
- ✅ `docs/issues/production-no-plan.md` - Updated with current status

### Documentation
- ✅ `docs/claude/subagent/production-monitor.md` - Render CLI monitoring guide

## Lessons Learned

1. **Testing Gap**: Mocked tests bypassed Pydantic validation
   - **Fix**: Added integration tests for response validation
   - **Prevention**: Require integration tests for all Pydantic schemas

2. **Production Database**: Plans not seeded during initial deployment
   - **Fix**: Created automated seeding scripts with safety checks
   - **Prevention**: Add database seeding to deployment checklist

3. **API Proxy Pattern**: Next.js proxy solved CORS issues elegantly
   - **Understanding**: Document architectural patterns clearly
   - **Benefit**: Easy to switch backends via environment variables

## Support Resources

- **Issue Tracking**: `@docs/issues/production-no-plan.md`
- **Deployment Guide**: `@docs/deployment/render-mcp-setup.md`
- **Monitoring Guide**: `@docs/claude/subagent/production-monitor.md`
- **Testing Guide**: `@docs/claude/testing.md`

---

**Current Status**: Waiting for Render MCP installation to verify and seed production database.
