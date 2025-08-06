"""Test client issue types handling."""

import pytest
from sqlalchemy.orm import Session
from coaching_assistant.models import Client, User
from coaching_assistant.core.database import get_db


@pytest.fixture
def test_user(db_session: Session):
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password="hashed_password"
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def test_client_issue_types_storage(db_session: Session, test_user: User):
    """Test that issue types are stored correctly as comma-separated string."""
    client = Client(
        coach_id=test_user.id,
        name="Test Client",
        email="client@example.com",
        issue_types="職涯發展, 人際關係, 領導力"
    )
    
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    
    assert client.issue_types == "職涯發展, 人際關係, 領導力"


def test_client_issue_types_can_be_empty(db_session: Session, test_user: User):
    """Test that issue types can be empty or None."""
    client1 = Client(
        coach_id=test_user.id,
        name="Test Client 1",
        issue_types=""
    )
    
    client2 = Client(
        coach_id=test_user.id,
        name="Test Client 2",
        issue_types=None
    )
    
    db_session.add_all([client1, client2])
    db_session.commit()
    
    assert client1.issue_types == ""
    assert client2.issue_types is None


def test_client_issue_types_update(db_session: Session, test_user: User):
    """Test updating client issue types."""
    client = Client(
        coach_id=test_user.id,
        name="Test Client",
        issue_types="職涯發展"
    )
    
    db_session.add(client)
    db_session.commit()
    
    # Update issue types
    client.issue_types = "職涯發展, 人際關係, 領導力, 時間管理"
    db_session.commit()
    db_session.refresh(client)
    
    assert client.issue_types == "職涯發展, 人際關係, 領導力, 時間管理"


def test_client_with_all_new_fields(db_session: Session, test_user: User):
    """Test client creation with all new fields including issue types."""
    client = Client(
        coach_id=test_user.id,
        name="Complete Test Client",
        email="complete@example.com",
        phone="0912345678",
        memo="Test memo",
        source="referral",
        client_type="paid",
        issue_types="職涯發展, 人際關係, 領導力, 溝通技巧, 團隊合作"
    )
    
    db_session.add(client)
    db_session.commit()
    db_session.refresh(client)
    
    assert client.name == "Complete Test Client"
    assert client.email == "complete@example.com"
    assert client.phone == "0912345678"
    assert client.memo == "Test memo"
    assert client.source == "referral"
    assert client.client_type == "paid"
    assert client.issue_types == "職涯發展, 人際關係, 領導力, 溝通技巧, 團隊合作"
    assert client.is_anonymized is False


def test_client_issue_types_preserved_after_anonymization(db_session: Session, test_user: User):
    """Test that issue types are preserved even after client anonymization."""
    client = Client(
        coach_id=test_user.id,
        name="Test Client",
        email="test@example.com",
        issue_types="職涯發展, 人際關係"
    )
    
    db_session.add(client)
    db_session.commit()
    
    # Anonymize client
    client.anonymize(1)
    db_session.commit()
    db_session.refresh(client)
    
    # Issue types should be preserved for analytical purposes
    assert client.issue_types == "職涯發展, 人際關係"
    assert client.is_anonymized is True
    assert client.name.startswith("匿名客戶")
    assert client.email is None  # PII should be removed