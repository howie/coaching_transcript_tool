"""
Unit tests for LeMUR response parsing and text processing functions.

Tests the core functions that handle LeMUR response parsing, Chinese text cleaning,
and segment merging to ensure they work correctly with various input formats.
"""

import os
import sys
from unittest.mock import patch

import pytest

from coaching_assistant.services.lemur_transcript_smoother import (
    LeMURTranscriptSmoother,
    SmoothingContext,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


class TestLeMURResponseParsing:
    """Test LeMUR response parsing with various formats."""

    def setup_method(self):
        """Setup test fixtures."""
        self.smoother = LeMURTranscriptSmoother()
        self.context = SmoothingContext(session_language="zh-TW")

        # Sample original segments for testing
        self.original_segments = [
            {
                "speaker": "A",
                "text": "我 想要 聊 一个 关于",
                "start": 1000,
                "end": 2000,
            },
            {
                "speaker": "B",
                "text": "好 的 没有 问题",
                "start": 2100,
                "end": 3000,
            },
            {"speaker": "A", "text": "谢谢 你", "start": 3100, "end": 4000},
        ]

    def test_parse_pure_text_response(self):
        """Test parsing when LeMUR returns pure text without JSON structure."""
        response = """
        教練: 我想要聊一個關於生活工作平衡的議題。
        客戶: 好的，沒有問題，我們可以開始討論。
        教練: 謝謝你願意分享。
        """

        speaker_mapping, segments = self.smoother._parse_combined_response(
            response, self.original_segments, self.context
        )

        # Should extract segments correctly
        assert len(segments) == 3
        assert segments[0].speaker == "教練"
        assert segments[1].speaker == "客戶"
        assert segments[2].speaker == "教練"

        # Text should be cleaned (no extra spaces)
        assert "我想要聊一個關於生活工作平衡的議題" in segments[0].text
        assert "好的，沒有問題，我們可以開始討論" in segments[1].text

    def test_parse_mixed_format_response(self):
        """Test parsing when LeMUR returns mixed format (some JSON, some text)."""
        response = """
        {"speaker_mapping": {"A": "教練", "B": "客戶"}}

        教練: 我想要聊一個關於工作的議題。
        客戶: 好的，沒有問題。
        """

        speaker_mapping, segments = self.smoother._parse_combined_response(
            response, self.original_segments, self.context
        )

        # Should extract speaker mapping
        assert speaker_mapping.get("A") == "教練"
        assert speaker_mapping.get("B") == "客戶"

        # Should extract segments
        assert len(segments) >= 2
        assert segments[0].speaker == "教練"
        assert segments[1].speaker == "客戶"

    def test_parse_malformed_response(self):
        """Test handling of malformed or unexpected response format."""
        response = """
        This is some random text without proper format
        A: Some content here
        Random line without colon
        B: Another piece of content
        """

        # Should not crash and should extract what it can
        speaker_mapping, segments = self.smoother._parse_combined_response(
            response, self.original_segments, self.context
        )

        # Should extract the lines with colons
        assert len(segments) >= 2
        assert any(s.speaker == "A" for s in segments)
        assert any(s.speaker == "B" for s in segments)


class TestChineseTextCleaning:
    """Test Chinese text cleaning functions."""

    def setup_method(self):
        """Setup test fixtures."""
        self.smoother = LeMURTranscriptSmoother()

    def test_remove_spaces_between_chinese_characters(self):
        """Test removal of spaces between Chinese characters."""
        test_cases = [
            ("我 想要 聊 一个 关于", "我想要聊一个关于"),
            ("只是 想 說 這個 問題", "只是想說這個問題"),
            ("你 好 ， 我 是", "你好，我是"),
            ("Hello 世 界 測 試", "Hello 世界測試"),  # Mixed language
        ]

        for input_text, expected in test_cases:
            result = self.smoother._clean_chinese_text_spacing(input_text)
            assert result == expected, (
                f"Input: '{input_text}', Expected: '{expected}', Got: '{result}'"
            )

    def test_handle_punctuation_spacing(self):
        """Test handling of spaces around Chinese punctuation."""
        test_cases = [
            ("你好 ， 我是 。", "你好，我是。"),
            ("真的 嗎 ？", "真的嗎？"),
            ("太好了 ！ 謝謝", "太好了！謝謝"),
            ("這樣 ： 很好", "這樣：很好"),
        ]

        for input_text, expected in test_cases:
            result = self.smoother._clean_chinese_text_spacing(input_text)
            assert result == expected, (
                f"Input: '{input_text}', Expected: '{expected}', Got: '{result}'"
            )

    def test_preserve_english_spaces(self):
        """Test that spaces between English words are preserved."""
        test_cases = [
            ("Hello world 測試", "Hello world 測試"),
            ("This is a test 這是測試", "This is a test 這是測試"),
        ]

        for input_text, expected in test_cases:
            result = self.smoother._clean_chinese_text_spacing(input_text)
            assert result == expected

    @patch("coaching_assistant.utils.chinese_converter.convert_to_traditional")
    def test_traditional_chinese_conversion_called(self, mock_convert):
        """Test that Traditional Chinese conversion is attempted."""
        mock_convert.return_value = "測試繁體字"

        # Test the function is called during mandatory cleanup
        result = self.smoother._apply_mandatory_cleanup(
            "测试繁体字", context_language="zh"
        )

        # Should have called the conversion function
        mock_convert.assert_called()
        assert (
            "測試繁體字" in result or result != "测试繁体字"
        )  # Some conversion happened


class TestSegmentMerging:
    """Test segment merging based on time intervals."""

    def setup_method(self):
        """Setup test fixtures."""
        self.smoother = LeMURTranscriptSmoother()

    def test_merge_close_segments_same_speaker(self):
        """Test merging of segments from same speaker with small time gap."""
        segments = [
            {
                "speaker": "A",
                "text": "我们今天就先暂时结束在这边",
                "start": 1000,
                "end": 2000,
            },
            {
                "speaker": "A",
                "text": "LisaOK吗",
                "start": 2100,
                "end": 2500,
            },  # 100ms gap
            {
                "speaker": "B",
                "text": "OK我没有问题",
                "start": 2600,
                "end": 3000,
            },
        ]

        # Need to implement this function
        merged = self.smoother._merge_close_segments(segments, max_gap_ms=500)

        # Should merge first two segments (same speaker, small gap)
        assert len(merged) == 2
        assert merged[0]["speaker"] == "A"
        assert "我们今天就先暂时结束在这边LisaOK吗" in merged[0]["text"]
        assert merged[0]["end"] == 2500  # End time updated
        assert merged[1]["speaker"] == "B"

    def test_dont_merge_different_speakers(self):
        """Test that segments from different speakers are not merged."""
        segments = [
            {"speaker": "A", "text": "第一段", "start": 1000, "end": 2000},
            {
                "speaker": "B",
                "text": "第二段",
                "start": 2100,
                "end": 2500,
            },  # Different speaker
        ]

        merged = self.smoother._merge_close_segments(segments, max_gap_ms=500)

        # Should not merge (different speakers)
        assert len(merged) == 2
        assert merged[0]["speaker"] == "A"
        assert merged[1]["speaker"] == "B"

    def test_dont_merge_large_time_gap(self):
        """Test that segments with large time gaps are not merged."""
        segments = [
            {"speaker": "A", "text": "第一段", "start": 1000, "end": 2000},
            {
                "speaker": "A",
                "text": "第二段",
                "start": 3000,
                "end": 4000,
            },  # 1000ms gap
        ]

        merged = self.smoother._merge_close_segments(segments, max_gap_ms=500)

        # Should not merge (gap too large)
        assert len(merged) == 2
        assert merged[0]["text"] == "第一段"
        assert merged[1]["text"] == "第二段"


class TestRealWorldCases:
    """Test with real-world examples from logs."""

    def setup_method(self):
        """Setup test fixtures."""
        self.smoother = LeMURTranscriptSmoother()
        self.context = SmoothingContext(session_language="zh-TW")

    def test_actual_log_case(self):
        """Test with the actual case from the user's log."""
        # This is the actual segment from the log
        problematic_segment = {
            "speaker": "B",
            "text": (
                "嗯 對 確實 嗯 好 那 我们 今天 就 先 暂时 结束 在 这边 LisaOK 吗 OK 我 没有 问题 好 谢谢 你 谢谢 谢谢 好."
            ),
            "start": 1785376,
            "end": 1804782,
        }

        # Test text cleaning
        cleaned_text = self.smoother._clean_chinese_text_spacing(
            problematic_segment["text"]
        )

        # Should remove spaces between Chinese characters
        # Check that some spaces were removed
        assert cleaned_text != problematic_segment["text"]  # Text was modified
        assert (
            "嗯對" in cleaned_text or "嗯 對" not in cleaned_text
        )  # Some spaces removed

        # Should not have excessive spaces
        assert "  " not in cleaned_text  # No double spaces

    def test_mixed_content_response(self):
        """Test parsing a response that mixes different types of content."""
        response = """
        教練: 好，Lisha你好，我是你今天的教練，那我待會錄音，並且會做一些筆記，你OK嗎？
        客戶: 我想要聊一個關於生活工作平衡的議題，嗯生活工作平衡的議題。
        教練: 怎麼說？
        """

        original_segments = [
            {"speaker": "A", "text": "original", "start": 1000, "end": 2000},
            {"speaker": "B", "text": "original", "start": 2000, "end": 3000},
            {"speaker": "A", "text": "original", "start": 3000, "end": 4000},
        ]

        speaker_mapping, segments = self.smoother._parse_combined_response(
            response, original_segments, self.context
        )

        # Should correctly identify 3 segments
        assert len(segments) == 3

        # Should have correct speakers
        assert segments[0].speaker == "教練"
        assert segments[1].speaker == "客戶"
        assert segments[2].speaker == "教練"

        # Should have proper timing from original segments
        assert segments[0].start == 1000
        assert segments[1].start == 2000
        assert segments[2].start == 3000


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
