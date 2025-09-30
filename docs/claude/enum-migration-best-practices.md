# PostgreSQL Enum Migration Best Practices

This document outlines best practices for handling PostgreSQL enum migrations in Alembic, particularly when using SQLAlchemy with PostgreSQL's native ENUM types.

## The Problem: Enum Value Transactions

PostgreSQL has a strict requirement for enum type modifications:

> **New enum values must be committed before they can be used in UPDATE statements.**

This means you cannot add enum values and use them in data updates within the same transaction.

## Example of Problematic Migration

```python
def upgrade() -> None:
    # ❌ WRONG: This will fail in production
    op.execute("ALTER TYPE userplan ADD VALUE 'new_value'")
    op.execute("UPDATE user SET plan = 'new_value' WHERE condition")
```

**Error:** `unsafe use of new value "new_value" of enum type userplan`

## Solution: Two-Phase Migration Approach

### Phase 1: Add Enum Values Only

```python
def upgrade() -> None:
    """Add new enum values to userplan enum (Phase 1)."""

    # IMPORTANT: Check for existing values to handle reruns safely
    connection = op.get_bind()

    # Get existing enum values
    existing_values_result = connection.execute(
        sa.text("""
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
        """)
    )
    existing_values = {row[0] for row in existing_values_result}

    # Add new enum values only if they don't exist
    values_to_add = ['new_value1', 'new_value2']

    for value in values_to_add:
        if value not in existing_values:
            op.execute(f"ALTER TYPE userplan ADD VALUE '{value}'")

    # Note: Data migration must be done separately after enum values are committed
```

### Phase 2: Data Migration (Separate Migration or Emergency Script)

```python
def upgrade() -> None:
    """Migrate user data to new enum values (Phase 2)."""

    # Now we can safely use the new enum values
    op.execute("UPDATE user SET plan = 'new_value1' WHERE old_condition")
    op.execute("UPDATE user SET plan = 'new_value2' WHERE other_condition")
```

## Emergency Production Fix Pattern

For production issues, create an emergency script that:

1. **Adds missing enum values** (committed immediately)
2. **Migrates data** (in separate transaction)
3. **Updates migration state** (marks migration as complete)

### Example Emergency Script Structure

```python
def add_missing_enum_values(db, dry_run=True):
    """Add missing enum values with proper error handling."""

    # Check existing values
    existing_values = get_current_enum_values(db)
    required_values = ['value1', 'value2']
    missing_values = [v for v in required_values if v not in existing_values]

    if not missing_values:
        return True

    if not dry_run:
        for value in missing_values:
            try:
                db.execute(text(f"ALTER TYPE userplan ADD VALUE '{value}'"))
                db.commit()  # Commit each enum addition separately
            except Exception as e:
                db.rollback()
                return False

    return True

def migrate_user_data(db, dry_run=True):
    """Migrate user data in separate transaction."""

    if not dry_run:
        # Safe to use new enum values after commit
        db.execute(text("UPDATE user SET plan = 'new_value' WHERE plan = 'OLD_VALUE'"))
        db.commit()

    return True
```

## Best Practices Checklist

### ✅ DO

1. **Separate enum additions from data updates** into different migrations or transactions
2. **Check for existing enum values** before adding to handle reruns safely
3. **Commit enum changes immediately** before using them
4. **Use idempotent migrations** that can be run multiple times safely
5. **Create emergency scripts** for production fixes
6. **Test migrations locally** with realistic data
7. **Use proper error handling** and rollback mechanisms

### ❌ DON'T

1. **Don't add enum values and use them in the same transaction**
2. **Don't assume enum values don't exist** - always check first
3. **Don't ignore migration rollbacks** - handle downgrade scenarios
4. **Don't hardcode enum values** without checking current state
5. **Don't skip testing** enum migrations in development

## Enum Downgrade Considerations

PostgreSQL doesn't support removing enum values directly. Handle this by:

```python
def downgrade() -> None:
    """Handle enum downgrades safely."""

    # Option 1: Migrate data away from deprecated values
    op.execute("""
        UPDATE user
        SET plan = 'fallback_value'
        WHERE plan IN ('deprecated_value1', 'deprecated_value2')
    """)

    # Option 2: Keep enum values but mark as deprecated in application
    # (Recommended for data safety)

    # Note: Actual enum value removal requires recreating the entire enum type
```

## Database vs Code Enum Synchronization

### The Synchronization Problem

**Critical Issue**: Python enum values must exactly match database enum values, or runtime errors occur.

**Example Mismatch**:
```python
# Database schema (from migration)
CREATE TYPE speakerrole AS ENUM ('COACH', 'CLIENT', 'UNKNOWN');  -- Uppercase

# Python code (incorrect)
class SpeakerRole(enum.Enum):
    COACH = "coach"      # lowercase - MISMATCH!
    CLIENT = "client"    # lowercase - MISMATCH!
    UNKNOWN = "unknown"  # lowercase - MISMATCH!
```

**Result**: `LookupError: 'SpeakerRole.CLIENT' is not among the defined enum values`

### Prevention Strategy

#### Step 1: Verify Database Schema First

Always check what's actually in the database before writing Python enums:

```sql
-- Check existing enum values in database
SELECT enumlabel
FROM pg_enum
WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'speakerrole')
ORDER BY enumsortorder;

-- Check actual data values
SELECT DISTINCT role FROM session_role;
SELECT DISTINCT role FROM segment_role;
```

#### Step 2: Match Python Enums to Database

Ensure Python enum values exactly match database:

```python
# ✅ Correct - matches database values
class SpeakerRole(enum.Enum):
    """Speaker roles in coaching session."""
    COACH = "COACH"      # Must match DB exactly
    CLIENT = "CLIENT"    # Must match DB exactly
    UNKNOWN = "UNKNOWN"  # Must match DB exactly

# SQLAlchemy column configuration
role = Column(
    postgresql.ENUM('COACH', 'CLIENT', 'UNKNOWN', name='speakerrole'),
    nullable=False
)
```

#### Step 3: Test Round-Trip Conversion

Always test that enum values survive database save/load:

```python
def test_enum_database_roundtrip():
    """Test that enum values survive DB save/load."""
    # Create with enum
    segment_role = SegmentRole(
        segment_id="test",
        role=SpeakerRole.CLIENT,  # Python enum
    )

    # Save to DB
    db.session.add(segment_role)
    db.session.commit()

    # Load from DB
    loaded = db.session.query(SegmentRole).filter_by(segment_id="test").first()

    # Verify exact match
    assert loaded.role == SpeakerRole.CLIENT
    assert loaded.role.value == "CLIENT"  # Verify string value
    assert isinstance(loaded.role, SpeakerRole)  # Verify type
```

### Automated Validation

Add to CI/CD pipeline to catch mismatches early:

```python
# scripts/validate_enum_consistency.py
"""Validate that Python enums match database schema."""
from sqlalchemy import inspect, text
from coaching_assistant.infrastructure.db.session import get_database_session
from coaching_assistant.core.models.transcript import SpeakerRole

def validate_enum_consistency():
    """Check that enum values match database schema."""
    session = get_database_session()

    # Get DB enum values
    result = session.execute(text("""
        SELECT enumlabel
        FROM pg_enum
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'speakerrole')
    """))
    db_enum_values = {row[0] for row in result}

    # Get Python enum values
    py_enum_values = {e.value for e in SpeakerRole}

    # Compare
    if db_enum_values != py_enum_values:
        print(f"❌ MISMATCH DETECTED!")
        print(f"   Database has: {sorted(db_enum_values)}")
        print(f"   Python has:   {sorted(py_enum_values)}")
        print(f"   Missing in Python: {db_enum_values - py_enum_values}")
        print(f"   Missing in DB:     {py_enum_values - db_enum_values}")
        return False

    print(f"✅ Enum values match: {sorted(db_enum_values)}")
    return True

if __name__ == "__main__":
    import sys
    sys.exit(0 if validate_enum_consistency() else 1)
```

### Integration in CI/CD

```yaml
# .github/workflows/test.yml
- name: Validate Enum Consistency
  run: |
    python scripts/validate_enum_consistency.py
```

### Common Synchronization Errors

**Error 1: Case Mismatch**
```python
# Database: 'COACH'
# Python: 'coach'
# Fix: Use 'COACH' in Python
```

**Error 2: Legacy Data Format**
```python
# Old code stored: "student"  (string)
# New code expects: UserPlan.STUDENT  (enum)

# Solution: Handle both in repository
def _convert_plan_enum(self, stored_value) -> UserPlan:
    """Handle legacy string and new enum formats."""
    if isinstance(stored_value, str):
        return UserPlan(stored_value)  # String → Enum
    return stored_value
```

**Error 3: Migration Without Python Update**
```sql
-- Migration adds new value
ALTER TYPE userplan ADD VALUE 'coaching_school';

-- But Python enum not updated - causes errors!
```

### Checklist for New Enum Values

When adding new enum values:

- [ ] Write migration to add database enum value
- [ ] Update Python enum class with matching value
- [ ] Run `validate_enum_consistency.py` script
- [ ] Add test for new enum value
- [ ] Update API schemas if needed
- [ ] Test round-trip save/load
- [ ] Document the new value

## Testing Enum Migrations

### Local Testing

```bash
# Test the migration
TEST_MODE=true uv run alembic upgrade head

# Verify enum values
TEST_MODE=true uv run python -c "
from coaching_assistant.infrastructure.db.session import get_database_session
from sqlalchemy import text
session = get_database_session()
result = session.execute(text('SELECT enumlabel FROM pg_enum WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = \\'userplan\\')'))
print([row[0] for row in result])
"

# Run enum consistency validation
python scripts/validate_enum_consistency.py
```

### Production Verification

```bash
# Use emergency script to check state
PRODUCTION_DATABASE_URL="..." python scripts/emergency_enum_fix_production.py --dry-run

# Verify enum consistency in production
PRODUCTION_DATABASE_URL="..." python scripts/validate_enum_consistency.py
```

## Common Enum Migration Patterns

### 1. Adding New Plan Types

```python
# Phase 1: Add enum values
values_to_add = ['student', 'enterprise', 'coaching_school']

# Phase 2: Data migration (separate transaction)
migrations = [
    ("STUDENT", "student"),
    ("ENTERPRISE", "enterprise"),
    ("COACHING_SCHOOL", "coaching_school")
]
```

### 2. Case Normalization

```python
# Phase 1: Add lowercase versions
lowercase_values = ['free', 'pro', 'enterprise']

# Phase 2: Migrate existing data
case_migrations = [
    ("FREE", "free"),
    ("PRO", "pro"),
    ("ENTERPRISE", "enterprise")
]
```

### 3. Renaming Enum Values

```python
# Phase 1: Add new values
new_values = ['basic', 'premium', 'business']

# Phase 2: Migrate data
renames = [
    ("free", "basic"),
    ("pro", "premium"),
    ("enterprise", "business")
]

# Phase 3: Keep old values for transition period
# (Remove in future migration after application update)
```

## Monitoring and Alerting

Add monitoring for:

- **Migration failures** with enum-specific error patterns
- **Data consistency** after enum migrations
- **Enum value usage** distribution
- **Failed migration rollback** scenarios

## Related Documentation

- [PostgreSQL ENUM Documentation](https://www.postgresql.org/docs/current/datatype-enum.html)
- [Alembic Operations Reference](https://alembic.sqlalchemy.org/en/latest/ops.html)
- [SQLAlchemy Enum Types](https://docs.sqlalchemy.org/en/20/core/type_basics.html#sqlalchemy.types.Enum)

## Emergency Response

When facing enum migration issues in production:

1. **Stop deployment** immediately
2. **Run emergency enum fix script** with `--dry-run` first
3. **Verify the fix** will work before executing
4. **Execute the fix** with proper confirmation
5. **Retry deployment** after successful fix
6. **Monitor application** for any data consistency issues

---

*Last updated: September 2024*
*Author: Claude Code Assistant*