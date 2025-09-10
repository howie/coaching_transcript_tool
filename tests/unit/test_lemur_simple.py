#!/usr/bin/env python3
"""
Simple test for improved LeMUR punctuation handling.
"""

import asyncio
import os
import sys
import pytest
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

# Simple test data
SIMPLE_TEST_DATA = [
    {
        "start": 1000,
        "end": 15000,
        "speaker": "A",
        "text": "好Lisha你好我是你今天的教練那我待會錄音並且會做一些筆記你OK嗎OK好那我想要了解今天會談想談些什麼",
    },
    {
        "start": 15000,
        "end": 45000,
        "speaker": "B",
        "text": "我今天想要談的一個議題呢就是最近有點困擾我的就是我今年暑假我要帶我女兒出國去念summercamp那我們原本的計劃就是只是要去溫哥華但是呢他有一個同學的媽媽一個很好朋友的媽媽就說你們都到了溫哥華了嘛那你們要不要來洛杉磯找我們因為很近",
    },
]


@pytest.mark.asyncio
async def test_simple_lemur():
    """Test improved LeMUR with simple data."""

    # Check API key
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    if not api_key:
        print("❌ Need ASSEMBLYAI_API_KEY environment variable")
        return False

    try:
        from coaching_assistant.services.lemur_transcript_smoother import (
            smooth_transcript_with_lemur,
        )

        print("🧪 Testing improved LeMUR prompts...")
        print("Input text:")
        for segment in SIMPLE_TEST_DATA:
            print(f"  {segment['speaker']}: {segment['text']}")
        print()

        # Run LeMUR
        result = await smooth_transcript_with_lemur(
            segments=SIMPLE_TEST_DATA,
            session_language="zh-TW",
            is_coaching_session=True,
        )

        print("✅ LeMUR processing completed!")
        print(f"🎭 Speaker mapping: {result.speaker_mapping}")
        print()
        print("Improved output:")
        for segment in result.segments:
            print(f"  {segment.speaker}: {segment.text}")
        print()

        # Check for improvements
        has_punctuation = any(
            "，" in seg.text or "。" in seg.text or "？" in seg.text
            for seg in result.segments
        )
        no_extra_spaces = all(
            "我 是" not in seg.text and "你 好" not in seg.text
            for seg in result.segments
        )
        has_speaker_mapping = len(result.speaker_mapping) > 0

        # Check for Traditional Chinese (look for traditional characters vs simplified)
        has_traditional = any(
            "學" in seg.text or "們" in seg.text or "會" in seg.text
            for seg in result.segments
        )
        no_simplified = all(
            "学" not in seg.text and "们" not in seg.text
            for seg in result.segments
        )

        print("Quality checks:")
        print(f"  ✓ Has punctuation: {has_punctuation}")
        print(f"  ✓ No extra spaces in Chinese: {no_extra_spaces}")
        print(f"  ✓ Speaker mapping: {has_speaker_mapping}")
        print(f"  ✓ Traditional Chinese: {has_traditional and no_simplified}")

        success = (
            has_punctuation
            and no_extra_spaces
            and has_speaker_mapping
            and (has_traditional and no_simplified)
        )
        print(f"\n{'🎉 SUCCESS' if success else '⚠️  NEEDS IMPROVEMENT'}")
        return success

    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_simple_lemur())
    sys.exit(0 if success else 1)
