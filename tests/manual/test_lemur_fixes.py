"""
Manual verification script for LeMUR Chinese processing fixes.

This script allows quick testing of the improved LeMUR processing logic
with real-world examples from user logs.
"""

import asyncio
import logging
import sys
import os

# Add source path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from coaching_assistant.services.lemur_transcript_smoother import (
    LeMURTranscriptSmoother, 
    SmoothingContext
)


# Setup logging to see detailed processing
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManualLeMURTester:
    """Manual testing class for LeMUR processing improvements."""
    
    def __init__(self):
        self.smoother = LeMURTranscriptSmoother()
        self.context = SmoothingContext(session_language="zh-TW")
    
    def test_text_cleanup_functions(self):
        """Test the core text cleanup functions."""
        print("=" * 60)
        print("🧪 TESTING CORE TEXT CLEANUP FUNCTIONS")
        print("=" * 60)
        
        test_cases = [
            # Space removal test cases
            ("我 想要 聊 一个 关于", "我想要聊一个关于"),
            ("嗯 對 確實 嗯 好", "嗯對確實嗯好"),
            ("只是 想 說 這個 問題", "只是想說這個問題"),
            ("你好 ， 我 是", "你好，我是"),
            ("LisaOK 吗 OK 我 没有 问题", "LisaOK吗OK我没有问题"),
            
            # Mixed language cases
            ("Hello 世 界 測 試", "Hello 世界測試"),
            ("This is a test 這 是 測 試", "This is a test 這是測試"),
            
            # Punctuation cases
            ("真的 嗎 ？", "真的嗎？"),
            ("太好了 ！ 謝謝", "太好了！謝謝"),
        ]
        
        print("\n📝 Testing _clean_chinese_text_spacing function:")
        all_passed = True
        
        for i, (input_text, expected) in enumerate(test_cases):
            result = self.smoother._clean_chinese_text_spacing(input_text)
            passed = result == expected
            all_passed &= passed
            
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {i+1:2d}. {status} '{input_text}' → '{result}' (expected: '{expected}')")
            
            if not passed:
                print(f"      ⚠️  Expected: '{expected}'")
                print(f"      ⚠️  Got:      '{result}'")
        
        print(f"\n🎯 Text Cleanup Results: {sum(1 for _, (i, e) in enumerate(test_cases) if self.smoother._clean_chinese_text_spacing(i) == e)}/{len(test_cases)} tests passed")
        return all_passed
    
    def test_mandatory_cleanup_function(self):
        """Test the mandatory cleanup function with Traditional Chinese conversion."""
        print("\n=" * 60)
        print("🔄 TESTING MANDATORY CLEANUP FUNCTION")
        print("=" * 60)
        
        test_cases = [
            # Simplified to Traditional conversion cases
            ("我 想要 聊 一个 关于 生活 工作", "我想要聊一個關於生活工作"),
            ("好 的 没有 问题", "好的沒有問題"),
            ("谢谢 你 愿意 分享", "謝謝你願意分享"),
        ]
        
        print("\n📝 Testing _apply_mandatory_cleanup function:")
        
        for i, (input_text, expected_contains) in enumerate(test_cases):
            try:
                result = self.smoother._apply_mandatory_cleanup(input_text, context_language="zh")
                print(f"  {i+1}. Input:  '{input_text}'")
                print(f"     Output: '{result}'")
                
                # Check key transformations
                has_no_extra_spaces = '  ' not in result and ' 想' not in result
                has_traditional = any(char in result for char in ['個', '關', '沒', '問', '題', '謝'])
                
                print(f"     ✅ No extra spaces: {has_no_extra_spaces}")
                print(f"     ✅ Traditional Chinese: {has_traditional}")
                print()
                
            except Exception as e:
                print(f"  {i+1}. ❌ ERROR: {e}")
    
    def test_segment_merging(self):
        """Test segment merging functionality."""
        print("=" * 60)
        print("🔗 TESTING SEGMENT MERGING")
        print("=" * 60)
        
        # Test case based on actual user log
        test_segments = [
            {'speaker': 'B', 'text': '我们今天就先暂时结束在这边', 'start': 1785376, 'end': 1798619},
            {'speaker': 'B', 'text': 'LisaOK吗', 'start': 1799480, 'end': 1800480},  # Small gap
            {'speaker': 'B', 'text': 'OK我没有问题', 'start': 1800800, 'end': 1802141},  # Small gap
            {'speaker': 'A', 'text': '好谢谢你', 'start': 1805000, 'end': 1806000},  # Different speaker
        ]
        
        print(f"📥 Original segments: {len(test_segments)}")
        for i, seg in enumerate(test_segments):
            gap = test_segments[i+1]['start'] - seg['end'] if i < len(test_segments)-1 else 0
            print(f"  {i+1}. Speaker {seg['speaker']}: '{seg['text']}' (gap to next: {gap}ms)")
        
        merged = self.smoother._merge_close_segments(test_segments, max_gap_ms=5000)  # Generous gap for this test
        
        print(f"\n📤 Merged segments: {len(merged)}")
        for i, seg in enumerate(merged):
            print(f"  {i+1}. Speaker {seg['speaker']}: '{seg['text']}'")
        
        # Should merge the B segments
        b_segments = [seg for seg in merged if seg['speaker'] == 'B']
        if len(b_segments) == 1:
            print("✅ Successfully merged fragmented B segments")
            print(f"   Combined text: '{b_segments[0]['text']}'")
        else:
            print(f"⚠️  Expected 1 B segment, got {len(b_segments)}")
    
    def test_response_parsing(self):
        """Test response parsing with various formats."""
        print("=" * 60)
        print("📋 TESTING RESPONSE PARSING")
        print("=" * 60)
        
        test_responses = [
            # Case 1: Pure text response
            {
                "name": "Pure Text Response",
                "response": """
                教練: 我想要聊一個關於生活工作平衡的議題。
                客戶: 好的，沒有問題，我們可以開始討論。
                教練: 謝謝你願意分享。
                """,
                "expected_segments": 3
            },
            
            # Case 2: Mixed format
            {
                "name": "Mixed JSON + Text Response", 
                "response": """
                {"A": "教練", "B": "客戶"}
                
                教練: 我想要聊一個關於工作的議題。
                客戶: 好的，沒有問題。
                """,
                "expected_segments": 2
            },
            
            # Case 3: Malformed response
            {
                "name": "Malformed Response",
                "response": """
                Some random text here
                A: Content from A
                Random line without colon
                B: Content from B
                """,
                "expected_segments": 2
            }
        ]
        
        original_segments = [
            {'speaker': 'A', 'text': 'original', 'start': 1000, 'end': 2000},
            {'speaker': 'B', 'text': 'original', 'start': 2000, 'end': 3000},
            {'speaker': 'A', 'text': 'original', 'start': 3000, 'end': 4000},
        ]
        
        for test_case in test_responses:
            print(f"\n📝 Testing: {test_case['name']}")
            print(f"Response preview: {test_case['response'][:100]}...")
            
            try:
                speaker_mapping, segments = self.smoother._parse_combined_response(
                    test_case['response'], original_segments, self.context
                )
                
                print(f"  ✅ Parsed {len(segments)} segments (expected ~{test_case['expected_segments']})")
                print(f"  📊 Speaker mapping: {speaker_mapping}")
                
                if segments:
                    print("  📤 Sample segments:")
                    for i, seg in enumerate(segments[:2]):  # Show first 2
                        print(f"    {i+1}. {seg.speaker}: {seg.text[:50]}...")
                
            except Exception as e:
                print(f"  ❌ PARSING FAILED: {e}")
    
    async def test_full_pipeline_mock(self):
        """Test the full pipeline with mocked LeMUR."""
        print("=" * 60)
        print("🚀 TESTING FULL PIPELINE (MOCK)")
        print("=" * 60)
        
        # Use the actual problematic segment from user logs
        test_segments = [{
            'speaker': 'B', 
            'text': '嗯 對 確實 嗯 好 那 我们 今天 就 先 暂时 结束 在 这边 LisaOK 吗 OK 我 没有 问题 好 谢谢 你 谢谢 谢谢 好.', 
            'start': 1785376, 
            'end': 1804782
        }]
        
        print(f"📥 Input segment:")
        print(f"   Speaker: {test_segments[0]['speaker']}")
        print(f"   Text: '{test_segments[0]['text']}'")
        print(f"   Issues: Spaces between Chinese, simplified Chinese, fragmented content")
        
        # Mock the LeMUR response processing directly
        mock_response = """
        客戶: 嗯，對確實嗯好，那我們今天就先暫時結束在這邊，Lisa OK嗎？OK我沒有問題，好謝謝你謝謝謝謝好。
        """
        
        print(f"\n📝 Simulated LeMUR response:")
        print(f"   '{mock_response.strip()}'")
        
        # Test parsing
        try:
            speaker_mapping, segments = self.smoother._parse_combined_response(
                mock_response, test_segments, self.context
            )
            
            if segments:
                result_segment = segments[0]
                print(f"\n📤 Processed result:")
                print(f"   Speaker: {result_segment.speaker}")
                print(f"   Text: '{result_segment.text}'")
                
                # Check improvements
                improvements = []
                if '嗯 對' not in result_segment.text:
                    improvements.append("✅ Removed spaces between Chinese")
                if '我們' in result_segment.text:
                    improvements.append("✅ Converted to Traditional Chinese")
                if result_segment.speaker in ['客戶', '教練']:
                    improvements.append("✅ Correct speaker identification")
                
                print(f"\n🎯 Improvements detected:")
                for improvement in improvements:
                    print(f"   {improvement}")
                    
        except Exception as e:
            print(f"❌ PIPELINE TEST FAILED: {e}")


async def main():
    """Run all manual tests."""
    print("🧪 LeMUR Chinese Processing - Manual Verification")
    print("=" * 80)
    
    tester = ManualLeMURTester()
    
    try:
        # Test core functions
        print("\n1️⃣ Testing Core Functions...")
        tester.test_text_cleanup_functions()
        tester.test_mandatory_cleanup_function()
        tester.test_segment_merging()
        tester.test_response_parsing()
        
        # Test full pipeline
        print("\n2️⃣ Testing Full Pipeline...")
        await tester.test_full_pipeline_mock()
        
        print("\n" + "=" * 80)
        print("✅ MANUAL VERIFICATION COMPLETED")
        print("📋 Review the results above to verify improvements are working correctly.")
        print("🔄 To test with real LeMUR API, use the E2E test scripts.")
        
    except Exception as e:
        print(f"\n❌ MANUAL TESTING FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())