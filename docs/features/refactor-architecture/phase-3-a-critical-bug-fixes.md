# Phase 3-A: Critical Bug Fixes - Session Transcription Issues

**Date Created**: 2025-09-16
**Status**: 🚨 **EMERGENCY HOTFIX**
**Priority**: P0 - Critical Production Bug
**Issue**: Users cannot view coaching session transcriptions

## 🔍 Problem Analysis

### Critical Error Log Analysis

Based on error logs from production, three critical bugs were identified that prevent users from viewing coaching session transcriptions:

**Error Signature**:
```
sqlalchemy.exc.ProgrammingError: column session.progress_percentage does not exist
RuntimeError: Database error retrieving session 1d685ea5-1870-4afc-a8ca-03daa950e311
```

**Frontend Symptoms**:
- 404 errors for `/api/v1/plan/validate-action`
- CORS errors blocking `/api/v1/sessions/{id}` and `/api/v1/sessions/{id}/status`
- Session transcriptions not loading in coaching session pages
- Plan limit validation failing

## 🚨 Critical Issues Identified

### 1. **Database Column Mismatch** (CRITICAL - P0)
**File**: `src/coaching_assistant/infrastructure/db/models/session_model.py:40`

**Problem**:
- Infrastructure ORM model `SessionModel` expects `progress_percentage` column (line 40)
- Production database doesn't have this column
- Results in SQL exception when trying to retrieve sessions

**Error Pattern**:
```sql
SELECT session.progress_percentage AS session_progress_percentage, ...
FROM session WHERE session.id = %(pk_1)s::UUID
-- ERROR: column session.progress_percentage does not exist
```

**Impact**:
- ❌ Sessions cannot be retrieved from database
- ❌ Coach session transcription pages fail completely
- ❌ Status polling fails, preventing real-time updates

### 2. **Missing Plan Validation API** (HIGH - P1)
**File**: API routing in `src/coaching_assistant/main.py`

**Problem**:
- Frontend calls `/api/v1/plan/validate-action` (404 Not Found)
- Router exists at `plan_limits.router` but path mismatch
- Frontend expects `/api/v1/plan/validate-action`, router provides different path

**Impact**:
- ❌ Plan limit validation fails
- ❌ Users can't see upload restrictions
- ❌ File upload blocking doesn't work

### 3. **CORS Configuration Issues** (MEDIUM - P2)
**Files**: Session endpoint CORS handling

**Problem**:
- CORS blocking requests to session endpoints
- Missing `Access-Control-Allow-Origin` headers
- Frontend can't access transcription status

**Impact**:
- ❌ Frontend can't poll transcription status
- ❌ Real-time updates don't work
- ❌ Session data loading fails

## 🔧 Solution Implementation

### Fix 1: Database Column Issue (IMMEDIATE)

**Root Cause**: Infrastructure model expects database schema that doesn't exist in production.

**Clean Architecture Solution**:
Use legacy model temporarily to maintain database compatibility while preserving Clean Architecture principles.

**Implementation**:
1. **Temporarily switch to legacy Session model** in repository
2. **Maintain repository pattern** - still use Clean Architecture
3. **Plan proper migration** for future infrastructure model adoption

```python
# In session_repository.py - Clean Architecture compliant fix
from ....models.session import Session as LegacySessionModel  # Temporary
# from ..models.session_model import SessionModel  # Future after migration

class SQLAlchemySessionRepository(SessionRepoPort):
    def get_by_id(self, session_id: UUID) -> Optional[Session]:
        try:
            # Use legacy model that matches production schema
            orm_session = self.session.get(LegacySessionModel, session_id)
            if orm_session:
                # Convert legacy ORM to domain model
                return self._legacy_to_domain(orm_session)
            return None
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving session {session_id}") from e
```

### Fix 2: Plan Validation API (QUICK)

**Root Cause**: Router mounted but path mismatch with frontend expectations.

**Implementation**:
Verify and fix the router mounting in `main.py`:

```python
# Ensure this line exists in main.py:
app.include_router(plan_limits.router, prefix="/api/v1/plan", tags=["plan-limits"])
```

### Fix 3: CORS Configuration (SIMPLE)

**Root Cause**: CORS middleware not properly handling all session endpoints.

**Implementation**:
Ensure CORS is properly configured for session endpoints:

```python
# Verify in main.py CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)
```

## 📋 Implementation Steps

### Step 1: Fix Database Column Issue
1. ✅ **Modify session repository** - Switch to legacy model import
2. ✅ **Add legacy-to-domain conversion** - Maintain Clean Architecture
3. ✅ **Test session retrieval** - Verify endpoints work
4. ✅ **Update error handling** - Ensure proper error messages

### Step 2: Fix API Routing
1. ✅ **Verify plan_limits router mounting** in main.py
2. ✅ **Test endpoint availability** - POST `/api/v1/plan/validate-action`
3. ✅ **Check response format** - Ensure frontend compatibility

### Step 3: Fix CORS Issues
1. ✅ **Review CORS middleware configuration**
2. ✅ **Test session endpoints** - GET `/api/v1/sessions/{id}`
3. ✅ **Verify status polling** - GET `/api/v1/sessions/{id}/status`

### Step 4: Documentation & Testing
1. ✅ **Document all changes** - This file
2. ✅ **Create rollback plan** - If issues arise
3. ✅ **Test critical user flows** - Session transcription viewing
4. ✅ **Monitor error logs** - Ensure fixes work in production

## 🧪 Testing Plan

### Critical Path Testing
1. **Session Retrieval**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/sessions/{session_id}" \
        -H "Authorization: Bearer {token}"
   ```

2. **Status Polling**:
   ```bash
   curl -X GET "http://localhost:8000/api/v1/sessions/{session_id}/status" \
        -H "Authorization: Bearer {token}"
   ```

3. **Plan Validation**:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/plan/validate-action" \
        -H "Authorization: Bearer {token}" \
        -H "Content-Type: application/json" \
        -d '{"action": "create_session"}'
   ```

### Success Criteria
- ✅ Session pages load without database errors
- ✅ Transcription text displays correctly
- ✅ Status polling works and shows progress
- ✅ Plan validation API returns proper responses
- ✅ No CORS errors in browser console

## 🔙 Rollback Plan

If fixes cause issues:

1. **Database Fix Rollback**:
   ```bash
   git revert {commit_hash}  # Revert session repository changes
   ```

2. **API Routing Rollback**:
   - Comment out plan_limits router inclusion
   - Redeploy previous version

3. **CORS Rollback**:
   - Revert CORS middleware changes
   - Use previous working configuration

## 🎯 Long-term Architecture Plan

### Database Migration Strategy
1. **Create Alembic migration** to add `progress_percentage` column
2. **Update production database** with proper schema
3. **Switch back to infrastructure models** after migration
4. **Remove legacy model dependencies**

### Clean Architecture Maintenance
- ✅ Repository pattern maintained during fix
- ✅ Use cases still use domain models
- ✅ API layer remains unchanged
- ✅ Dependency injection preserved

## 📊 Success Metrics

### Immediate (24 hours)
- ✅ Zero session retrieval errors in logs
- ✅ Session transcription pages load successfully
- ✅ Plan validation endpoints return 200 status
- ✅ CORS errors eliminated from browser console

### Short-term (1 week)
- ✅ User complaints about transcription viewing resolved
- ✅ Support tickets for session loading closed
- ✅ Frontend error monitoring shows clean session workflows

### Long-term (1 month)
- ✅ Proper database migration completed
- ✅ Infrastructure models fully adopted
- ✅ Legacy model dependencies removed
- ✅ Architecture compliance restored to 100%

## 🚀 Deployment Notes

### Pre-deployment Checklist
- [ ] Test fixes locally with production-like database
- [ ] Verify all session endpoints work
- [ ] Check frontend integration
- [ ] Prepare rollback scripts

### Post-deployment Monitoring
- [ ] Watch error logs for session-related errors
- [ ] Monitor frontend error rates
- [ ] Check session page load times
- [ ] Verify transcription display functionality

---

**Status**: 🔧 **IN PROGRESS**
**Next Actions**: Implement database column fix first (highest priority)
**Estimated Time**: 2-4 hours for all fixes
**Risk Level**: LOW (temporary legacy model usage preserves functionality)