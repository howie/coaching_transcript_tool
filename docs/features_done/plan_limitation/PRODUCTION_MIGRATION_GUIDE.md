# Production Database Migration Guide

## 📋 Overview
This guide provides step-by-step instructions for migrating the production database to support the plan limitation system.

## ⚠️ Pre-Migration Checklist

### Database Backup
```bash
# Create full database backup before migration
pg_dump $PRODUCTION_DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup integrity
pg_restore --list backup_*.sql | head -20
```

### Environment Verification
```bash
# Verify production environment variables
echo "DATABASE_URL: ${DATABASE_URL:0:20}..."
echo "ENVIRONMENT: $ENVIRONMENT"

# Check current migration status
alembic current
alembic history | head -10
```

## 🚀 Migration Steps

### Step 1: Prepare Migration Environment
```bash
# Set production database URL
export DATABASE_URL="postgresql://user:password@host:port/dbname"

# Verify connection
python -c "
from coaching_assistant.core.config import Settings
import psycopg2
settings = Settings()
conn = psycopg2.connect(settings.DATABASE_URL)
print('✅ Database connection successful')
conn.close()
"
```

### Step 2: Run Database Migration
```bash
# Apply all pending migrations
alembic upgrade head

# Verify migration completed successfully
alembic current
```

### Step 3: Seed Plan Configurations
```bash
# Run the plan configuration seed script
python scripts/database/seed_plan_configurations.py

# Verify plan configurations
python -c "
from coaching_assistant.core.config import Settings
import psycopg2
settings = Settings()
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()
cur.execute('SELECT plan_type, plan_name, display_name FROM plan_configurations;')
rows = cur.fetchall()
print('Plan configurations:')
for row in rows:
    print(f'  {row[0]}: {row[1]} ({row[2]})')
print(f'Total: {len(rows)} plans')
cur.close()
conn.close()
"
```

### Step 4: Initialize User Plans
```bash
# Set all existing users to FREE plan with reset counters
python -c "
from coaching_assistant.core.config import Settings
import psycopg2
settings = Settings()
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

# Update all users to FREE plan with reset usage
cur.execute('''
    UPDATE \"user\" 
    SET plan = 'FREE',
        session_count = 0,
        transcription_count = 0,
        usage_minutes = 0,
        current_month_start = NOW()
    WHERE plan IS NULL OR plan != 'FREE';
''')

affected_rows = cur.rowcount
print(f'✅ Updated {affected_rows} users to FREE plan')

conn.commit()
cur.close()
conn.close()
"
```

## 🧪 Post-Migration Verification

### Test Plan Enforcement
```bash
# Test plan validation endpoint
curl -X POST "https://api.yourapp.com/api/v1/plan/validate-action" \
  -H "Authorization: Bearer $TEST_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"action": "create_session", "resource_size": 25}'

# Expected response: {"allowed": true, "reason": null, ...}
```

### Verify Database Schema
```bash
# Check table structure
python -c "
from coaching_assistant.core.config import Settings
import psycopg2
settings = Settings()
conn = psycopg2.connect(settings.DATABASE_URL)
cur = conn.cursor()

# Check plan_configurations table
cur.execute(\"SELECT COUNT(*) FROM plan_configurations;\")
plan_count = cur.fetchone()[0]
print(f'Plan configurations: {plan_count}')

# Check user table has plan field
cur.execute(\"SELECT COUNT(*) FROM \\\"user\\\" WHERE plan IS NOT NULL;\")
user_count = cur.fetchone()[0]
print(f'Users with plans: {user_count}')

# Check usage_history table exists
cur.execute(\"SELECT COUNT(*) FROM usage_history;\")
usage_count = cur.fetchone()[0]
print(f'Usage history records: {usage_count}')

cur.close()
conn.close()
"
```

## 🔄 Rollback Procedure (Emergency)

### Immediate Rollback
```bash
# Rollback to previous migration if issues occur
alembic downgrade e26380bb6576  # Previous stable migration

# Restore from backup if necessary
psql $DATABASE_URL < backup_YYYYMMDD_HHMMSS.sql
```

### Gradual Recovery
```bash
# If partial failure, check migration status
alembic current

# Re-run specific migration steps
alembic upgrade +1  # Apply one migration at a time
```

## 📊 Migration Status Tracking

### Development Environment ✅
- **Status**: Complete
- **Migration**: 3d7a3c607c3f (head)
- **Plan Configs**: 3 plans seeded (FREE, PRO, ENTERPRISE)
- **Users**: All set to FREE plan with reset usage

### Production Environment 🎯
- **Status**: Ready for migration
- **Prerequisites**: ✅ All met
- **Backup Required**: ✅ Yes
- **Downtime**: ~5 minutes estimated
- **Risk Level**: Low (rollback available)

## 🚨 Emergency Contacts

**Database Admin**: [Contact Info]  
**Engineering Lead**: [Contact Info]  
**DevOps Team**: [Contact Info]  
**Product Owner**: [Contact Info]

## 📝 Migration Log Template

```
Migration Date: YYYY-MM-DD HH:MM UTC
Database: Production
Performed By: [Name]
Start Time: [HH:MM UTC]
End Time: [HH:MM UTC]
Status: [SUCCESS/FAILED/PARTIAL]

Steps Completed:
[ ] Database backup created
[ ] Migration applied successfully
[ ] Plan configurations seeded
[ ] User plans initialized
[ ] Post-migration tests passed

Issues Encountered: [None/Details]
Rollback Required: [No/Yes - Details]

Notes: [Additional observations]
```

## 🎯 Success Criteria

✅ **Technical Success**:
- All migrations applied without errors
- Plan configurations table populated
- User plans initialized correctly
- API endpoints responding correctly

✅ **Business Success**:
- No user data lost
- All existing functionality preserved
- New plan features available
- System performance maintained

✅ **Operational Success**:
- Minimal downtime achieved
- Monitoring alerts functioning
- Logs show healthy system state
- Ready for beta testing with limits

---

**Last Updated**: August 17, 2025  
**Migration Target**: Production Environment  
**Estimated Downtime**: 5 minutes  
**Risk Assessment**: Low Risk (with proper backup and rollback plan)