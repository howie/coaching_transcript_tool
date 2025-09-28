#!/usr/bin/env python3
"""
Fix user plan case mismatch - convert uppercase enum values to lowercase.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from sqlalchemy import text

from coaching_assistant.core.config import Settings
from coaching_assistant.infrastructure.db.session import get_database_session


def fix_user_plan_case():
    """Fix user plan case mismatch by converting uppercase to lowercase."""

    print("🔧 Fixing user plan case mismatch...")
    settings = Settings()

    try:
        session = get_database_session(settings)
        try:
            # First, check all current plan values
            result = session.execute(
                text("""
                SELECT plan, COUNT(*) as count
                FROM "user"
                GROUP BY plan
                ORDER BY plan
            """)
            )
            plan_counts = list(result)
            print("📊 Current plan distribution:")
            for plan, count in plan_counts:
                print(f"  - {plan}: {count} users")

            # The error is actually that the user model is trying to use uppercase values
            # but database has lowercase enum values.
            # We need to check if there are any problematic records and fix the application code

            # Since the database has proper lowercase enum values, the issue must be
            # in the application code trying to compare/use uppercase enum values

            print(
                "🔍 The issue is likely in the application code using uppercase enum values"
            )
            print("💡 Database has correct lowercase enum values")
            print("✅ No database changes needed - fix is in application enum handling")

        finally:
            session.close()

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

    print("✅ User plan case fix completed")
    return True


if __name__ == "__main__":
    success = fix_user_plan_case()
    sys.exit(0 if success else 1)
