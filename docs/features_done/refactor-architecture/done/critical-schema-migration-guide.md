# Critical Schema Migration Guide - Clean Architecture Phase 3 Fix

## ⚠️ CRITICAL ISSUE: Database Schema Mismatch

### Current Problem (2025-09-16)

The `/api/plans/current` endpoint is failing with 500 errors due to a schema mismatch between:
1. **Legacy Database Schema** (what's actually in production)
2. **Infrastructure Models** (what Phase 3 attempted to use)

### Root Cause Analysis

#### What Went Wrong
1. Phase 3 implementation updated `user_repository.py` to import the infrastructure `UserModel`
2. Infrastructure `UserModel` expects NEW schema fields
3. But the database still has the LEGACY schema
4. Result: SQLAlchemy queries fail with "Database connection error"

#### Schema Comparison

**Legacy User Table (Current Database)**
```sql
-- Located in: src/coaching_assistant/models/user.py
-- This is what's ACTUALLY in the database
Fields:
- google_id (String)
- transcription_count (Integer)
- current_month_start (DateTime)
- total_sessions_created (Integer)
- total_transcriptions_generated (Integer)
- total_minutes_processed (Integer)
- total_cost_usd (Decimal)
- preferences (JSON)
```

**Infrastructure User Model (Attempted to Use)**
```sql
-- Located in: src/coaching_assistant/infrastructure/db/models/user_model.py
-- This is what Phase 3 EXPECTED in the database
Fields:
- language_preference (String)
- timezone (String)
- email_notifications (String)
- marketing_emails (String)
- profile_completed (String)
- onboarding_completed (String)
- admin_notes (Text)
- is_test_user (String)
```

## 🔧 Immediate Fix Required

### Step 1: Revert User Repository (URGENT)

```python
# File: src/coaching_assistant/infrastructure/db/repositories/user_repository.py

# WRONG (causes 500 errors):
from ...db.models.user_model import UserModel  # ❌ Infrastructure model

# CORRECT (works with current database):
from ....models.user import User as UserModel  # ✅ Legacy model
```

### Step 2: Keep Domain Conversion Methods

The repository should still convert to/from domain models, but using the legacy ORM:

```python
def _to_domain(self, orm_user: UserModel) -> DomainUser:
    """Convert ORM User to domain User."""
    if not orm_user:
        return None
    # Use the legacy model's conversion method
    return orm_user.to_domain()  # Legacy model must have this method
```

## 📋 Proper Migration Path (Future)

### Phase 3A: Database Migration (Prerequisites)

1. **Create Alembic Migration**
   ```bash
   alembic revision --autogenerate -m "Migrate user table to new schema"
   ```

2. **Migration Script Must**:
   - Add new columns with defaults
   - Migrate data from old columns
   - Keep old columns temporarily (for rollback)

3. **Test Migration**:
   - Run on development database
   - Verify data integrity
   - Test rollback procedure

### Phase 3B: Model Transition

1. **Update Legacy Model Gradually**:
   ```python
   # Step 1: Add new fields to legacy model
   class User(BaseModel):
       # Existing fields
       google_id = Column(String(255), ...)

       # NEW fields (with defaults)
       language_preference = Column(String(20), default="zh-TW")
       timezone = Column(String(50), default="Asia/Taipei")
   ```

2. **Create Compatibility Layer**:
   ```python
   # Temporary: Support both old and new field names
   @property
   def transcription_count(self):
       """Backward compatibility"""
       return self.session_count  # Map to new field
   ```

### Phase 3C: Repository Cutover

Only after database migration is complete:

1. **Switch to Infrastructure Model**:
   ```python
   from ...db.models.user_model import UserModel  # Now safe to use
   ```

2. **Remove Legacy Model References**:
   - Delete `src/coaching_assistant/models/user.py`
   - Update all imports

3. **Clean Up Compatibility Layer**:
   - Remove property mappings
   - Remove deprecated fields

## 🚨 Critical Validation Checklist

Before attempting Phase 3 again:

- [ ] Database migration script created and tested
- [ ] All environments migrated (dev, staging, prod)
- [ ] Legacy model updated with new fields
- [ ] Compatibility layer tested
- [ ] Rollback plan documented
- [ ] All API endpoints tested after migration

## 🔍 How to Verify the Fix

### Test the Endpoint
```bash
# Should return 401 (auth required) not 500 (server error)
curl -X GET "http://localhost:8000/api/plans/current"
```

### Check SQL Queries
Look for these in logs:
- ✅ CORRECT: Queries with `google_id`, `transcription_count`
- ❌ WRONG: Queries with `language_preference`, `timezone`

### Monitor for Errors
```python
# Look for this error pattern:
"Database connection error while retrieving user"
# This indicates schema mismatch
```

## 📚 Lessons Learned

1. **Never change ORM models without database migration**
2. **Clean Architecture phases must include schema migrations**
3. **Test with actual database schema, not assumed schema**
4. **Keep legacy models until database is fully migrated**

## 🎯 Action Items

### Immediate (Fix Production)
1. Revert `user_repository.py` to use legacy model
2. Test all user-related endpoints
3. Deploy hotfix

### Short Term (Proper Migration)
1. Audit all model differences
2. Create comprehensive migration plan
3. Test migration in staging

### Long Term (Complete Clean Architecture)
1. Migrate all legacy models to infrastructure
2. Remove all legacy ORM dependencies from core
3. Document migration patterns for future use

## ⚠️ DO NOT ATTEMPT

Until database migration is complete, DO NOT:
- Switch repositories to infrastructure models
- Delete legacy model files
- Update ORM field names
- Remove backward compatibility

## 📝 References

- Legacy User Model: `src/coaching_assistant/models/user.py`
- Infrastructure User Model: `src/coaching_assistant/infrastructure/db/models/user_model.py`
- User Repository: `src/coaching_assistant/infrastructure/db/repositories/user_repository.py`
- Failed Endpoints: `/api/plans/current`, `/api/v1/subscriptions/current`

---

**Document Status**: CRITICAL - Required reading before any Phase 3 work
**Last Updated**: 2025-09-16
**Issue Tracking**: #clean-architecture-schema-mismatch