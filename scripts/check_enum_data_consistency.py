#!/usr/bin/env python3
"""
Check data consistency across all tables using userplan enum
"""

import os
import sys

from sqlalchemy import create_engine, text

# Production database URL from environment variable
PRODUCTION_DB_URL = os.getenv("PRODUCTION_DATABASE_URL")

if not PRODUCTION_DB_URL:
    print("❌ PRODUCTION_DATABASE_URL environment variable is not set")
    sys.exit(1)


def check_enum_data_consistency():
    """Check data consistency across all tables using userplan enum"""

    try:
        engine = create_engine(PRODUCTION_DB_URL)

        with engine.connect() as conn:
            print("🔍 Checking enum data consistency across all tables...")

            # Check each table that uses userplan enum
            tables_to_check = [
                ("user", "plan"),
                ("plan_configurations", "plan_type"),
                ("subscription_history", "old_plan"),
                ("subscription_history", "new_plan"),
            ]

            for table_name, column_name in tables_to_check:
                print(f"\n📋 Checking {table_name}.{column_name}:")

                try:
                    # Check if table exists
                    result = conn.execute(
                        text(f"""
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_name = '{table_name}'
                    """)
                    )

                    if result.scalar() == 0:
                        print(f"   ⚠️  Table '{table_name}' does not exist")
                        continue

                    # Check column values
                    result = conn.execute(
                        text(f"""
                        SELECT {column_name}, COUNT(*) as count
                        FROM "{table_name}"
                        WHERE {column_name} IS NOT NULL
                        GROUP BY {column_name}
                        ORDER BY count DESC
                    """)
                    )

                    values = result.fetchall()
                    if values:
                        print(f"   📊 Values in {table_name}.{column_name}:")
                        for value in values:
                            print(f"     {value[0]}: {value[1]} rows")
                    else:
                        print(f"   ℹ️  No data in {table_name}.{column_name}")

                except Exception as e:
                    print(f"   ❌ Error checking {table_name}.{column_name}: {e}")

            # Check for any invalid enum values
            print("\n🔍 Checking for invalid enum values...")
            valid_values = [
                "FREE",
                "PRO",
                "ENTERPRISE",
                "free",
                "pro",
                "enterprise",
                "student",
                "coaching_school",
            ]

            for table_name, column_name in tables_to_check:
                try:
                    result = conn.execute(
                        text(f"""
                        SELECT COUNT(*)
                        FROM information_schema.tables
                        WHERE table_name = '{table_name}'
                    """)
                    )

                    if result.scalar() == 0:
                        continue

                    # Find invalid values
                    placeholders = "'" + "','".join(valid_values) + "'"
                    result = conn.execute(
                        text(f"""
                        SELECT DISTINCT {column_name}
                        FROM "{table_name}"
                        WHERE {column_name} IS NOT NULL
                        AND {column_name} NOT IN ({placeholders})
                    """)
                    )

                    invalid_values = [row[0] for row in result]
                    if invalid_values:
                        print(
                            f"   ⚠️  Invalid values in {table_name}.{column_name}: {invalid_values}"
                        )
                    else:
                        print(f"   ✅ All values valid in {table_name}.{column_name}")

                except Exception as e:
                    print(
                        f"   ❌ Error checking invalid values in {table_name}.{column_name}: {e}"
                    )

            print("\n✅ Enum data consistency check completed")

    except Exception as e:
        print(f"❌ Database connection error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_enum_data_consistency()
