#!/usr/bin/env python3
"""
Check the current migration status in production
"""

import os
import sys
from sqlalchemy import create_engine, text

# Production database URL from environment variable
PRODUCTION_DB_URL = os.getenv("PRODUCTION_DATABASE_URL")

if not PRODUCTION_DB_URL:
    print("❌ PRODUCTION_DATABASE_URL environment variable is not set")
    sys.exit(1)

def check_migration_status():
    """Check current migration status and enum state"""

    try:
        engine = create_engine(PRODUCTION_DB_URL)

        with engine.connect() as conn:
            print("🔍 Checking production migration status...")

            # Check current migration version
            try:
                result = conn.execute(text("SELECT version_num FROM alembic_version"))
                current_version = result.scalar()
                print(f"📋 Current migration version: {current_version}")
            except Exception as e:
                print(f"❌ Error checking migration version: {e}")

            # Check enum values
            try:
                result = conn.execute(text("""
                    SELECT enumlabel
                    FROM pg_enum
                    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
                    ORDER BY enumsortorder
                """))
                enum_values = [row[0] for row in result]
                print(f"📋 Current enum values: {enum_values}")
            except Exception as e:
                print(f"❌ Error checking enum values: {e}")

            # Check user plan distribution
            try:
                result = conn.execute(text("""
                    SELECT plan, COUNT(*) as count
                    FROM "user"
                    GROUP BY plan
                    ORDER BY count DESC
                """))
                plans = result.fetchall()
                print(f"📊 User plan distribution:")
                for plan in plans:
                    print(f"   {plan[0]}: {plan[1]} users")
            except Exception as e:
                print(f"❌ Error checking user plans: {e}")

            # Check if there are any tables with enum issues
            try:
                result = conn.execute(text("""
                    SELECT table_name, column_name, data_type
                    FROM information_schema.columns
                    WHERE udt_name = 'userplan'
                """))
                enum_columns = result.fetchall()
                print(f"📋 Tables using userplan enum:")
                for col in enum_columns:
                    print(f"   {col[0]}.{col[1]} ({col[2]})")
            except Exception as e:
                print(f"❌ Error checking enum usage: {e}")

            print("✅ Migration status check completed")

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    check_migration_status()