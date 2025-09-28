"""
Integration tests for LeMUR Chinese text processing.

Tests the complete LeMUR processing pipeline with mocked LeMUR API calls
to ensure the improved parsing and cleanup logic works correctly.
"""

import asyncio
import os
import sys
from unittest.mock import Mock, patch

import pytest

from coaching_assistant.services.lemur_transcript_smoother import (
    LeMURTranscriptSmoother,
    SmoothingContext,
    smooth_transcript_with_lemur,
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src"))


class TestLeMURChineseProcessingIntegration:
    """Integration tests for complete LeMUR Chinese processing pipeline."""

    def setup_method(self):
        """Setup test fixtures."""
        self.context = SmoothingContext(session_language="zh-TW")

        # Real-world test data based on user logs
        self.test_segments = [
            {
                "speaker": "A",
                "text": "我 想要 聊 一个 关于 生活 工作 平衡",
                "start": 1000,
                "end": 5000,
            },
            {
                "speaker": "B",
                "text": "好 的 没有 问题 我们 可以 开始 讨论",
                "start": 5100,
                "end": 8000,
            },
            {
                "speaker": "A",
                "text": "谢谢 你 愿意 分享",
                "start": 8100,
                "end": 10000,
            },
        ]

        # Example of problematic segment from actual logs
        self.problematic_segment = {
            "speaker": "B",
            "text": (
                "嗯 對 確實 嗯 好 那 我们 今天 就 先 暂时 结束 在 这边 LisaOK 吗 OK 我 没有 问题 好 谢谢 你 谢谢 谢谢 好."
            ),
            "start": 1785376,
            "end": 1804782,
        }

    @pytest.mark.asyncio
    @patch("coaching_assistant.services.lemur_transcript_smoother.aai.Lemur.task")
    async def test_combined_processing_with_pure_text_response(self, mock_lemur_task):
        """Test combined processing when LeMUR returns pure text (no JSON structure)."""

        # Mock LeMUR response - pure text format (what often happens in
        # practice)
        mock_response = Mock()
        mock_response.response = """
        教練: 我想要聊一個關於生活工作平衡的議題。
        客戶: 好的，沒有問題，我們可以開始討論。
        教練: 謝謝你願意分享。
        """

        mock_lemur_task.return_value = mock_response

        # Run combined processing
        smoother = LeMURTranscriptSmoother()
        result = await smoother.combined_processing_with_lemur(
            self.test_segments, self.context
        )

        # Verify results
        assert len(result.segments) == 3

        # Check speaker identification
        assert result.segments[0].speaker == "教練"
        assert result.segments[1].speaker == "客戶"
        assert result.segments[2].speaker == "教練"

        # Check text cleanup
        for segment in result.segments:
            # Should not have spaces between Chinese characters
            assert "  " not in segment.text  # No double spaces
            assert " 想" not in segment.text  # No space before Chinese
            assert "我 想" not in segment.text  # No space between Chinese

        # Check first segment specifically
        assert "我想要聊一個關於生活工作平衡的議題" in result.segments[0].text

        # Verify timing preserved from original segments
        assert result.segments[0].start == 1000
        assert result.segments[1].start == 5100
        assert result.segments[2].start == 8100

    @pytest.mark.asyncio
    @patch("coaching_assistant.services.lemur_transcript_smoother.aai.Lemur.task")
    async def test_combined_processing_with_mixed_response(self, mock_lemur_task):
        """Test processing with mixed JSON + text response."""

        # Mock LeMUR response - mixed format
        mock_response = Mock()
        mock_response.response = """
        Some explanatory text here...

        {"A": "教練", "B": "客戶"}

        教練: 我想要聊一個關於工作的議題。
        客戶: 好的，沒有問題。
        教練: 謝謝你。
        """

        mock_lemur_task.return_value = mock_response

        smoother = LeMURTranscriptSmoother()
        result = await smoother.combined_processing_with_lemur(
            self.test_segments, self.context
        )

        # Should extract speaker mapping
        assert len(result.segments) == 3
        assert result.segments[0].speaker == "教練"
        assert result.segments[1].speaker == "客戶"

        # Should still apply cleanup
        for segment in result.segments:
            assert " 想" not in segment.text

    @pytest.mark.asyncio
    @patch("coaching_assistant.services.lemur_transcript_smoother.aai.Lemur.task")
    async def test_emergency_fallback_when_lemur_fails(self, mock_lemur_task):
        """Test emergency fallback when LeMUR processing completely fails."""

        # Mock LeMUR failure
        mock_lemur_task.side_effect = Exception("LeMUR API error")

        smoother = LeMURTranscriptSmoother()
        result = await smoother.combined_processing_with_lemur(
            self.test_segments, self.context
        )

        # Should still return segments with basic cleanup
        assert len(result.segments) == 3

        # Should apply mandatory cleanup even in fallback
        for segment in result.segments:
            # Check that spaces were removed by mandatory cleanup
            original_had_spaces = any(" " in seg["text"] for seg in self.test_segments)
            if original_had_spaces:
                # At least some cleanup should have been applied
                assert (
                    segment.text
                    != self.test_segments[result.segments.index(segment)]["text"]
                )

    @pytest.mark.asyncio
    @patch("coaching_assistant.utils.chinese_converter.convert_to_traditional")
    @patch("coaching_assistant.services.lemur_transcript_smoother.aai.Lemur.task")
    async def test_mandatory_traditional_chinese_conversion(
        self, mock_lemur_task, mock_convert
    ):
        """Test that Traditional Chinese conversion is always applied."""

        # Mock conversion
        mock_convert.side_effect = lambda x: x.replace("关于", "關於").replace(
            "问题", "問題"
        )

        # Mock LeMUR response with simplified Chinese
        mock_response = Mock()
        mock_response.response = """
        教練: 我想要聊关于工作问题。
        客戶: 好的没有问题。
        """

        mock_lemur_task.return_value = mock_response

        smoother = LeMURTranscriptSmoother()
        result = await smoother.combined_processing_with_lemur(
            self.test_segments, self.context
        )

        # Should call Traditional Chinese conversion
        assert mock_convert.call_count > 0

        # Should have converted simplified to traditional
        assert "關於" in result.segments[0].text
        assert "問題" in result.segments[0].text or "問題" in result.segments[1].text

    def test_segment_merging_before_lemur(self):
        """Test that segments are merged before LeMUR processing."""

        # Segments with small gaps that should be merged
        fragmented_segments = [
            {
                "speaker": "A",
                "text": "我们今天就先",
                "start": 1000,
                "end": 2000,
            },
            {
                "speaker": "A",
                "text": "暂时结束在这边",
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

        smoother = LeMURTranscriptSmoother()
        merged = smoother._merge_close_segments(fragmented_segments, max_gap_ms=500)

        # Should merge first two segments (same speaker, small gap)
        assert len(merged) == 2
        assert merged[0]["speaker"] == "A"
        assert "我们今天就先暂时结束在这边" in merged[0]["text"]
        assert merged[1]["speaker"] == "B"

    @pytest.mark.asyncio
    @patch("coaching_assistant.services.lemur_transcript_smoother.aai.Lemur.task")
    async def test_problematic_segment_processing(self, mock_lemur_task):
        """Test processing of the actual problematic segment from user logs."""

        # Mock LeMUR response for the problematic segment
        mock_response = Mock()
        mock_response.response = """
        客戶: 嗯，對確實，嗯好，那我們今天就先暫時結束在這邊，Lisa OK嗎？
        教練: OK我沒有問題，好謝謝你，謝謝謝謝好。
        """

        mock_lemur_task.return_value = mock_response

        # Test with the actual problematic segment
        segments = [self.problematic_segment]

        smoother = LeMURTranscriptSmoother()
        result = await smoother.combined_processing_with_lemur(segments, self.context)

        # Should handle the mixed content correctly
        assert len(result.segments) >= 1

        # Should remove spaces between Chinese characters
        for segment in result.segments:
            assert "嗯 對" not in segment.text  # Should be "嗯對"
            assert "我 们" not in segment.text  # Should be "我們"
            assert "没有 问题" not in segment.text  # Should be "沒有問題"

        # Should identify speakers correctly
        speakers = [seg.speaker for seg in result.segments]
        assert "客戶" in speakers or "教練" in speakers


class TestConvenienceFunctionIntegration:
    """Test the convenience function smooth_transcript_with_lemur."""

    @pytest.mark.asyncio
    @patch("coaching_assistant.services.lemur_transcript_smoother.aai.Lemur.task")
    async def test_convenience_function_with_combined_mode(self, mock_lemur_task):
        """Test the convenience function using combined processing mode."""

        mock_response = Mock()
        mock_response.response = """
        教練: 測試內容一。
        客戶: 測試內容二。
        """
        mock_lemur_task.return_value = mock_response

        segments = [
            {
                "speaker": "A",
                "text": "测试 内容 一",
                "start": 1000,
                "end": 2000,
            },
            {
                "speaker": "B",
                "text": "测试 内容 二",
                "start": 2000,
                "end": 3000,
            },
        ]

        # Test with combined processing enabled
        result = await smooth_transcript_with_lemur(
            segments=segments,
            session_language="zh-TW",
            use_combined_processing=True,
        )

        assert len(result.segments) == 2
        assert result.segments[0].speaker == "教練"
        assert result.segments[1].speaker == "客戶"

        # Should apply cleanup
        assert "測試內容一" in result.segments[0].text
        assert "測試內容二" in result.segments[1].text

    @pytest.mark.asyncio
    @patch("coaching_assistant.services.lemur_transcript_smoother.aai.Lemur.task")
    async def test_convenience_function_speaker_only_mode(self, mock_lemur_task):
        """Test speaker identification only mode."""

        mock_response = Mock()
        mock_response.response = '{"A": "教練", "B": "客戶"}'
        mock_lemur_task.return_value = mock_response

        segments = [
            {"speaker": "A", "text": "测试内容", "start": 1000, "end": 2000},
            {"speaker": "B", "text": "测试内容", "start": 2000, "end": 3000},
        ]

        result = await smooth_transcript_with_lemur(
            segments=segments,
            session_language="zh-TW",
            speaker_identification_only=True,
        )

        # Should have correct speakers but might keep original text
        assert len(result.segments) == 2
        # The speaker correction should be applied
        speakers = [seg.speaker for seg in result.segments]
        assert "教練" in speakers or "客戶" in speakers


if __name__ == "__main__":
    # Run async tests
    async def run_tests():
        test_instance = TestLeMURChineseProcessingIntegration()
        test_instance.setup_method()

        # Run a basic test
        await test_instance.test_combined_processing_with_pure_text_response()
        print("✅ Basic integration test passed")

    asyncio.run(run_tests())
