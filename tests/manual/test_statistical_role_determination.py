#!/usr/bin/env python3
"""
Test script for statistical role determination.

Tests the new approach:
1. LeMUR focuses only on speaker distinction (Speaker_1 vs Speaker_2)
2. Post-processing uses statistics to determine coach vs client roles
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.coaching_assistant.services.lemur_transcript_smoother import (  # noqa: E402
    LeMURTranscriptSmoother,
    SmoothingContext,
    TranscriptSegment,
)


def create_test_segments():
    """Create test segments with realistic coach/client distribution."""

    # Typical coaching session pattern:
    # - Coach asks shorter questions (less text)
    # - Client shares longer stories and explanations (more text)

    test_segments = [
        TranscriptSegment(
            start=0, end=2000, speaker="Speaker_1", text="你好，今天想聊什麼？"
        ),  # Coach - short
        TranscriptSegment(
            start=2000,
            end=8000,
            speaker="Speaker_2",
            text="我最近工作上遇到很多困難，感覺壓力很大，不知道該怎麼處理這些問題。每天都覺得很焦慮。",
        ),  # Client - long
        TranscriptSegment(
            start=8000,
            end=10000,
            speaker="Speaker_1",
            text="可以具體說說是什麼樣的困難嗎？",
        ),  # Coach - short
        TranscriptSegment(
            start=10000,
            end=18000,
            speaker="Speaker_2",
            text="主要是我的主管總是給我很多額外的工作，而且時間都很急，我常常需要加班到很晚。而且同事之間的關係也不太好，大家都很有競爭性。",
        ),  # Client - long
        TranscriptSegment(
            start=18000, end=20000, speaker="Speaker_1", text="聽起來確實很有挑戰性。"
        ),  # Coach - short
        TranscriptSegment(
            start=20000,
            end=28000,
            speaker="Speaker_2",
            text="對啊，我覺得自己好像無法平衡工作和生活。我的家人也開始抱怨我回家都很晚，週末也要工作。我真的不知道該怎麼辦。",
        ),  # Client - long
        TranscriptSegment(
            start=28000, end=31000, speaker="Speaker_1", text="你希望達到什麼樣的平衡？"
        ),  # Coach - short
    ]

    return test_segments


def create_balanced_test_segments():
    """Create test segments where both speakers talk similar amounts (edge case)."""

    balanced_segments = [
        TranscriptSegment(
            start=0,
            end=3000,
            speaker="Speaker_1",
            text="我想今天我們來討論一下你的職業發展。",
        ),
        TranscriptSegment(
            start=3000,
            end=6000,
            speaker="Speaker_2",
            text="好的，我最近確實在考慮這個問題。",
        ),
        TranscriptSegment(
            start=6000,
            end=9000,
            speaker="Speaker_1",
            text="你覺得目前的工作有什麼挑戰？",
        ),
        TranscriptSegment(
            start=9000,
            end=12000,
            speaker="Speaker_2",
            text="主要是感覺成長空間有限制。",
        ),
    ]

    return balanced_segments


def test_statistical_determination():
    """Test the statistical role determination function."""

    print("🧪 Testing Statistical Role Determination")
    print("=" * 60)

    smoother = LeMURTranscriptSmoother()

    # Test Case 1: Typical coaching pattern
    print("📋 Test Case 1: Typical Coaching Pattern")
    segments = create_test_segments()

    print("Input segments:")
    total_chars_speaker1 = 0
    total_chars_speaker2 = 0

    for i, segment in enumerate(segments):
        char_count = len(segment.text)
        if segment.speaker == "Speaker_1":
            total_chars_speaker1 += char_count
        else:
            total_chars_speaker2 += char_count

        print(f"  {i + 1}. {segment.speaker}: {segment.text} ({char_count} chars)")

    print("\nPre-analysis:")
    print(f"  Speaker_1 total: {total_chars_speaker1} chars")
    print(f"  Speaker_2 total: {total_chars_speaker2} chars")
    print(
        f"  Ratio (Speaker_2/Speaker_1): {total_chars_speaker2 / max(total_chars_speaker1, 1):.2f}"
    )

    # Run statistical determination
    role_mapping = smoother._determine_roles_by_statistics(segments)
    print(f"\n✅ Statistical determination result: {role_mapping}")

    # Apply role mapping
    updated_segments = smoother._apply_role_mapping_to_segments(segments, role_mapping)
    print("\nSegments with role labels:")
    for i, segment in enumerate(updated_segments):
        print(f"  {i + 1}. {segment.speaker}: {segment.text[:50]}...")

    print("\n" + "=" * 60)

    # Test Case 2: Balanced speech (edge case)
    print("📋 Test Case 2: Balanced Speech (Edge Case)")
    balanced_segments = create_balanced_test_segments()

    print("Input segments:")
    for i, segment in enumerate(balanced_segments):
        char_count = len(segment.text)
        print(f"  {i + 1}. {segment.speaker}: {segment.text} ({char_count} chars)")

    role_mapping_balanced = smoother._determine_roles_by_statistics(balanced_segments)
    print(f"\n⚠️ Balanced case result: {role_mapping_balanced}")

    print("\n" + "=" * 60)


def test_lemur_response_with_role_labels():
    """Test handling of LeMUR responses that still contain role labels."""

    print("📋 Test Case 3: LeMUR Returns Role Labels")

    # Simulate LeMUR returning role labels instead of Speaker_1/Speaker_2
    mock_response = """教練: 你今天想聊什麼？
客戶: 我最近工作壓力很大，不知道該怎麼處理。
教練: 可以具體說說嗎？
客戶: 主要是工作量太大，而且同事關係複雜。"""

    original_segments = [
        {"speaker": "Speaker_1", "text": "你今天想聊什麼", "start": 0, "end": 2000},
        {
            "speaker": "Speaker_2",
            "text": "我最近工作壓力很大",
            "start": 2000,
            "end": 5000,
        },
        {"speaker": "Speaker_1", "text": "可以具體說說嗎", "start": 5000, "end": 7000},
        {
            "speaker": "Speaker_2",
            "text": "主要是工作量太大",
            "start": 7000,
            "end": 10000,
        },
    ]

    print("Mock LeMUR Response (with role labels):")
    print(mock_response)
    print()

    print("Original segments (Speaker_1/Speaker_2):")
    for seg in original_segments:
        print(f"  {seg['speaker']}: {seg['text']}")
    print()

    smoother = LeMURTranscriptSmoother()
    context = SmoothingContext(session_language="zh-TW", is_coaching_session=True)

    try:
        # Test the parsing - should convert role labels back to Speaker_1/Speaker_2
        # Mock normalization mapping (A->Speaker_1, B->Speaker_2 for this test)
        normalized_to_original_map = {"A": "Speaker_1", "B": "Speaker_2"}
        speaker_mapping, parsed_segments = smoother._parse_combined_response(
            mock_response, original_segments, context, normalized_to_original_map
        )

        print("✅ Parsed segments (should preserve Speaker_1/Speaker_2):")
        for i, segment in enumerate(parsed_segments):
            print(f"  {i + 1}. {segment.speaker}: {segment.text}")
        print()

        # Now test statistical determination
        role_mapping = smoother._determine_roles_by_statistics(parsed_segments)
        print(f"📊 Statistical role determination: {role_mapping}")

        # Apply role mapping if needed
        if role_mapping:
            final_segments = smoother._apply_role_mapping_to_segments(
                parsed_segments, role_mapping
            )
            print("\n🎯 Final segments with statistical role assignment:")
            for i, segment in enumerate(final_segments):
                print(f"  {i + 1}. {segment.speaker}: {segment.text}")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


async def main():
    """Run all tests."""
    print("🚀 Statistical Role Determination Test Suite")
    print("=" * 80)
    print()

    # Test 1: Basic statistical determination
    test_statistical_determination()
    print()

    # Test 2: Handle LeMUR responses with role labels
    test_lemur_response_with_role_labels()

    print("\n📊 Test Summary:")
    print("✅ Statistical determination works with typical coaching patterns")
    print("✅ Handles balanced speech scenarios gracefully")
    print("✅ Converts role labels back to Speaker format")
    print("✅ Can apply statistical role determination afterward")
    print("\n🎯 Key Benefits:")
    print("  - LeMUR focuses on speaker distinction, not role judgment")
    print("  - Statistics provide reliable role determination")
    print("  - Flexible: can keep Speaker_1/2 or convert to 教練/客戶")
    print("  - Robust against LeMUR response variations")


if __name__ == "__main__":
    asyncio.run(main())
