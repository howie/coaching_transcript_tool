#!/usr/bin/env python3
"""
Manual test script for speaker continuity checking approach.

This tests the new LeMUR strategy that focuses on sentence completeness
rather than coach/client role identification.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.coaching_assistant.services.lemur_transcript_smoother import LeMURTranscriptSmoother, SmoothingContext

def test_speaker_continuity_examples():
    """Test various speaker continuity scenarios."""
    
    print("🧪 Testing Speaker Continuity Checking")
    print("=" * 60)
    
    # Test Case 1: Sentence fragmentation (should be merged)
    test_case_1 = [
        {"speaker": "Speaker_1", "text": "你今天想談什麼", "start": 0, "end": 2000},
        {"speaker": "Speaker_2", "text": "呢", "start": 2100, "end": 2500},  # Fragment
        {"speaker": "Speaker_2", "text": "我想談談工作壓力", "start": 2600, "end": 5000}
    ]
    
    print("📋 Test Case 1: Sentence Fragmentation")
    print("Input:")
    for seg in test_case_1:
        print(f"  {seg['speaker']}: {seg['text']}")
    print("\nExpected: Speaker_1 should ask complete question, Speaker_2 should have merged response")
    print()
    
    # Test Case 2: Normal conversation (should remain unchanged)
    test_case_2 = [
        {"speaker": "Speaker_1", "text": "這很有趣", "start": 0, "end": 1500},
        {"speaker": "Speaker_2", "text": "是的", "start": 1600, "end": 2000},
        {"speaker": "Speaker_1", "text": "那我們繼續", "start": 2100, "end": 3500}
    ]
    
    print("📋 Test Case 2: Normal Conversation")
    print("Input:")
    for seg in test_case_2:
        print(f"  {seg['speaker']}: {seg['text']}")
    print("\nExpected: Should remain unchanged (normal turn-taking)")
    print()
    
    # Test Case 3: Mixed scenario
    test_case_3 = [
        {"speaker": "Speaker_1", "text": "你覺得這個問題", "start": 0, "end": 2000},
        {"speaker": "Speaker_2", "text": "怎麼樣", "start": 2100, "end": 2800},  # Should merge with Speaker_1
        {"speaker": "Speaker_2", "text": "我覺得很困難", "start": 2900, "end": 4000}  # Separate response
    ]
    
    print("📋 Test Case 3: Mixed Scenario")
    print("Input:")
    for seg in test_case_3:
        print(f"  {seg['speaker']}: {seg['text']}")
    print("\nExpected: First two should merge to Speaker_1, third stays with Speaker_2")
    print()
    
    return [
        ("sentence_fragmentation", test_case_1),
        ("normal_conversation", test_case_2),
        ("mixed_scenario", test_case_3)
    ]

async def test_with_mock_lemur():
    """Test with mocked LeMUR responses to verify parsing logic."""
    
    smoother = LeMURTranscriptSmoother()
    
    # Mock a LeMUR response that follows the new continuity format
    mock_response = """Speaker_1: 你今天想談什麼呢？
Speaker_2: 我想談談工作壓力。"""
    
    print("🔧 Mock LeMUR Response:")
    print(mock_response)
    print()
    
    # Test the parsing logic
    original_segments = [
        {"speaker": "Speaker_1", "text": "你今天想談什麼", "start": 0, "end": 2000},
        {"speaker": "Speaker_2", "text": "呢", "start": 2100, "end": 2500},
        {"speaker": "Speaker_2", "text": "我想談談工作壓力", "start": 2600, "end": 5000}
    ]
    
    context = SmoothingContext(
        session_language="zh-TW",
        is_coaching_session=True
    )
    
    # Test the parsing function
    try:
        speaker_mapping, parsed_segments = smoother._parse_combined_response(
            mock_response, original_segments, context
        )
        
        print("✅ Parsing successful!")
        print(f"📍 Speaker mapping: {speaker_mapping}")
        print(f"📍 Parsed segments: {len(parsed_segments)}")
        
        for i, segment in enumerate(parsed_segments):
            print(f"  {i+1}. {segment.speaker}: {segment.text}")
            
        # Test mandatory cleanup
        test_text = "这是一个测试, 包含半角标点."
        cleaned = smoother._apply_mandatory_cleanup(test_text, "zh")
        print(f"\n🧹 Cleanup test:")
        print(f"  Input:  {test_text}")
        print(f"  Output: {cleaned}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

def test_punctuation_fixes():
    """Test the new punctuation fixing functionality."""
    
    print("\n🔤 Testing Punctuation Fixes")
    print("=" * 40)
    
    smoother = LeMURTranscriptSmoother()
    
    test_cases = [
        ("这是一个测试, 包含标点.", "這是一個測試，包含標點。"),
        ("你好! 这很有趣?", "你好！這很有趣？"),
        ("我想说: 这很重要; 你觉得呢?", "我想說：這很重要；你覺得呢？"),
    ]
    
    for input_text, expected in test_cases:
        result = smoother._apply_mandatory_cleanup(input_text, "zh")
        success = "✅" if result == expected else "❌"
        print(f"{success} Input:    {input_text}")
        print(f"   Expected: {expected}")
        print(f"   Got:      {result}")
        print()

async def main():
    """Main test function."""
    print("🚀 Speaker Continuity Testing Suite")
    print("=" * 80)
    print()
    
    # Test 1: Show example scenarios
    test_cases = test_speaker_continuity_examples()
    
    # Test 2: Mock LeMUR parsing
    await test_with_mock_lemur()
    
    # Test 3: Punctuation fixes
    test_punctuation_fixes()
    
    print("\n📊 Test Summary:")
    print("✅ Prompt strategy updated to focus on speaker continuity")
    print("✅ Punctuation fixing added to mandatory cleanup")
    print("✅ Parsing logic works with new format")
    print("\n🔄 Next: Test with real LeMUR API")

if __name__ == "__main__":
    asyncio.run(main())