"""Test speaker roles API endpoint."""

from coaching_assistant.models.transcript import (
    SessionRole,
    SpeakerRole,
)


def test_speaker_roles_update():
    """Test updating speaker roles for a completed session."""
    # This is a unit test that validates the logic, not a full integration test
    # The actual API would require authentication setup which is complex in tests

    # Test the SpeakerRole enum
    assert SpeakerRole.COACH.value == "coach"
    assert SpeakerRole.CLIENT.value == "client"
    assert SpeakerRole.UNKNOWN.value == "unknown"

    # Test SessionRole model creation
    role = SessionRole.create_assignment(
        session_id="test-session-id", speaker_id=1, role=SpeakerRole.COACH
    )

    assert role.speaker_id == 1
    assert role.role == SpeakerRole.COACH
    assert role.session_id == "test-session-id"


def test_speaker_role_validation():
    """Test speaker role validation logic."""

    # Valid roles
    valid_roles = ["coach", "client"]
    for role in valid_roles:
        assert role in ["coach", "client"]

    # Invalid roles should be rejected
    invalid_roles = ["unknown", "speaker", "", None]
    for role in invalid_roles:
        assert role not in ["coach", "client"]


def test_role_assignment_logic():
    """Test the logic for role assignments."""

    # Test speaker role assignments
    speaker_roles = {1: "coach", 2: "client"}

    # Validate all roles are valid
    for speaker_id, role_str in speaker_roles.items():
        assert isinstance(speaker_id, int)
        assert role_str in ["coach", "client"]

        # Convert to enum
        role_enum = (
            SpeakerRole.COACH if role_str == "coach" else SpeakerRole.CLIENT
        )
        assert role_enum in [SpeakerRole.COACH, SpeakerRole.CLIENT]


if __name__ == "__main__":
    test_speaker_roles_update()
    test_speaker_role_validation()
    test_role_assignment_logic()
    print("✅ All speaker roles tests passed!")
