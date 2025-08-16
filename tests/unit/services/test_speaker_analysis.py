"""Unit tests for speaker analysis utilities."""

import pytest
from unittest.mock import Mock

from coaching_assistant.utils.speaker_analysis import (
    SpeakerAnalyzer,
    SpeakerStats,
    analyze_and_assign_roles,
)
from coaching_assistant.services.stt_provider import TranscriptSegment


class TestSpeakerStats:
    """Test SpeakerStats dataclass."""

    def test_speaker_stats_properties(self):
        """Test calculated properties."""
        stats = SpeakerStats(
            speaker_id=1,
            total_words=100,
            total_duration=120.0,
            segment_count=10,
            question_count=3,
            statement_count=7,
            avg_segment_length=10.0,
        )

        assert stats.question_ratio == 0.3  # 3/10
        assert stats.words_per_minute == 50.0  # 100 words / 2 minutes

    def test_speaker_stats_edge_cases(self):
        """Test edge cases in property calculations."""
        stats = SpeakerStats(
            speaker_id=1,
            total_words=50,
            total_duration=0.0,  # Edge case: zero duration
            segment_count=0,  # Edge case: zero segments
            question_count=0,
            statement_count=0,
            avg_segment_length=0.0,
        )

        assert stats.question_ratio == 0.0  # 0/1 (max prevents division by zero)
        assert stats.words_per_minute > 0  # Should handle near-zero duration


class TestSpeakerAnalyzer:
    """Test SpeakerAnalyzer functionality."""

    def test_init_language_detection(self):
        """Test language detection during initialization."""
        # Test Chinese language codes
        analyzer_zh = SpeakerAnalyzer("cmn-Hant-TW")
        assert analyzer_zh.language == "zh"

        analyzer_zh2 = SpeakerAnalyzer("zh-CN")
        assert analyzer_zh2.language == "zh"

        # Test English language codes
        analyzer_en = SpeakerAnalyzer("en-US")
        assert analyzer_en.language == "en"

        # Test auto/unknown defaults to English
        analyzer_auto = SpeakerAnalyzer("auto")
        assert analyzer_auto.language == "en"

        analyzer_unknown = SpeakerAnalyzer("fr-FR")
        assert analyzer_unknown.language == "en"

    def test_word_counting_english(self):
        """Test word counting for English text."""
        analyzer = SpeakerAnalyzer("en")

        assert analyzer._count_words("Hello world") == 2
        assert analyzer._count_words("How are you doing today?") == 5
        assert analyzer._count_words("") == 0
        assert analyzer._count_words("Single") == 1

    def test_word_counting_chinese(self):
        """Test word counting for Chinese text."""
        analyzer = SpeakerAnalyzer("zh")

        # Chinese characters should be counted individually
        assert analyzer._count_words("你好") == 2  # 2 Chinese characters
        assert (
            analyzer._count_words("你好嗎？") == 3
        )  # 3 Chinese characters, punctuation ignored
        assert (
            analyzer._count_words("Hello 你好") == 2
        )  # Only Chinese characters counted

    def test_question_detection_english(self):
        """Test question detection for English text."""
        analyzer = SpeakerAnalyzer("en")

        # Direct questions
        assert analyzer._is_question("How are you?") is True
        assert analyzer._is_question("What do you think?") is True
        assert analyzer._is_question("Are you feeling better?") is True
        assert analyzer._is_question("Can you help me?") is True

        # Statements
        assert analyzer._is_question("I am fine.") is False
        assert analyzer._is_question("That sounds good.") is False
        assert analyzer._is_question("Thank you very much.") is False

        # Edge cases
        assert analyzer._is_question("") is False

    def test_question_detection_chinese(self):
        """Test question detection for Chinese text."""
        analyzer = SpeakerAnalyzer("zh")

        # Questions with question mark
        assert analyzer._is_question("你好嗎？") is True
        assert analyzer._is_question("今天怎麼樣？") is True

        # Questions with particles
        assert analyzer._is_question("你覺得呢？") is True
        assert analyzer._is_question("好嗎？") is True

        # Statements
        assert analyzer._is_question("我很好。") is False
        assert analyzer._is_question("謝謝你。") is False

    def test_coaching_question_detection_english(self):
        """Test coaching-specific question detection for English."""
        analyzer = SpeakerAnalyzer("en")

        # Coaching patterns
        assert analyzer._is_coaching_question("How does that make you feel?") is True
        assert analyzer._is_coaching_question("Tell me more about that.") is True
        assert analyzer._is_coaching_question("What would you like to happen?") is True
        assert (
            analyzer._is_coaching_question("Help me understand your perspective.")
            is True
        )

        # Regular questions (not coaching-specific)
        assert analyzer._is_coaching_question("What time is it?") is False
        assert analyzer._is_coaching_question("How old are you?") is False

    def test_coaching_question_detection_chinese(self):
        """Test coaching-specific question detection for Chinese."""
        analyzer = SpeakerAnalyzer("zh")

        # Coaching patterns
        assert analyzer._is_coaching_question("你有什麼感受？") is True
        assert analyzer._is_coaching_question("告訴我更多關於這個。") is True
        assert analyzer._is_coaching_question("如果你可以改變什麼？") is True

        # Regular questions
        assert analyzer._is_coaching_question("幾點了？") is False


class TestSpeakerAnalysis:
    """Test speaker analysis and role assignment."""

    def test_analyze_two_speakers_coach_client(self):
        """Test analysis of typical coach-client conversation."""
        analyzer = SpeakerAnalyzer("en")

        segments = [
            # Coach segments - shorter, more questions
            TranscriptSegment(0, 0.0, 3.0, "How are you feeling today?", 0.9),
            TranscriptSegment(0, 10.0, 13.0, "What brings you here?", 0.9),
            TranscriptSegment(0, 25.0, 28.0, "Tell me more about that.", 0.9),
            TranscriptSegment(0, 40.0, 42.0, "How does that make you feel?", 0.9),
            # Client segments - longer, more statements
            TranscriptSegment(
                1, 3.5, 9.5, "I've been struggling with work-life balance lately.", 0.8
            ),
            TranscriptSegment(
                1,
                13.5,
                24.5,
                "Well, I've been working long hours and I feel like I'm missing out on family time. It's really stressing me out.",
                0.8,
            ),
            TranscriptSegment(
                1,
                28.5,
                39.5,
                "It makes me feel guilty and frustrated. I want to be there for my family but I also need to perform at work.",
                0.8,
            ),
        ]

        stats = analyzer.analyze_speakers(segments)

        # Should have 2 speakers
        assert len(stats) == 2
        assert 0 in stats and 1 in stats

        # Speaker 0 (coach) should have more questions
        coach_stats = stats[0]
        client_stats = stats[1]

        assert coach_stats.question_count > client_stats.question_count
        assert coach_stats.question_ratio > client_stats.question_ratio
        assert coach_stats.avg_segment_length < client_stats.avg_segment_length

    def test_role_assignment_clear_case(self):
        """Test role assignment for clear coach-client pattern."""
        analyzer = SpeakerAnalyzer("en")

        segments = [
            # Clear coach pattern: many questions, short segments
            TranscriptSegment(0, 0.0, 2.0, "How are you?", 0.9),
            TranscriptSegment(0, 8.0, 10.0, "What's concerning you?", 0.9),
            TranscriptSegment(0, 20.0, 22.0, "How does that feel?", 0.9),
            TranscriptSegment(0, 35.0, 37.0, "What would help?", 0.9),
            # Clear client pattern: longer responses, fewer questions
            TranscriptSegment(
                1, 2.5, 7.5, "I'm struggling with anxiety and stress.", 0.8
            ),
            TranscriptSegment(
                1,
                10.5,
                19.5,
                "Work has been overwhelming and I can't seem to manage my time effectively.",
                0.8,
            ),
            TranscriptSegment(
                1,
                22.5,
                34.5,
                "It feels like I'm drowning in responsibilities and I don't know how to prioritize.",
                0.8,
            ),
        ]

        roles = analyzer.assign_roles(segments)

        assert len(roles) == 2
        assert roles[0] == "coach"  # Speaker 0 should be identified as coach
        assert roles[1] == "client"  # Speaker 1 should be identified as client

    def test_single_speaker_assignment(self):
        """Test role assignment with single speaker."""
        analyzer = SpeakerAnalyzer("en")

        segments = [
            TranscriptSegment(0, 0.0, 5.0, "This is a monologue.", 0.9),
            TranscriptSegment(0, 5.5, 10.0, "Only one person speaking.", 0.9),
        ]

        roles = analyzer.assign_roles(segments)

        assert len(roles) == 1
        assert roles[0] == "coach"  # Single speaker defaults to coach

    def test_multiple_speaker_assignment(self):
        """Test role assignment with more than 2 speakers."""
        analyzer = SpeakerAnalyzer("en")

        segments = [
            # Speaker 0: Most questions (should be coach)
            TranscriptSegment(0, 0.0, 2.0, "How is everyone?", 0.9),
            TranscriptSegment(0, 10.0, 12.0, "What do you think?", 0.9),
            # Speaker 1: Some responses
            TranscriptSegment(1, 2.5, 5.0, "I'm doing well.", 0.8),
            TranscriptSegment(1, 15.0, 18.0, "That's interesting.", 0.8),
            # Speaker 2: Some responses
            TranscriptSegment(2, 5.5, 9.5, "I agree with that perspective.", 0.8),
            TranscriptSegment(2, 18.5, 22.0, "Thanks for sharing.", 0.8),
        ]

        roles = analyzer.assign_roles(segments)

        assert len(roles) == 3
        assert roles[0] == "coach"  # Highest question ratio
        assert roles[1] == "client"
        assert roles[2] == "client"

    def test_confidence_metrics_high_confidence(self):
        """Test confidence calculation for clear role differentiation."""
        analyzer = SpeakerAnalyzer("en")

        segments = [
            # Very clear coach pattern
            TranscriptSegment(0, 0.0, 2.0, "How are you?", 0.9),
            TranscriptSegment(0, 8.0, 10.0, "What's wrong?", 0.9),
            TranscriptSegment(0, 20.0, 22.0, "Tell me more.", 0.9),
            # Very clear client pattern
            TranscriptSegment(
                1, 2.5, 7.5, "I'm struggling with work and feeling overwhelmed.", 0.8
            ),
            TranscriptSegment(
                1,
                10.5,
                19.5,
                "The deadlines are impossible and my boss is unreasonable.",
                0.8,
            ),
        ]

        roles = {0: "coach", 1: "client"}
        confidence = analyzer.get_confidence_metrics(segments, roles)

        # Should have high confidence due to clear differentiation
        assert confidence["confidence"] > 0.7
        assert confidence["coach_question_ratio"] > confidence["client_question_ratio"]
        assert confidence["question_ratio_difference"] > 0

    def test_confidence_metrics_low_confidence(self):
        """Test confidence calculation for ambiguous role differentiation."""
        analyzer = SpeakerAnalyzer("en")

        segments = [
            # Ambiguous speakers - both ask questions and make statements
            TranscriptSegment(
                0, 0.0, 5.0, "How was your weekend? I had a great time.", 0.9
            ),
            TranscriptSegment(
                1, 5.5, 10.0, "Good, thanks. What did you do? I went hiking.", 0.9
            ),
        ]

        roles = {0: "coach", 1: "client"}
        confidence = analyzer.get_confidence_metrics(segments, roles)

        # Should have lower confidence due to ambiguous pattern
        assert confidence["confidence"] <= 0.7

    def test_empty_segments(self):
        """Test handling of empty segment list."""
        analyzer = SpeakerAnalyzer("en")

        roles = analyzer.assign_roles([])
        confidence = analyzer.get_confidence_metrics([], {})

        assert roles == {}
        assert confidence["confidence"] == 0.0


class TestConvenienceFunctions:
    """Test convenience functions."""

    def test_analyze_and_assign_roles_function(self):
        """Test the convenience function for analysis and role assignment."""
        segments = [
            TranscriptSegment(0, 0.0, 2.0, "How are you feeling?", 0.9),
            TranscriptSegment(1, 2.5, 8.0, "I'm feeling anxious about work.", 0.8),
            TranscriptSegment(0, 8.5, 10.0, "Tell me more.", 0.9),
        ]

        roles, confidence = analyze_and_assign_roles(segments, "en-US")

        assert len(roles) == 2
        assert 0 in roles and 1 in roles
        assert "confidence" in confidence
        assert confidence["confidence"] >= 0.0
        assert confidence["confidence"] <= 1.0

    def test_analyze_chinese_conversation(self):
        """Test analysis of Chinese conversation."""
        segments = [
            TranscriptSegment(0, 0.0, 3.0, "你今天感覺怎麼樣？", 0.9),
            TranscriptSegment(1, 3.5, 10.0, "我最近工作壓力很大，感覺很焦慮。", 0.8),
            TranscriptSegment(0, 10.5, 12.0, "告訴我更多。", 0.9),
        ]

        roles, confidence = analyze_and_assign_roles(segments, "zh-TW")

        assert len(roles) == 2
        assert roles[0] == "coach"  # More questions
        assert roles[1] == "client"  # Longer responses

        # Should detect questions properly in Chinese
        assert confidence["coach_question_ratio"] > confidence["client_question_ratio"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
