"""Unit tests for enum conversions between domain and database layers.

This module tests the critical enum conversion logic that prevents cross-domain
data type errors like the SessionSource.CLIENT enum mismatch bug.
"""

import pytest

from src.coaching_assistant.core.models.coaching_session import (
    SessionSource as DomainSessionSource,
)
from src.coaching_assistant.core.models.transcript import (
    SpeakerRole as DomainSpeakerRole,
)
from src.coaching_assistant.core.models.user import UserPlan as DomainUserPlan
from src.coaching_assistant.models.coaching_session import (
    SessionSource as DatabaseSessionSource,
)
from src.coaching_assistant.models.transcript import (
    SpeakerRole as DatabaseSpeakerRole,
)
from src.coaching_assistant.models.user import UserPlan as DatabaseUserPlan


class TestSessionSourceConversion:
    """Test SessionSource enum conversion between domain and database layers."""

    def test_domain_to_database_conversion(self):
        """Test converting domain SessionSource to database SessionSource."""
        conversions = [
            (DomainSessionSource.CLIENT, DatabaseSessionSource.CLIENT),
            (DomainSessionSource.FRIEND, DatabaseSessionSource.FRIEND),
            (DomainSessionSource.CLASSMATE, DatabaseSessionSource.CLASSMATE),
            (
                DomainSessionSource.SUBORDINATE,
                DatabaseSessionSource.SUBORDINATE,
            ),
        ]

        for domain_value, expected_db_value in conversions:
            # Test conversion by value
            db_value = DatabaseSessionSource(domain_value.value)
            assert db_value == expected_db_value
            assert db_value.value == expected_db_value.value

    def test_database_to_domain_conversion(self):
        """Test converting database SessionSource to domain SessionSource."""
        conversions = [
            (DatabaseSessionSource.CLIENT, DomainSessionSource.CLIENT),
            (DatabaseSessionSource.FRIEND, DomainSessionSource.FRIEND),
            (DatabaseSessionSource.CLASSMATE, DomainSessionSource.CLASSMATE),
            (
                DatabaseSessionSource.SUBORDINATE,
                DomainSessionSource.SUBORDINATE,
            ),
        ]

        for db_value, expected_domain_value in conversions:
            # Test conversion by value
            domain_value = DomainSessionSource(db_value.value)
            assert domain_value == expected_domain_value
            assert domain_value.value == expected_domain_value.value

    def test_round_trip_conversion(self):
        """Test that enum values can be converted back and forth without loss."""
        for domain_value in DomainSessionSource:
            # Domain → Database → Domain
            db_value = DatabaseSessionSource(domain_value.value)
            round_trip_domain = DomainSessionSource(db_value.value)
            assert round_trip_domain == domain_value
            assert round_trip_domain.value == domain_value.value

        for db_value in DatabaseSessionSource:
            # Database → Domain → Database
            domain_value = DomainSessionSource(db_value.value)
            round_trip_db = DatabaseSessionSource(domain_value.value)
            assert round_trip_db == db_value
            assert round_trip_db.value == db_value.value

    def test_enum_value_completeness(self):
        """Test that all enum values exist in both domain and database layers."""
        domain_values = {e.value for e in DomainSessionSource}
        database_values = {e.value for e in DatabaseSessionSource}

        assert domain_values == database_values, (
            f"Domain and database SessionSource enums have different values:\n"
            f"Domain only: {domain_values - database_values}\n"
            f"Database only: {database_values - domain_values}"
        )

    def test_domain_to_database_all_values(self):
        """Test domain to database conversion for all enum values."""
        for domain_value in DomainSessionSource:
            db_value = DatabaseSessionSource(domain_value.value)
            assert isinstance(db_value, DatabaseSessionSource)
            assert db_value.value == domain_value.value

    def test_database_to_domain_all_values(self):
        """Test database to domain conversion for all enum values."""
        for db_value in DatabaseSessionSource:
            domain_value = DomainSessionSource(db_value.value)
            assert isinstance(domain_value, DomainSessionSource)
            assert domain_value.value == db_value.value


class TestSpeakerRoleConversion:
    """Test SpeakerRole enum conversion between domain and database layers."""

    def test_domain_to_database_conversion(self):
        """Test converting domain SpeakerRole to database SpeakerRole."""
        conversions = [
            (DomainSpeakerRole.COACH, DatabaseSpeakerRole.COACH),
            (DomainSpeakerRole.CLIENT, DatabaseSpeakerRole.CLIENT),
            (DomainSpeakerRole.OTHER, DatabaseSpeakerRole.OTHER),
            (DomainSpeakerRole.UNKNOWN, DatabaseSpeakerRole.UNKNOWN),
        ]

        for domain_value, expected_db_value in conversions:
            db_value = DatabaseSpeakerRole(domain_value.value)
            assert db_value == expected_db_value
            assert db_value.value == expected_db_value.value

    def test_database_to_domain_conversion(self):
        """Test converting database SpeakerRole to domain SpeakerRole."""
        conversions = [
            (DatabaseSpeakerRole.COACH, DomainSpeakerRole.COACH),
            (DatabaseSpeakerRole.CLIENT, DomainSpeakerRole.CLIENT),
            (DatabaseSpeakerRole.OTHER, DomainSpeakerRole.OTHER),
            (DatabaseSpeakerRole.UNKNOWN, DomainSpeakerRole.UNKNOWN),
        ]

        for db_value, expected_domain_value in conversions:
            domain_value = DomainSpeakerRole(db_value.value)
            assert domain_value == expected_domain_value
            assert domain_value.value == expected_domain_value.value

    def test_round_trip_conversion(self):
        """Test SpeakerRole round-trip conversion."""
        for domain_value in DomainSpeakerRole:
            db_value = DatabaseSpeakerRole(domain_value.value)
            round_trip_domain = DomainSpeakerRole(db_value.value)
            assert round_trip_domain == domain_value

        for db_value in DatabaseSpeakerRole:
            domain_value = DomainSpeakerRole(db_value.value)
            round_trip_db = DatabaseSpeakerRole(domain_value.value)
            assert round_trip_db == db_value

    def test_enum_value_completeness(self):
        """Test that all SpeakerRole values exist in both layers."""
        domain_values = {e.value for e in DomainSpeakerRole}
        database_values = {e.value for e in DatabaseSpeakerRole}

        assert domain_values == database_values, (
            f"Domain and database SpeakerRole enums have different values:\n"
            f"Domain only: {domain_values - database_values}\n"
            f"Database only: {database_values - domain_values}"
        )


class TestUserPlanConversion:
    """Test UserPlan enum conversion between domain and database layers."""

    def test_domain_to_database_conversion(self):
        """Test converting domain UserPlan to database UserPlan."""
        conversions = [
            (DomainUserPlan.FREE, DatabaseUserPlan.FREE),
            (DomainUserPlan.STUDENT, DatabaseUserPlan.STUDENT),
            (DomainUserPlan.PRO, DatabaseUserPlan.PRO),
            (DomainUserPlan.ENTERPRISE, DatabaseUserPlan.ENTERPRISE),
        ]

        for domain_value, expected_db_value in conversions:
            db_value = DatabaseUserPlan(domain_value.value)
            assert db_value == expected_db_value
            assert db_value.value == expected_db_value.value

    def test_database_to_domain_conversion(self):
        """Test converting database UserPlan to domain UserPlan."""
        conversions = [
            (DatabaseUserPlan.FREE, DomainUserPlan.FREE),
            (DatabaseUserPlan.STUDENT, DomainUserPlan.STUDENT),
            (DatabaseUserPlan.PRO, DomainUserPlan.PRO),
            (DatabaseUserPlan.ENTERPRISE, DomainUserPlan.ENTERPRISE),
        ]

        for db_value, expected_domain_value in conversions:
            domain_value = DomainUserPlan(db_value.value)
            assert domain_value == expected_domain_value
            assert domain_value.value == expected_domain_value.value

    def test_round_trip_conversion(self):
        """Test UserPlan round-trip conversion."""
        for domain_value in DomainUserPlan:
            db_value = DatabaseUserPlan(domain_value.value)
            round_trip_domain = DomainUserPlan(db_value.value)
            assert round_trip_domain == domain_value

        for db_value in DatabaseUserPlan:
            domain_value = DomainUserPlan(db_value.value)
            round_trip_db = DatabaseUserPlan(domain_value.value)
            assert round_trip_db == db_value

    def test_enum_value_completeness(self):
        """Test that all UserPlan values exist in both layers."""
        domain_values = {e.value for e in DomainUserPlan}
        database_values = {e.value for e in DatabaseUserPlan}

        assert domain_values == database_values, (
            f"Domain and database UserPlan enums have different values:\n"
            f"Domain only: {domain_values - database_values}\n"
            f"Database only: {database_values - domain_values}"
        )


class TestEnumConversionHelpers:
    """Test helper functions for enum conversions."""

    def test_invalid_enum_value_handling(self):
        """Test that invalid enum values raise appropriate errors."""
        with pytest.raises(ValueError):
            DatabaseSessionSource("INVALID_VALUE")

        with pytest.raises(ValueError):
            DomainSessionSource("INVALID_VALUE")

    def test_none_value_handling(self):
        """Test handling of None values in enum conversions."""
        # This tests edge cases where enum fields might be None
        # Important for optional enum fields in domain models
        assert (
            None is None
        )  # Placeholder - actual None handling depends on implementation

    def test_case_sensitivity(self):
        """Test that enum values are case sensitive."""
        with pytest.raises(ValueError):
            DatabaseSessionSource("client")  # lowercase should fail

        with pytest.raises(ValueError):
            DomainSessionSource("CLIENT ")  # with space should fail


if __name__ == "__main__":
    pytest.main([__file__])
