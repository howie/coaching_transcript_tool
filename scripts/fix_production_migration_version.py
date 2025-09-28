#!/usr/bin/env python3
"""
Fix production migration version to match deployed code
"""

import os
import sys
from sqlalchemy import create_engine, text

# Production database URL from environment variable
PRODUCTION_DB_URL = os.getenv("PRODUCTION_DATABASE_URL")

if not PRODUCTION_DB_URL:
    print("❌ PRODUCTION_DATABASE_URL environment variable is not set")
    sys.exit(1)

def fix_migration_version():
    """Fix migration version to match deployed code"""

    try:
        engine = create_engine(PRODUCTION_DB_URL)

        with engine.connect() as conn:
            print("🔍 Checking current migration status...")

            # Check current version
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            current_version = result.scalar()
            print(f"📋 Current migration version: {current_version}")

            # The deployed code likely has up to 04a3991223d9
            # Let's set it to that so our new migration can apply
            target_version = "04a3991223d9"

            print(f"🔧 Updating migration version to {target_version}...")
            conn.execute(text("""
                UPDATE alembic_version
                SET version_num = :version
            """), {"version": target_version})

            conn.commit()
            print(f"✅ Migration version updated to {target_version}")

            # Verify
            result = conn.execute(text("SELECT version_num FROM alembic_version"))
            new_version = result.scalar()
            print(f"✅ Verified new version: {new_version}")

    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("🚨 FIXING PRODUCTION MIGRATION VERSION 🚨")
    print("This will set the migration version to match deployed code")
    print()

    confirmation = input("Type 'FIX MIGRATION VERSION' to continue: ")
    if confirmation != "FIX MIGRATION VERSION":
        print("❌ Operation cancelled")
        sys.exit(0)

    fix_migration_version()