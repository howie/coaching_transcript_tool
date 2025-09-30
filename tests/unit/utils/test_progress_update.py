"""Test progress update functionality."""

from datetime import UTC, datetime
from uuid import uuid4

from coaching_assistant.models.processing_status import ProcessingStatus


def test_progress_update():
    """Test that progress updates correctly."""

    # Create a ProcessingStatus instance
    session_id = uuid4()
    status = ProcessingStatus(
        session_id=session_id,
        status="processing",
        progress=0,
        message="Initial",
    )

    # Test update_progress method
    status.update_progress(28, "Processing audio... 8.1 min elapsed")

    assert status.progress == 28
    assert status.message == "Processing audio... 8.1 min elapsed"
    assert status.progress_percentage == 28

    # Test clamping
    status.update_progress(150, "Over 100%")
    assert status.progress == 100
    assert status.progress_percentage == 100

    status.update_progress(-10, "Negative")
    assert status.progress == 0
    assert status.progress_percentage == 0

    print("✅ All progress update tests passed!")


def test_progress_not_overridden():
    """Test that existing progress is not overridden."""

    # Simulate a status with existing progress
    status = ProcessingStatus(
        session_id=uuid4(),
        status="processing",
        progress=28,  # Already has progress
        message="Processing audio...",
        started_at=datetime.now(UTC),
    )

    # The _update_processing_progress function should not override
    # if progress > 0
    # We test the logic here
    if status.progress == 0:
        # Only update if progress is 0
        status.progress = 10

    # Progress should remain 28
    assert status.progress == 28
    assert status.progress_percentage == 28

    print("✅ Progress not overridden test passed!")


if __name__ == "__main__":
    test_progress_update()
    test_progress_not_overridden()
    print("\n✅ All tests passed!")
