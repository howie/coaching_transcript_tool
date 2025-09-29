"""Integration tests for repository layer conversions.

These tests verify that repository _to_domain() and _from_domain() methods
correctly handle enum conversions and prevent data type mismatches.
"""

from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from src.coaching_assistant.core.models.coaching_session import (
    CoachingSession as DomainCoachingSession,
)
from src.coaching_assistant.core.models.coaching_session import (
    SessionSource as DomainSessionSource,
)
from src.coaching_assistant.core.models.user import User as DomainUser
from src.coaching_assistant.core.models.user import UserPlan as DomainUserPlan
from src.coaching_assistant.infrastructure.db.repositories.coaching_session_repository import (
    SQLAlchemyCoachingSessionRepository,
)
from src.coaching_assistant.infrastructure.db.repositories.user_repository import (
    SQLAlchemyUserRepository,
)
from src.coaching_assistant.models.coaching_session import (
    CoachingSession as CoachingSessionModel,
)
from src.coaching_assistant.models.coaching_session import (
    SessionSource as DatabaseSessionSource,
)
from src.coaching_assistant.models.user import User as UserModel
from src.coaching_assistant.models.user import UserPlan as DatabaseUserPlan


@pytest.fixture
def coaching_session_repository(db_session):
    """Create CoachingSessionRepository for testing."""
    return SQLAlchemyCoachingSessionRepository(db_session)


@pytest.fixture
def user_repository(db_session):
    """Create UserRepository for testing."""
    return SQLAlchemyUserRepository(db_session)


@pytest.fixture
def sample_domain_coaching_session():
    """Create a sample domain coaching session for testing."""
    return DomainCoachingSession(
        id=uuid4(),
        user_id=uuid4(),
        client_id=uuid4(),
        session_date=date.today(),
        source=DomainSessionSource.CLIENT,
        duration_min=60,
        fee_currency="TWD",
        fee_amount=Decimal("2000.00"),
        transcription_session_id=uuid4(),
        notes="Test session notes",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_database_coaching_session():
    """Create a sample database coaching session model for testing."""
    return CoachingSessionModel(
        id=uuid4(),
        user_id=uuid4(),
        client_id=uuid4(),
        session_date=date.today(),
        source=DatabaseSessionSource.CLIENT,
        duration_min=60,
        fee_currency="TWD",
        fee_amount=Decimal("2000.00"),
        transcription_session_id=uuid4(),
        notes="Test session notes",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_domain_user():
    """Create a sample domain user for testing."""
    return DomainUser(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        plan=DomainUserPlan.STUDENT,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_database_user():
    """Create a sample database user model for testing."""
    return UserModel(
        id=uuid4(),
        email="test@example.com",
        name="Test User",
        plan=DatabaseUserPlan.STUDENT,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


class TestCoachingSessionRepositoryConversions:
    """Test CoachingSessionRepository conversion methods."""

    def test_to_domain_conversion(
        self, coaching_session_repository, sample_database_coaching_session
    ):
        """Test _to_domain() method correctly converts database model to domain model."""
        domain_session = coaching_session_repository._to_domain(
            sample_database_coaching_session
        )

        # Verify basic fields
        assert isinstance(domain_session, DomainCoachingSession)
        assert domain_session.id == sample_database_coaching_session.id
        assert domain_session.user_id == sample_database_coaching_session.user_id
        assert domain_session.client_id == sample_database_coaching_session.client_id
        assert (
            domain_session.session_date == sample_database_coaching_session.session_date
        )
        assert (
            domain_session.duration_min == sample_database_coaching_session.duration_min
        )
        assert (
            domain_session.fee_currency == sample_database_coaching_session.fee_currency
        )
        assert domain_session.fee_amount == sample_database_coaching_session.fee_amount
        assert (
            domain_session.transcription_session_id
            == sample_database_coaching_session.transcription_session_id
        )
        assert domain_session.notes == sample_database_coaching_session.notes
        assert domain_session.created_at == sample_database_coaching_session.created_at
        assert domain_session.updated_at == sample_database_coaching_session.updated_at

        # Verify enum conversion
        assert isinstance(domain_session.source, DomainSessionSource)
        assert (
            domain_session.source.value == sample_database_coaching_session.source.value
        )

    def test_to_domain_with_all_enum_values(self, coaching_session_repository):
        """Test _to_domain() with all possible SessionSource enum values."""
        enum_test_cases = [
            (DatabaseSessionSource.CLIENT, DomainSessionSource.CLIENT),
            (DatabaseSessionSource.FRIEND, DomainSessionSource.FRIEND),
            (DatabaseSessionSource.CLASSMATE, DomainSessionSource.CLASSMATE),
            (
                DatabaseSessionSource.SUBORDINATE,
                DomainSessionSource.SUBORDINATE,
            ),
        ]

        for db_enum, expected_domain_enum in enum_test_cases:
            db_model = CoachingSessionModel(
                id=uuid4(),
                user_id=uuid4(),
                client_id=uuid4(),
                session_date=date.today(),
                source=db_enum,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=Decimal("1000.00"),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            domain_model = coaching_session_repository._to_domain(db_model)
            assert domain_model.source == expected_domain_enum

    def test_create_orm_session_conversion(
        self, coaching_session_repository, sample_domain_coaching_session
    ):
        """Test _create_orm_session() method correctly converts domain model to database model."""
        db_session = coaching_session_repository._create_orm_session(
            sample_domain_coaching_session
        )

        # Verify basic fields
        assert isinstance(db_session, CoachingSessionModel)
        assert db_session.id == sample_domain_coaching_session.id
        assert db_session.user_id == sample_domain_coaching_session.user_id
        assert db_session.client_id == sample_domain_coaching_session.client_id
        assert db_session.session_date == sample_domain_coaching_session.session_date
        assert db_session.duration_min == sample_domain_coaching_session.duration_min
        assert db_session.fee_currency == sample_domain_coaching_session.fee_currency
        assert db_session.fee_amount == sample_domain_coaching_session.fee_amount
        assert (
            db_session.transcription_session_id
            == sample_domain_coaching_session.transcription_session_id
        )
        assert db_session.notes == sample_domain_coaching_session.notes
        assert db_session.created_at == sample_domain_coaching_session.created_at
        assert db_session.updated_at == sample_domain_coaching_session.updated_at

        # Verify enum conversion
        assert isinstance(db_session.source, DatabaseSessionSource)
        assert db_session.source.value == sample_domain_coaching_session.source.value

    def test_create_orm_session_with_all_enum_values(self, coaching_session_repository):
        """Test _create_orm_session() with all possible SessionSource enum values."""
        enum_test_cases = [
            (DomainSessionSource.CLIENT, DatabaseSessionSource.CLIENT),
            (DomainSessionSource.FRIEND, DatabaseSessionSource.FRIEND),
            (DomainSessionSource.CLASSMATE, DatabaseSessionSource.CLASSMATE),
            (
                DomainSessionSource.SUBORDINATE,
                DatabaseSessionSource.SUBORDINATE,
            ),
        ]

        for domain_enum, expected_db_enum in enum_test_cases:
            domain_model = DomainCoachingSession(
                id=uuid4(),
                user_id=uuid4(),
                client_id=uuid4(),
                session_date=date.today(),
                source=domain_enum,
                duration_min=60,
                fee_currency="TWD",
                fee_amount=Decimal("1000.00"),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            db_model = coaching_session_repository._create_orm_session(domain_model)
            assert db_model.source == expected_db_enum

    def test_round_trip_conversion(
        self, coaching_session_repository, sample_domain_coaching_session
    ):
        """Test that domain → database → domain conversion preserves all data."""
        # Domain → Database
        db_session = coaching_session_repository._create_orm_session(
            sample_domain_coaching_session
        )

        # Database → Domain
        round_trip_domain = coaching_session_repository._to_domain(db_session)

        # Verify all fields are preserved
        assert round_trip_domain.id == sample_domain_coaching_session.id
        assert round_trip_domain.user_id == sample_domain_coaching_session.user_id
        assert round_trip_domain.client_id == sample_domain_coaching_session.client_id
        assert (
            round_trip_domain.session_date
            == sample_domain_coaching_session.session_date
        )
        assert round_trip_domain.source == sample_domain_coaching_session.source
        assert (
            round_trip_domain.duration_min
            == sample_domain_coaching_session.duration_min
        )
        assert (
            round_trip_domain.fee_currency
            == sample_domain_coaching_session.fee_currency
        )
        assert round_trip_domain.fee_amount == sample_domain_coaching_session.fee_amount
        assert (
            round_trip_domain.transcription_session_id
            == sample_domain_coaching_session.transcription_session_id
        )
        assert round_trip_domain.notes == sample_domain_coaching_session.notes
        assert round_trip_domain.created_at == sample_domain_coaching_session.created_at
        assert round_trip_domain.updated_at == sample_domain_coaching_session.updated_at

    def test_to_domain_with_none_input(self, coaching_session_repository):
        """Test _to_domain() with None input returns None."""
        result = coaching_session_repository._to_domain(None)
        assert result is None

    def test_optional_field_handling(self, coaching_session_repository):
        """Test handling of optional fields (None values)."""
        db_model = CoachingSessionModel(
            id=uuid4(),
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=DatabaseSessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=Decimal("1000.00"),
            transcription_session_id=None,  # Optional field
            notes=None,  # Optional field
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        domain_model = coaching_session_repository._to_domain(db_model)
        assert domain_model.transcription_session_id is None
        assert domain_model.notes is None


class TestUserRepositoryConversions:
    """Test UserRepository conversion methods."""

    def test_to_domain_conversion(self, user_repository, sample_database_user):
        """Test _to_domain() method correctly converts database model to domain model."""
        domain_user = user_repository._to_domain(sample_database_user)

        # Verify basic fields
        assert isinstance(domain_user, DomainUser)
        assert domain_user.id == sample_database_user.id
        assert domain_user.email == sample_database_user.email
        assert domain_user.name == sample_database_user.name
        assert domain_user.created_at == sample_database_user.created_at
        assert domain_user.updated_at == sample_database_user.updated_at

        # Verify enum conversion
        assert isinstance(domain_user.plan, DomainUserPlan)
        assert domain_user.plan.value == sample_database_user.plan.value

    def test_to_domain_with_all_user_plan_values(self, user_repository):
        """Test _to_domain() with all possible UserPlan enum values."""
        enum_test_cases = [
            (DatabaseUserPlan.FREE, DomainUserPlan.FREE),
            (DatabaseUserPlan.STUDENT, DomainUserPlan.STUDENT),
            (DatabaseUserPlan.PRO, DomainUserPlan.PRO),
            (DatabaseUserPlan.ENTERPRISE, DomainUserPlan.ENTERPRISE),
        ]

        for db_enum, expected_domain_enum in enum_test_cases:
            db_model = UserModel(
                id=uuid4(),
                email="test@example.com",
                name="Test User",
                plan=db_enum,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )

            domain_model = user_repository._to_domain(db_model)
            assert domain_model.plan == expected_domain_enum

    def test_from_domain_conversion(self, user_repository, sample_domain_user):
        """Test _from_domain() method correctly converts domain model to database model."""
        db_user = user_repository._from_domain(sample_domain_user)

        # Verify basic fields
        assert isinstance(db_user, UserModel)
        assert db_user.id == sample_domain_user.id
        assert db_user.email == sample_domain_user.email
        assert db_user.name == sample_domain_user.name
        assert db_user.created_at == sample_domain_user.created_at
        assert db_user.updated_at == sample_domain_user.updated_at

        # Verify enum conversion
        assert isinstance(db_user.plan, DatabaseUserPlan)
        assert db_user.plan.value == sample_domain_user.plan.value

    def test_round_trip_user_conversion(self, user_repository, sample_domain_user):
        """Test that user domain → database → domain conversion preserves all data."""
        # Domain → Database
        db_user = user_repository._from_domain(sample_domain_user)

        # Database → Domain
        round_trip_domain = user_repository._to_domain(db_user)

        # Verify all fields are preserved
        assert round_trip_domain.id == sample_domain_user.id
        assert round_trip_domain.email == sample_domain_user.email
        assert round_trip_domain.name == sample_domain_user.name
        assert round_trip_domain.plan == sample_domain_user.plan
        assert round_trip_domain.created_at == sample_domain_user.created_at
        assert round_trip_domain.updated_at == sample_domain_user.updated_at


class TestConversionEdgeCases:
    """Test edge cases in repository conversions."""

    def test_datetime_timezone_handling(self, coaching_session_repository):
        """Test that datetime fields are handled correctly across timezones."""
        # This is important for UTC storage vs local time display
        utc_time = datetime.now(UTC)

        domain_model = DomainCoachingSession(
            id=uuid4(),
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=DomainSessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=Decimal("1000.00"),
            created_at=utc_time,
            updated_at=utc_time,
        )

        # Convert and verify datetime preservation
        db_model = coaching_session_repository._create_orm_session(domain_model)
        round_trip_domain = coaching_session_repository._to_domain(db_model)

        assert round_trip_domain.created_at == utc_time
        assert round_trip_domain.updated_at == utc_time

    def test_decimal_precision_handling(self, coaching_session_repository):
        """Test that Decimal fields maintain precision."""
        precise_amount = Decimal("1234.56")

        domain_model = DomainCoachingSession(
            id=uuid4(),
            user_id=uuid4(),
            client_id=uuid4(),
            session_date=date.today(),
            source=DomainSessionSource.CLIENT,
            duration_min=60,
            fee_currency="TWD",
            fee_amount=precise_amount,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )

        # Convert and verify decimal precision is preserved
        db_model = coaching_session_repository._create_orm_session(domain_model)
        round_trip_domain = coaching_session_repository._to_domain(db_model)

        assert round_trip_domain.fee_amount == precise_amount
        assert isinstance(round_trip_domain.fee_amount, Decimal)


if __name__ == "__main__":
    pytest.main([__file__])
