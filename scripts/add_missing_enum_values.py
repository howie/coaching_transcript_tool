#!/usr/bin/env python3
"""
Add missing enum values to userplan enum in database.
"""

import os
import sys

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from coaching_assistant.infrastructure.db.session import get_database_session
from coaching_assistant.core.config import Settings
from sqlalchemy import text

def add_missing_enum_values():
    """Add missing enum values to userplan enum."""

    print("🔧 Adding missing enum values to userplan enum...")
    settings = Settings()

    try:
        session = get_database_session(settings)
        try:
            # Check current enum values
            result = session.execute(text("""
                SELECT enumlabel
                FROM pg_enum
                WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
                ORDER BY enumsortorder;
            """))
            current_values = [row[0] for row in result]
            print(f"📋 Current enum values: {current_values}")

            # Add missing values if not present
            missing_values = []
            required_values = ['student', 'coaching_school']

            for value in required_values:
                if value not in current_values:
                    missing_values.append(value)

            if missing_values:
                print(f"➕ Adding missing enum values: {missing_values}")
                for value in missing_values:
                    try:
                        session.execute(text(f"ALTER TYPE userplan ADD VALUE '{value}'"))
                        session.commit()
                        print(f"✅ Added enum value: {value}")
                    except Exception as e:
                        print(f"❌ Error adding {value}: {e}")
                        session.rollback()

                # Verify the additions
                result = session.execute(text("""
                    SELECT enumlabel
                    FROM pg_enum
                    WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
                    ORDER BY enumsortorder;
                """))
                new_values = [row[0] for row in result]
                print(f"🔄 Updated enum values: {new_values}")
            else:
                print("✅ All required enum values are present")
        finally:
            session.close()

    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

    print("✅ Enum values update completed")
    return True

if __name__ == "__main__":
    success = add_missing_enum_values()
    sys.exit(0 if success else 1)