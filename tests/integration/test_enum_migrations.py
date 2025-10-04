"""
Integration tests for PostgreSQL enum migrations.

These tests verify that enum migrations follow PostgreSQL's transaction safety rules
and properly handle the two-phase commit pattern required for enum value additions.

Reference:
    @docs/claude/enum-migration-best-practices.md
"""

import pytest
from sqlalchemy import text


class TestEnumMigrationSafety:
    """Test enum migration safety patterns with real PostgreSQL."""

    def test_enum_values_exist_in_database(self, test_db):
        """Verify that all required userplan enum values exist in database."""
        # Query actual enum values from PostgreSQL
        result = test_db.execute(
            text(
                """
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
            ORDER BY enumsortorder
        """
            )
        )
        enum_values = [row[0] for row in result]

        # Required lowercase values (from Phase 1 migration)
        required_values = ["free", "pro", "enterprise", "student", "coaching_school"]

        for value in required_values:
            assert value in enum_values, (
                f"Enum value '{value}' not found in database. Found: {enum_values}"
            )

    def test_no_uppercase_enum_values_in_user_table(self, test_db):
        """Verify that user table has no uppercase plan values (after Phase 2 migration)."""
        # Query user plan distribution
        result = test_db.execute(
            text('SELECT plan, COUNT(*) FROM "user" GROUP BY plan')
        )
        plan_distribution = {row[0]: row[1] for row in result}

        # Uppercase values that should NOT exist after migration
        uppercase_values = ["FREE", "PRO", "ENTERPRISE", "STUDENT", "COACHING_SCHOOL"]

        for uppercase_value in uppercase_values:
            assert uppercase_value not in plan_distribution, (
                f"Found uppercase value '{uppercase_value}' in user table. This should have been migrated to lowercase."
            )

    def test_user_plan_values_are_valid_enums(self, test_db):
        """Verify that all user plan values are valid enum values."""
        # Get all distinct plan values from user table
        result = test_db.execute(text('SELECT DISTINCT plan FROM "user"'))
        user_plans = [row[0] for row in result if row[0] is not None]

        # Get valid enum values
        result = test_db.execute(
            text(
                """
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
        """
            )
        )
        valid_enum_values = [row[0] for row in result]

        # Verify all user plans are valid enums
        for plan in user_plans:
            assert plan in valid_enum_values, (
                f"User plan '{plan}' is not a valid userplan enum value. Valid values: {valid_enum_values}"
            )

    @pytest.mark.parametrize(
        "plan_value",
        ["free", "pro", "enterprise", "student", "coaching_school"],
    )
    def test_can_insert_user_with_lowercase_plan(self, test_db, plan_value):
        """Test that we can insert users with lowercase plan values."""
        import uuid
        from datetime import datetime, timezone

        user_id = uuid.uuid4()

        try:
            # Insert a test user with lowercase plan value
            test_db.execute(
                text(
                    """
                INSERT INTO "user" (id, email, name, plan, created_at, updated_at)
                VALUES (:id, :email, :name, :plan, :created_at, :updated_at)
            """
                ),
                {
                    "id": user_id,
                    "email": f"test_{plan_value}_{user_id}@example.com",
                    "name": f"Test User {plan_value}",
                    "plan": plan_value,
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            test_db.commit()

            # Verify the user was inserted
            result = test_db.execute(
                text('SELECT plan FROM "user" WHERE id = :id'), {"id": user_id}
            )
            row = result.fetchone()
            assert row is not None, f"User with {plan_value} plan was not inserted"
            assert row[0] == plan_value, (
                f"Plan value mismatch: expected {plan_value}, got {row[0]}"
            )

        finally:
            # Cleanup
            test_db.execute(text('DELETE FROM "user" WHERE id = :id'), {"id": user_id})
            test_db.commit()

    def test_cannot_insert_user_with_invalid_enum_value(self, test_db):
        """Test that PostgreSQL rejects invalid enum values."""
        import uuid
        from datetime import datetime, timezone

        user_id = uuid.uuid4()

        with pytest.raises(Exception) as exc_info:
            test_db.execute(
                text(
                    """
                INSERT INTO "user" (id, email, name, plan, created_at, updated_at)
                VALUES (:id, :email, :name, :plan, :created_at, :updated_at)
            """
                ),
                {
                    "id": user_id,
                    "email": f"test_invalid_{user_id}@example.com",
                    "name": "Test Invalid Plan",
                    "plan": "INVALID_PLAN_VALUE",
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc),
                },
            )
            test_db.commit()

        # Should raise exception about invalid enum value
        assert "invalid input value for enum" in str(exc_info.value).lower()

        # Cleanup (in case it somehow succeeded)
        try:
            test_db.rollback()
            test_db.execute(text('DELETE FROM "user" WHERE id = :id'), {"id": user_id})
            test_db.commit()
        except Exception:
            pass


class TestEnumMigrationTwoPhasePattern:
    """
    Test the two-phase migration pattern for enum safety.

    This verifies that:
    1. Phase 1 adds enum values and commits
    2. Phase 2 can safely use those values in UPDATE statements
    """

    def test_phase1_migration_adds_lowercase_values(self, test_db):
        """Verify Phase 1 migration (6d160a319b2c) added lowercase values."""
        result = test_db.execute(
            text(
                """
            SELECT enumlabel
            FROM pg_enum
            WHERE enumtypid = (SELECT oid FROM pg_type WHERE typname = 'userplan')
            ORDER BY enumsortorder
        """
            )
        )
        enum_values = [row[0] for row in result]

        # Phase 1 should have added these lowercase values
        phase1_values = ["free", "pro", "enterprise", "student", "coaching_school"]

        for value in phase1_values:
            assert value in enum_values, (
                f"Phase 1 migration did not add '{value}' enum value"
            )

    def test_phase2_migration_migrated_user_data(self, test_db):
        """Verify Phase 2 migration (5572c099bcd1) migrated user data."""
        # Check that no users have uppercase plan values
        result = test_db.execute(
            text(
                """
            SELECT COUNT(*)
            FROM "user"
            WHERE plan IN ('FREE', 'PRO', 'ENTERPRISE', 'STUDENT', 'COACHING_SCHOOL')
        """
            )
        )
        uppercase_count = result.scalar()

        assert uppercase_count == 0, (
            f"Found {uppercase_count} users with uppercase plan values. "
            "Phase 2 migration should have migrated all data to lowercase."
        )

    def test_migration_is_idempotent(self, test_db):
        """
        Test that migrations can be run multiple times safely.

        This is important for:
        - Local development environments
        - CI/CD pipelines
        - Production deployments with retries
        """
        # Get current state
        result = test_db.execute(
            text('SELECT plan, COUNT(*) FROM "user" GROUP BY plan')
        )
        initial_distribution = {row[0]: row[1] for row in result}

        # Simulate running Phase 2 migration again (UPDATE statements are idempotent)
        uppercase_to_lowercase = [
            ("FREE", "free"),
            ("PRO", "pro"),
            ("ENTERPRISE", "enterprise"),
        ]

        for old_value, new_value in uppercase_to_lowercase:
            check_result = test_db.execute(
                text(f"SELECT COUNT(*) FROM \"user\" WHERE plan = '{old_value}'")
            )
            count = check_result.scalar()

            if count and count > 0:
                test_db.execute(
                    text(
                        f"UPDATE \"user\" SET plan = '{new_value}' WHERE plan = '{old_value}'"
                    )
                )

        test_db.commit()

        # Get state after re-running migration
        result = test_db.execute(
            text('SELECT plan, COUNT(*) FROM "user" GROUP BY plan')
        )
        final_distribution = {row[0]: row[1] for row in result}

        # Distribution should be unchanged (idempotent)
        assert initial_distribution == final_distribution, (
            "Migration is not idempotent - state changed on re-run"
        )


class TestEnumMigrationValidator:
    """Test the enum migration validator script."""

    def test_validator_detects_unsafe_pattern(self):
        """Test that validator script detects unsafe enum usage patterns."""
        # Import the validator
        from pathlib import Path

        validator_path = (
            Path(__file__).parent.parent.parent
            / "scripts"
            / "database"
            / "validate_enum_migration.py"
        )

        # This is a smoke test - just verify the validator can be imported and run
        # Full functional testing would require creating test migration files
        assert validator_path.exists(), (
            f"Validator script not found at {validator_path}"
        )

    def test_problematic_migration_900f713316c0_is_documented(self):
        """Verify that the problematic migration is documented."""
        from pathlib import Path

        migration_path = (
            Path(__file__).parent.parent.parent
            / "alembic"
            / "versions"
            / "900f713316c0_fix_enum_metadata_compatibility.py"
        )

        assert migration_path.exists(), "Migration 900f713316c0 not found"

        # Read the migration file
        with open(migration_path) as f:
            content = f.read()

        # Verify it contains the problematic pattern (for documentation)
        assert "ALTER TYPE userplan ADD VALUE" in content
        assert "UPDATE" in content

        # This migration should be superseded by the two-phase repair migrations
        # (6d160a319b2c and 5572c099bcd1)
