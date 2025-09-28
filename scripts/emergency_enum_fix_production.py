#!/usr/bin/env python3
"""
Emergency script to fix enum migration issue in production

This script addresses the PostgreSQL enum migration error by:
1. Adding missing enum values to userplan enum type
2. Migrating existing user data to new enum values
3. Updating the migration state properly

Environment Variables Required:
    PRODUCTION_DATABASE_URL - Full PostgreSQL connection string for production

Usage:
    export PRODUCTION_DATABASE_URL="postgresql://user:pass@host:port/db"
    python scripts/emergency_enum_fix_production.py --dry-run
    python scripts/emergency_enum_fix_production.py --execute

Security Note:
    This script requires production database credentials. Never commit
    these credentials to git. Always use environment variables.
"""

import argparse
import logging
import os
import sys

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Production database URL from environment variable
PRODUCTION_DB_URL = os.getenv("PRODUCTION_DATABASE_URL")

if not PRODUCTION_DB_URL:
    logger.error("❌ PRODUCTION_DATABASE_URL environment variable is not set")
    logger.error("💡 Please set PRODUCTION_DATABASE_URL before running this script")
    logger.error(
        "Example: export PRODUCTION_DATABASE_URL='postgresql://user:pass@host:port/db'"
    )
    sys.exit(1)


def get_production_db():
    """Create connection to production database"""
    engine = create_engine(PRODUCTION_DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


def check_current_enum_values(db):
    """Check current userplan enum values"""
    logger.info("🔍 Checking current userplan enum values...")

    try:
        # Rollback any pending transaction first
        db.rollback()

        result = db.execute(
            text("""
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
            ORDER BY enumsortorder;
        """)
        )
        current_values = [row[0] for row in result]
        logger.info(f"📋 Current enum values: {current_values}")
        return current_values
    except Exception as e:
        logger.error(f"❌ Error checking enum values: {e}")
        db.rollback()
        return []


def check_user_plan_distribution(db):
    """Check distribution of user plans"""
    logger.info("📊 Checking user plan distribution...")

    try:
        # Rollback any pending transaction first
        db.rollback()

        result = db.execute(
            text("""
            SELECT plan, COUNT(*) as count
            FROM "user"
            GROUP BY plan
            ORDER BY count DESC;
        """)
        )

        plan_counts = result.fetchall()
        total_users = sum(row.count for row in plan_counts)

        logger.info(f"👥 Total users: {total_users}")
        for row in plan_counts:
            percentage = (row.count / total_users * 100) if total_users > 0 else 0
            logger.info(f"   📋 {row.plan}: {row.count} ({percentage:.1f}%)")

        return plan_counts
    except Exception as e:
        logger.error(f"❌ Error checking user plans: {e}")
        db.rollback()
        return []


def add_missing_enum_values(db, dry_run=True):
    """Add missing enum values to userplan enum"""
    logger.info("🔧 Adding missing enum values to userplan enum...")

    try:
        # Check current values
        current_values = check_current_enum_values(db)

        # Define required values
        required_values = ["free", "pro", "enterprise", "student", "coaching_school"]
        missing_values = [
            value for value in required_values if value not in current_values
        ]

        if not missing_values:
            logger.info("✅ All required enum values already exist")
            return True

        logger.info(f"➕ Missing enum values: {missing_values}")

        if not dry_run:
            for value in missing_values:
                try:
                    logger.info(f"   Adding enum value: {value}")
                    db.execute(text(f"ALTER TYPE userplan ADD VALUE '{value}'"))
                    db.commit()  # Commit each enum addition separately
                    logger.info(f"   ✅ Added: {value}")
                except Exception as e:
                    logger.error(f"   ❌ Failed to add {value}: {e}")
                    db.rollback()
                    return False

            # Verify additions
            new_values = check_current_enum_values(db)
            logger.info(f"🔄 Updated enum values: {new_values}")
        else:
            logger.info(f"🔍 DRY RUN: Would add enum values: {missing_values}")

        return True

    except Exception as e:
        logger.error(f"❌ Error adding enum values: {e}")
        if not dry_run:
            db.rollback()
        return False


def migrate_user_data(db, dry_run=True):
    """Migrate existing user data to new enum values"""
    logger.info("🔄 Migrating user data to new enum values...")

    try:
        # Rollback any pending transaction first
        db.rollback()

        # Check what needs to be migrated
        result = db.execute(
            text("""
            SELECT plan, COUNT(*) as count
            FROM "user"
            WHERE plan IN ('FREE', 'PRO', 'ENTERPRISE')
            GROUP BY plan;
        """)
        )

        migration_needed = result.fetchall()

        if not migration_needed:
            logger.info("✅ No user data migration needed")
            return True

        logger.info("📋 Users needing migration:")
        total_to_migrate = 0
        for row in migration_needed:
            logger.info(f"   {row.plan}: {row.count} users")
            total_to_migrate += row.count

        logger.info(f"📊 Total users to migrate: {total_to_migrate}")

        if not dry_run:
            # Perform migrations
            migrations = [
                ("FREE", "free"),
                ("PRO", "pro"),
                ("ENTERPRISE", "enterprise"),
            ]

            total_migrated = 0
            for old_value, new_value in migrations:
                logger.info(f"🔄 Migrating {old_value} → {new_value}")
                result = db.execute(
                    text(f"""
                    UPDATE "user"
                    SET plan = '{new_value}'
                    WHERE plan = '{old_value}'
                """)
                )

                rows_affected = result.rowcount
                if rows_affected > 0:
                    logger.info(f"   ✅ Migrated {rows_affected} users")
                    total_migrated += rows_affected
                else:
                    logger.info(f"   ℹ️  No users with {old_value} plan")

            db.commit()
            logger.info(f"✅ Successfully migrated {total_migrated} users")

            # Verify migration
            result = db.execute(
                text("""
                SELECT plan, COUNT(*) as count
                FROM "user"
                WHERE plan IN ('FREE', 'PRO', 'ENTERPRISE')
                GROUP BY plan;
            """)
            )

            remaining_old = result.fetchall()
            if remaining_old:
                logger.warning("⚠️  Still have users with old enum values:")
                for row in remaining_old:
                    logger.warning(f"   {row.plan}: {row.count} users")
            else:
                logger.info("✅ All users successfully migrated to new enum values")
        else:
            logger.info(f"🔍 DRY RUN: Would migrate {total_to_migrate} users")

        return True

    except Exception as e:
        logger.error(f"❌ Error migrating user data: {e}")
        db.rollback()
        return False


def check_migration_state(db):
    """Check the current migration state"""
    logger.info("🔍 Checking migration state...")

    try:
        # Rollback any pending transaction first
        db.rollback()

        # Check alembic version table structure first
        try:
            result = db.execute(
                text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = 'alembic_version'
                ORDER BY ordinal_position;
            """)
            )
            columns = [row[0] for row in result]
            logger.info(f"📋 Alembic version table columns: {columns}")
        except Exception as e:
            logger.warning(f"⚠️  Could not check alembic table structure: {e}")

        # Check current version (simpler query)
        result = db.execute(
            text("""
            SELECT version_num
            FROM alembic_version
            LIMIT 1;
        """)
        )

        version_row = result.fetchone()
        current_version = version_row[0] if version_row else "None"
        logger.info(f"📋 Current migration version: {current_version}")

        # Check if our problematic migration is marked as applied
        problematic_version = "04a3991223d9"

        if current_version == problematic_version:
            logger.warning(
                f"⚠️  Migration {problematic_version} is marked as current but may have failed"
            )
        else:
            logger.info(
                f"ℹ️  Current version {current_version} != problematic version {problematic_version}"
            )

        return current_version

    except Exception as e:
        logger.error(f"❌ Error checking migration state: {e}")
        db.rollback()
        return None


def fix_migration_state(db, dry_run=True):
    """Fix the migration state after manual enum fix"""
    logger.info("🔧 Fixing migration state...")

    problematic_version = "04a3991223d9"

    try:
        # Check if migration is already marked as applied
        result = db.execute(
            text("""
            SELECT version_num FROM alembic_version
            WHERE version_num = :version
        """),
            {"version": problematic_version},
        )

        existing = result.fetchone()

        if existing:
            logger.info(f"ℹ️  Migration {problematic_version} already marked as applied")
            return True

        if not dry_run:
            # Mark the migration as applied since we've manually fixed it
            logger.info(f"📝 Marking migration {problematic_version} as applied...")
            db.execute(
                text("""
                UPDATE alembic_version
                SET version_num = :version
            """),
                {"version": problematic_version},
            )

            db.commit()
            logger.info(f"✅ Migration {problematic_version} marked as applied")
        else:
            logger.info(
                f"🔍 DRY RUN: Would mark migration {problematic_version} as applied"
            )

        return True

    except Exception as e:
        logger.error(f"❌ Error fixing migration state: {e}")
        if not dry_run:
            db.rollback()
        return False


def run_full_fix(dry_run=True):
    """Run the complete enum fix process"""
    logger.info(f"🚀 Starting enum fix process (dry_run={dry_run})...")

    try:
        db = get_production_db()
    except Exception as e:
        logger.error(f"❌ Failed to connect to production database: {e}")
        return False

    try:
        # Step 1: Check current state
        logger.info("=" * 60)
        logger.info("STEP 1: CHECKING CURRENT STATE")
        logger.info("=" * 60)

        check_current_enum_values(db)
        check_user_plan_distribution(db)
        current_migration = check_migration_state(db)

        # Step 2: Add missing enum values
        logger.info("\n" + "=" * 60)
        logger.info("STEP 2: ADDING MISSING ENUM VALUES")
        logger.info("=" * 60)

        if not add_missing_enum_values(db, dry_run):
            logger.error("❌ Failed to add missing enum values")
            return False

        # Step 3: Migrate user data
        logger.info("\n" + "=" * 60)
        logger.info("STEP 3: MIGRATING USER DATA")
        logger.info("=" * 60)

        if not migrate_user_data(db, dry_run):
            logger.error("❌ Failed to migrate user data")
            return False

        # Step 4: Fix migration state
        logger.info("\n" + "=" * 60)
        logger.info("STEP 4: FIXING MIGRATION STATE")
        logger.info("=" * 60)

        if not fix_migration_state(db, dry_run):
            logger.error("❌ Failed to fix migration state")
            return False

        logger.info("\n" + "=" * 60)
        logger.info("✅ ENUM FIX COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)

        if dry_run:
            logger.info("🔍 This was a DRY RUN - no changes were made")
            logger.info("💡 Use --execute to apply the fix")
        else:
            logger.info("✅ Production database has been fixed")
            logger.info("🚀 You can now retry the deployment")

        return True

    except Exception as e:
        logger.error(f"❌ Unexpected error during fix: {e}")
        return False

    finally:
        db.close()
        logger.info("🔌 Database connection closed")


def main():
    parser = argparse.ArgumentParser(
        description="Fix enum migration issue in production",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚨 PRODUCTION DATABASE WARNING 🚨
This script connects directly to the production database!

Environment Setup Required:
  export PRODUCTION_DATABASE_URL="postgresql://user:pass@host:port/db"

Examples:
  # Check what would be fixed (safe)
  PRODUCTION_DATABASE_URL="..." python scripts/emergency_enum_fix_production.py --dry-run  # noqa: E501

  # Actually fix the enum issue
  PRODUCTION_DATABASE_URL="..." python scripts/emergency_enum_fix_production.py --execute  # noqa: E501
        """,
    )

    parser.add_argument(
        "--execute", action="store_true", help="Actually execute changes (PRODUCTION)"
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Only show what would be done (default)"
    )

    args = parser.parse_args()

    print("🚨" + "=" * 60 + "🚨")
    print("🚨  PRODUCTION ENUM FIX EMERGENCY SCRIPT  🚨")
    print("🚨" + "=" * 60 + "🚨")
    print(
        f"🔗 Database: {PRODUCTION_DB_URL.split('@')[-1].split('?')[0]}"
    )  # Show host without credentials
    print("")

    # Handle conflicting flags
    if args.execute and args.dry_run:
        logger.error("❌ Cannot specify both --execute and --dry-run")
        sys.exit(1)

    # Determine if this is a dry run
    dry_run = not args.execute

    # Show extra warning for execute mode
    if not dry_run:
        print("⚠️ " + "=" * 50 + " ⚠️")
        print("⚠️   PRODUCTION DATABASE MODIFICATION WARNING   ⚠️")
        print("⚠️ " + "=" * 50 + " ⚠️")
        print("This will MODIFY the production database!")
        print("It will:")
        print("  1. Add missing enum values to userplan type")
        print("  2. Migrate user data to new enum values")
        print("  3. Mark the failed migration as complete")
        print("")
        print("Type 'FIX ENUM PRODUCTION' to confirm:")

        confirmation = input().strip()
        if confirmation != "FIX ENUM PRODUCTION":
            print("❌ Operation cancelled.")
            sys.exit(0)
        print()

    # Run the fix
    success = run_full_fix(dry_run)

    print("\n" + "📋 " + "=" * 50)
    if dry_run:
        print("📋 DRY RUN SUMMARY:")
        if success:
            print("✅ The enum fix process would succeed")
            print("💡 Use --execute to actually apply the fix")
        else:
            print("❌ The enum fix process would fail")
            print("🔍 Check the errors above and fix them first")
    else:
        print("✅ EXECUTION SUMMARY:")
        if success:
            print("✅ Production enum issue has been fixed")
            print("🚀 You can now retry the deployment")
            print("📝 The migration should now succeed")
        else:
            print("❌ Failed to fix the enum issue")
            print("🔍 Check the errors above and try manual intervention")
    print("📋 " + "=" * 50)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
