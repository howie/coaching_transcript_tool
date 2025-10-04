#!/usr/bin/env python3
"""
Validate Alembic migrations for PostgreSQL enum safety violations.

This script detects dangerous patterns in migrations that violate PostgreSQL's
enum transaction safety rules, specifically:

1. Adding enum values with ALTER TYPE ADD VALUE
2. Using those new values in UPDATE/INSERT statements
3. Both operations in the same transaction (without commit)

PostgreSQL Rule:
    New enum values must be committed before they can be used in DML statements.

Usage:
    # Validate all migrations
    python scripts/database/validate_enum_migration.py

    # Validate specific migration
    python scripts/database/validate_enum_migration.py --migration 900f713316c0

    # Use in CI/CD
    python scripts/database/validate_enum_migration.py --strict

Reference:
    @docs/claude/enum-migration-best-practices.md
"""

import argparse
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class EnumSafetyViolation:
    """Represents a detected enum safety violation."""

    def __init__(
        self, migration_file: str, line_number: int, violation_type: str, details: str
    ):
        self.migration_file = migration_file
        self.line_number = line_number
        self.violation_type = violation_type
        self.details = details

    def __str__(self):
        return (
            f"\n  ✗ {self.violation_type} at line {self.line_number}\n"
            f"    File: {self.migration_file}\n"
            f"    Details: {self.details}"
        )


class EnumMigrationValidator:
    """Validates Alembic migrations for enum safety violations."""

    # Patterns to detect
    ADD_ENUM_PATTERN = re.compile(
        r"ALTER\s+TYPE\s+(\w+)\s+ADD\s+VALUE\s+['\"](\w+)['\"]", re.IGNORECASE
    )
    UPDATE_PATTERN = re.compile(r"UPDATE\s+['\"]?(\w+)['\"]?\s+SET", re.IGNORECASE)
    INSERT_PATTERN = re.compile(r"INSERT\s+INTO\s+['\"]?(\w+)['\"]?", re.IGNORECASE)
    COMMIT_PATTERN = re.compile(r"op\.execute\(['\"]COMMIT['\"]", re.IGNORECASE)

    def __init__(self, migrations_dir: Path, strict: bool = False):
        self.migrations_dir = migrations_dir
        self.strict = strict
        self.violations: List[EnumSafetyViolation] = []

    def validate_migration_file(
        self, migration_path: Path
    ) -> List[EnumSafetyViolation]:
        """
        Validate a single migration file for enum safety violations.

        Args:
            migration_path: Path to migration file

        Returns:
            List of detected violations
        """
        violations = []

        with open(migration_path, "r") as f:
            content = f.read()
            lines = content.split("\n")

        # Track state within the migration
        added_enum_values: Dict[
            str, List[Tuple[int, str]]
        ] = {}  # enum_type -> [(line, value)]
        commit_lines: List[int] = []

        # Parse the migration
        for i, line in enumerate(lines, start=1):
            # Detect enum value additions
            add_match = self.ADD_ENUM_PATTERN.search(line)
            if add_match:
                enum_type = add_match.group(1)
                enum_value = add_match.group(2)
                if enum_type not in added_enum_values:
                    added_enum_values[enum_type] = []
                added_enum_values[enum_type].append((i, enum_value))

            # Detect commits
            if self.COMMIT_PATTERN.search(line):
                commit_lines.append(i)

            # Detect UPDATE statements
            update_match = self.UPDATE_PATTERN.search(line)
            if update_match:
                # Check if this UPDATE uses any newly added enum values
                for enum_type, value_list in added_enum_values.items():
                    for add_line, enum_value in value_list:
                        # Check if this UPDATE is after the ADD but before a COMMIT
                        if add_line < i and not any(
                            add_line < c < i for c in commit_lines
                        ):
                            # Check if the UPDATE uses the new enum value
                            if enum_value in line:
                                violations.append(
                                    EnumSafetyViolation(
                                        migration_file=migration_path.name,
                                        line_number=i,
                                        violation_type="UNSAFE_ENUM_USAGE",
                                        details=f"UPDATE uses new enum value '{enum_value}' "
                                        f"of type '{enum_type}' added at line {add_line} "
                                        f"without intermediate COMMIT",
                                    )
                                )

            # Detect INSERT statements (less common but also problematic)
            insert_match = self.INSERT_PATTERN.search(line)
            if insert_match:
                for enum_type, value_list in added_enum_values.items():
                    for add_line, enum_value in value_list:
                        if add_line < i and not any(
                            add_line < c < i for c in commit_lines
                        ):
                            if enum_value in line:
                                violations.append(
                                    EnumSafetyViolation(
                                        migration_file=migration_path.name,
                                        line_number=i,
                                        violation_type="UNSAFE_ENUM_USAGE",
                                        details=f"INSERT uses new enum value '{enum_value}' "
                                        f"of type '{enum_type}' added at line {add_line} "
                                        f"without intermediate COMMIT",
                                    )
                                )

        # Check for migrations that add enums but don't have any commits
        if added_enum_values and not commit_lines:
            # This is a warning, not necessarily an error
            first_add_line = min(
                line for values in added_enum_values.values() for line, _ in values
            )
            if self.strict:
                violations.append(
                    EnumSafetyViolation(
                        migration_file=migration_path.name,
                        line_number=first_add_line,
                        violation_type="MISSING_COMMIT",
                        details="Migration adds enum values but contains no explicit "
                        "COMMIT statements. Consider splitting into separate migrations "
                        "or adding op.execute('COMMIT') after enum additions.",
                    )
                )

        return violations

    def validate_all_migrations(self) -> bool:
        """
        Validate all migration files in the migrations directory.

        Returns:
            True if all migrations are safe, False if violations found
        """
        migration_files = sorted(self.migrations_dir.glob("*.py"))

        # Filter out __init__.py and non-migration files
        migration_files = [
            f
            for f in migration_files
            if f.name != "__init__.py" and not f.name.startswith(".")
        ]

        print("=" * 80)
        print("ENUM MIGRATION SAFETY VALIDATOR")
        print("=" * 80)
        print(f"Migrations directory: {self.migrations_dir}")
        print(f"Found {len(migration_files)} migration files")
        print(f"Mode: {'STRICT (warnings as errors)' if self.strict else 'NORMAL'}")
        print("=" * 80)

        all_violations = []

        for migration_file in migration_files:
            violations = self.validate_migration_file(migration_file)
            if violations:
                all_violations.extend(violations)

        # Report results
        if all_violations:
            print(f"\n✗ Found {len(all_violations)} enum safety violation(s):\n")
            for violation in all_violations:
                print(violation)

            print("\n" + "=" * 80)
            print("RECOMMENDATIONS")
            print("=" * 80)
            print(
                """
1. Split problematic migrations into two phases:
   Phase 1: Add enum values + COMMIT
   Phase 2: Migrate data using new values

2. Use explicit commits in migrations:
   op.execute('COMMIT')

3. Reference: @docs/claude/enum-migration-best-practices.md

4. Example fix:
   # ❌ UNSAFE (violates PostgreSQL rules)
   op.execute("ALTER TYPE userplan ADD VALUE 'free'")
   op.execute("UPDATE user SET plan = 'free' WHERE plan = 'FREE'")

   # ✅ SAFE (two-phase with commit)
   op.execute("ALTER TYPE userplan ADD VALUE 'free'")
   op.execute("COMMIT")
   # In next migration or after transaction:
   op.execute("UPDATE user SET plan = 'free' WHERE plan = 'FREE'")
"""
            )
            return False

        print("\n✓ All migrations passed enum safety validation")
        return True

    def validate_specific_migration(self, migration_id: str) -> bool:
        """
        Validate a specific migration by its ID.

        Args:
            migration_id: Migration revision ID

        Returns:
            True if migration is safe, False if violations found
        """
        # Find migration file
        migration_files = list(self.migrations_dir.glob(f"{migration_id}*.py"))

        if not migration_files:
            print(f"✗ Migration not found: {migration_id}")
            return False

        migration_file = migration_files[0]

        print("=" * 80)
        print(f"VALIDATING: {migration_file.name}")
        print("=" * 80)

        violations = self.validate_migration_file(migration_file)

        if violations:
            print(f"\n✗ Found {len(violations)} violation(s):")
            for violation in violations:
                print(violation)
            return False

        print("\n✓ Migration passed enum safety validation")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="Validate Alembic migrations for enum safety violations"
    )
    parser.add_argument(
        "--migration",
        type=str,
        help="Validate specific migration by revision ID (e.g., 900f713316c0)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict mode (treat warnings as errors)",
    )
    parser.add_argument(
        "--migrations-dir",
        type=str,
        help="Path to migrations directory (default: alembic/versions/)",
    )

    args = parser.parse_args()

    # Determine migrations directory
    if args.migrations_dir:
        migrations_dir = Path(args.migrations_dir)
    else:
        # Default to alembic/versions relative to script location
        script_dir = Path(__file__).parent.parent.parent
        migrations_dir = script_dir / "alembic" / "versions"

    if not migrations_dir.exists():
        print(f"✗ Error: Migrations directory not found: {migrations_dir}")
        sys.exit(1)

    # Create validator
    validator = EnumMigrationValidator(migrations_dir, strict=args.strict)

    # Run validation
    if args.migration:
        success = validator.validate_specific_migration(args.migration)
    else:
        success = validator.validate_all_migrations()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
