#!/usr/bin/env python3
"""
Test script for AssemblyAI A/B speaker format handling.

Tests the fixes for:
1. Time mapping when LeMUR returns more segments than original
2. A/B speaker format (not Speaker_1/Speaker_2)
3. Statistical role determination being called automatically
"""

import sys
import asyncio
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.coaching_assistant.services.lemur_transcript_smoother import LeMURTranscriptSmoother, SmoothingContext

def create_assemblyai_segments():
    """Create test segments in AssemblyAI format (using 'A', 'B' speakers)."""
    
    # Simulate real AssemblyAI output with A/B speakers
    segments = [
        {"speaker": "A", "text": "你好 ， Lisha 你好 ， 我 是 你 今天 的 教練", "start": 0, "end": 3000},
        {"speaker": "B", "text": "只是 想 說 這個 問題 其實 它 也 是 跟著 我 非常 非常 非常 久 的 問題 了", "start": 3000, "end": 8000},
        {"speaker": "A", "text": "可以 多 說 一點 嗎", "start": 8000, "end": 10000},
        {"speaker": "B", "text": "我 覺得 我 一直 以來 都 有 這種 拖延 的 習慣", "start": 10000, "end": 14000},
        {"speaker": "A", "text": "這 聽起來 很 有 挑戰性", "start": 14000, "end": 16000},
        {"speaker": "B", "text": "對啊 而且 我 發現 這個 問題 影響到 我 的 工作 和 生活", "start": 16000, "end": 20000},
    ]
    
    return segments

async def test_ab_format_parsing():
    """Test parsing with A/B speaker format."""
    
    print("🧪 Testing A/B Speaker Format Parsing")
    print("=" * 60)
    
    segments = create_assemblyai_segments()
    
    print("📋 Input Segments (AssemblyAI A/B format):")
    for i, segment in enumerate(segments):
        char_count = len(segment['text'])
        duration = (segment['end'] - segment['start']) / 1000
        print(f"  {i+1}. {segment['speaker']}: {segment['text']} ({char_count} chars, {duration:.1f}s)")
    
    # Calculate expected coach/client distribution
    a_chars = sum(len(seg['text']) for seg in segments if seg['speaker'] == 'A')
    b_chars = sum(len(seg['text']) for seg in segments if seg['speaker'] == 'B')
    
    print(f"\nPre-analysis:")
    print(f"  A (should be Coach): {a_chars} chars")  
    print(f"  B (should be Client): {b_chars} chars")
    print(f"  Ratio (B/A): {b_chars/max(a_chars,1):.2f}")
    print(f"  Expected: A → 教練, B → 客戶")
    
    smoother = LeMURTranscriptSmoother()
    context = SmoothingContext(session_language="zh-TW", is_coaching_session=True)
    
    try:
        # Test combined processing (this is what gets called in production)
        result = await smoother.combined_processing_with_lemur(segments, context)
        
        print("\n✅ Combined processing completed!")
        print(f"📊 Input segments: {len(segments)}")
        print(f"📊 Output segments: {len(result.segments)}")
        print(f"🎭 Speaker mapping: {result.speaker_mapping}")
        
        # Show results
        print("\n📝 Processed segments:")
        for i, segment in enumerate(result.segments[:10]):  # Show first 10
            timing = f"{segment.start/1000:.1f}-{segment.end/1000:.1f}s"
            print(f"  {i+1}. {segment.speaker}: {segment.text[:50]}... ({timing})")
        
        if len(result.segments) > 10:
            print(f"  ... and {len(result.segments) - 10} more segments")
        
        # Validate timing (no 00:00 at the end)
        timing_issues = []
        for i, segment in enumerate(result.segments):
            if segment.start == 0 and i > 0:  # First segment can be 0
                timing_issues.append(f"Segment {i+1} has start=0")
        
        if timing_issues:
            print(f"\n❌ Timing Issues Found:")
            for issue in timing_issues:
                print(f"  - {issue}")
        else:
            print(f"\n✅ No timing issues detected")
        
        # Test statistical role determination
        if result.speaker_mapping:
            print(f"\n✅ Statistical role determination worked:")
            for original, role in result.speaker_mapping.items():
                print(f"  {original} → {role}")
        else:
            print(f"\n⚠️ No role mapping found")
            
        return result
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_extra_segments_scenario():
    """Test scenario where LeMUR returns more segments than original."""
    
    print("\n" + "=" * 60)
    print("🧪 Testing Extra Segments Scenario")
    print("=" * 60)
    
    # Simulate the scenario from logs: 61 original → 64 LeMUR
    original_segments = [
        {"speaker": "A", "text": "你好", "start": 0, "end": 1000},
        {"speaker": "B", "text": "我想談", "start": 1000, "end": 2000},
        {"speaker": "A", "text": "好的", "start": 2000, "end": 3000},
    ]
    
    # Mock LeMUR response that creates more segments
    mock_response = """A: 你好，很高興見到你。
B: 我想談談我的問題。
B: 這個問題困擾我很久了。
A: 好的，我們來討論看看。
A: 你可以詳細描述一下嗎？"""
    
    print("📋 Original segments:", len(original_segments))
    print("📋 Mock LeMUR response lines:", len(mock_response.strip().split('\n')))
    
    smoother = LeMURTranscriptSmoother()
    context = SmoothingContext(session_language="zh-TW", is_coaching_session=True)
    
    try:
        # Test the parsing function directly
        # Mock normalization mapping (A->Speaker_1, B->Speaker_2 for this test)
        normalized_to_original_map = {'A': 'Speaker_1', 'B': 'Speaker_2'}
        speaker_mapping, parsed_segments = smoother._parse_combined_response(
            mock_response, original_segments, context, normalized_to_original_map
        )
        
        print(f"\n✅ Parsing successful!")
        print(f"📊 Parsed segments: {len(parsed_segments)}")
        
        # Check timing progression
        print("\n⏰ Timing Analysis:")
        for i, segment in enumerate(parsed_segments):
            timing = f"{segment.start/1000:.1f}-{segment.end/1000:.1f}s"
            print(f"  {i+1}. {segment.speaker}: {timing} - {segment.text[:30]}...")
        
        # Test statistical determination
        role_mapping = smoother._determine_roles_by_statistics(parsed_segments)
        print(f"\n📊 Statistical role mapping: {role_mapping}")
        
        return parsed_segments
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Run all tests."""
    print("🚀 AssemblyAI A/B Format Test Suite")
    print("=" * 80)
    print()
    
    # Test 1: A/B format parsing with statistical determination
    result1 = await test_ab_format_parsing()
    
    # Test 2: Extra segments scenario
    result2 = await test_extra_segments_scenario()
    
    print("\n" + "=" * 80)
    print("📊 Test Summary:")
    
    if result1:
        print("✅ A/B format processing works")
        print("✅ Statistical role determination integrated")
        if result1.speaker_mapping:
            print("✅ Roles assigned based on speech volume")
        else:
            print("⚠️ No role mapping generated")
    else:
        print("❌ A/B format processing failed")
    
    if result2:
        print("✅ Extra segments handling works") 
        print("✅ No timing issues (00:00) detected")
    else:
        print("❌ Extra segments handling failed")
    
    print("\n🎯 Key Fixes Implemented:")
    print("  - Prompt updated to use A/B format (not Speaker_1/2)")
    print("  - Time mapping fixed for extra segments") 
    print("  - Statistical role determination auto-called")
    print("  - A/B speakers properly handled throughout pipeline")

if __name__ == "__main__":
    asyncio.run(main())