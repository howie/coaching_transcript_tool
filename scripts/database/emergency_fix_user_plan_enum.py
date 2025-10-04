#!/usr/bin/env python3
"""
Emergency script to fix user plan enum values in production.

This script repairs the database state caused by migration 900f713316c0
which violated PostgreSQL's enum transaction safety rules.

Problem:
- Migration added new enum values (free, pro, enterprise) in lowercase
- Then tried to UPDATE user records in same transaction
- PostgreSQL rejected: "unsafe use of new value"
- Database left in inconsistent state with uppercase values (FREE, PRO, ENTERPRISE)

Solution:
- Safely migrate uppercase enum values to lowercase
- Verify database state before and after
- Support dry-run mode for safety

Usage:
    # Check current state without making changes
    python scripts/database/emergency_fix_user_plan_enum.py --dry-run

    # Apply the fix to production
    python scripts/database/emergency_fix_user_plan_enum.py --env=production

    # Apply to staging for testing
    python scripts/database/emergency_fix_user_plan_enum.py --env=staging
"""

import argparse
import sys
from typing import Dict, List, Tuple

import psycopg2


class UserPlanEnumFixer:
    """Fixes user plan enum values from uppercase to lowercase."""

    # Map of old (uppercase) to new (lowercase) values
    ENUM_MIGRATIONS = {
        "FREE": "free",
        "PRO": "pro",
        "ENTERPRISE": "enterprise",
        "STUDENT": "student",  # In case it exists in uppercase
        "COACHING_SCHOOL": "coaching_school",
    }

    def __init__(self, database_url: str, dry_run: bool = True):
        self.database_url = database_url
        self.dry_run = dry_run
        self.conn = None

    def connect(self):
        """Establish database connection."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            print("✓ Connected to database")
        except Exception as e:
            print(f"✗ Failed to connect to database: {e}")
            sys.exit(1)

    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            print("✓ Disconnected from database")

    def get_enum_values(self) -> List[str]:
        """Query all current enum values for userplan type."""
        query = """
        SELECT enumlabel
        FROM pg_enum
        WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
        ORDER BY enumsortorder;
        """
        with self.conn.cursor() as cur:
            cur.execute(query)
            return [row[0] for row in cur.fetchall()]

    def get_user_plan_distribution(self) -> Dict[str, int]:
        """Query distribution of plan values in user table."""
        query = 'SELECT plan, COUNT(*) FROM "user" GROUP BY plan ORDER BY plan;'
        with self.conn.cursor() as cur:
            cur.execute(query)
            return {row[0]: row[1] for row in cur.fetchall()}

    def verify_state(self) -> Tuple[List[str], Dict[str, int]]:
        """Verify current database state."""
        print("\n" + "=" * 80)
        print("DATABASE STATE VERIFICATION")
        print("=" * 80)

        # Check enum values
        enum_values = self.get_enum_values()
        print(f"\nUserPlan Enum Values ({len(enum_values)}):")
        for value in enum_values:
            print(f"  - {value}")

        # Check user plan distribution
        distribution = self.get_user_plan_distribution()
        print(f"\nUser Plan Distribution ({sum(distribution.values())} total users):")
        for plan, count in distribution.items():
            print(f"  - {plan}: {count} users")

        return enum_values, distribution

    def check_migration_needed(
        self, distribution: Dict[str, int]
    ) -> List[Tuple[str, str, int]]:
        """
        Check which migrations are needed.

        Returns:
            List of (old_value, new_value, user_count) tuples
        """
        migrations_needed = []
        for old_value, new_value in self.ENUM_MIGRATIONS.items():
            if old_value in distribution:
                user_count = distribution[old_value]
                migrations_needed.append((old_value, new_value, user_count))

        return migrations_needed

    def apply_migrations(self, migrations: List[Tuple[str, str, int]]) -> bool:
        """
        Apply enum value migrations.

        Args:
            migrations: List of (old_value, new_value, user_count) tuples

        Returns:
            True if successful, False otherwise
        """
        if not migrations:
            print("\n✓ No migrations needed - database is already in correct state")
            return True

        print("\n" + "=" * 80)
        print("MIGRATION PLAN")
        print("=" * 80)

        for old_value, new_value, user_count in migrations:
            print(
                f"  {old_value} → {new_value} ({user_count} user{'s' if user_count != 1 else ''})"
            )

        if self.dry_run:
            print("\n⚠️  DRY RUN MODE - No changes will be made")
            print("   Run without --dry-run to apply changes")
            return True

        # Confirm with user
        print("\n" + "⚠️  WARNING: This will modify production data!")
        response = input("Continue with migration? (yes/no): ")
        if response.lower() != "yes":
            print("✗ Migration cancelled by user")
            return False

        # Apply migrations
        print("\n" + "=" * 80)
        print("APPLYING MIGRATIONS")
        print("=" * 80)

        try:
            with self.conn.cursor() as cur:
                for old_value, new_value, user_count in migrations:
                    print(f"\n  Migrating {old_value} → {new_value}...")

                    # Update user records
                    update_query = f"""
                    UPDATE "user"
                    SET plan = '{new_value}'
                    WHERE plan = '{old_value}';
                    """
                    cur.execute(update_query)
                    rows_affected = cur.rowcount

                    if rows_affected != user_count:
                        print(
                            f"    ⚠️  Warning: Expected {user_count} rows, "
                            f"updated {rows_affected}"
                        )
                    else:
                        print(f"    ✓ Updated {rows_affected} user records")

                # Commit transaction
                self.conn.commit()
                print("\n✓ All migrations committed successfully")
                return True

        except Exception as e:
            print(f"\n✗ Migration failed: {e}")
            self.conn.rollback()
            print("✓ Transaction rolled back - no changes made")
            return False

    def run(self) -> bool:
        """
        Execute the complete repair process.

        Returns:
            True if successful or no changes needed, False otherwise
        """
        try:
            self.connect()

            # Verify current state
            enum_values, distribution = self.verify_state()

            # Check what migrations are needed
            migrations = self.check_migration_needed(distribution)

            # Apply migrations
            success = self.apply_migrations(migrations)

            if success and not self.dry_run:
                # Verify final state
                print("\n" + "=" * 80)
                print("POST-MIGRATION VERIFICATION")
                print("=" * 80)
                self.verify_state()

            return success

        finally:
            self.disconnect()


def main():
    parser = argparse.ArgumentParser(
        description="Fix user plan enum values in production database"
    )
    parser.add_argument(
        "--env",
        choices=["production", "staging", "development"],
        default="development",
        help="Environment to run against (default: development)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Run in dry-run mode without making changes (default: True)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute the changes (disables dry-run)",
    )
    parser.add_argument(
        "--database-url", type=str, help="Database URL (overrides environment)"
    )

    args = parser.parse_args()

    # Determine dry-run mode
    dry_run = not args.execute

    # Get database URL
    if args.database_url:
        database_url = args.database_url
    else:
        # Import here to avoid dependency issues
        import os

        from dotenv import load_dotenv

        load_dotenv()

        # Get environment-specific database URL
        env_var_map = {
            "production": "PRODUCTION_DATABASE_URL",
            "staging": "STAGING_DATABASE_URL",
            "development": "DATABASE_URL",
        }

        env_var = env_var_map.get(args.env)
        database_url = os.getenv(env_var)

        if not database_url:
            print(f"✗ Error: {env_var} not found in environment")
            print("  Set the environment variable or use --database-url")
            sys.exit(1)

    # Display configuration
    print("=" * 80)
    print("USER PLAN ENUM REPAIR SCRIPT")
    print("=" * 80)
    print(f"Environment: {args.env}")
    print(
        f"Mode: {'DRY RUN (no changes)' if dry_run else 'EXECUTE (will modify data)'}"
    )
    print(f"Database: {database_url.split('@')[1] if '@' in database_url else 'local'}")
    print("=" * 80)

    # Run the fixer
    fixer = UserPlanEnumFixer(database_url, dry_run=dry_run)
    success = fixer.run()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
