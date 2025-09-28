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
```

### Production Verification

```bash
# Use emergency script to check state
PRODUCTION_DATABASE_URL="..." python scripts/emergency_enum_fix_production.py --dry-run
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