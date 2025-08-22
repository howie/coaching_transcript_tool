"""
Unit tests for transcript smoothing service.

Following TDD methodology with comprehensive test coverage.
"""

import pytest
from decimal import Decimal
from typing import List, Dict, Any

from coaching_assistant.services.transcript_smoother import (
    TranscriptSmoothingService,
    LanguageProcessorFactory,
    ChineseProcessor,
    EnglishProcessor,
    SpeakerBoundarySmoother,
    PunctuationRepairer,
    WordTimestamp,
    Utterance,
    TranscriptInput,
    ProcessedSegment,
    SupportedLanguage,
    ChineseSmoothingConfig,
    ChineseProcessorConfig,
    TranscriptProcessingError,
    MissingWordsError,
    UnsupportedLanguageError,
    smooth_and_punctuate
)


class TestLanguageDetection:
    """Test language detection functionality."""
    
    def test_chinese_language_detection(self):
        """Test Chinese language detection with Chinese characters."""
        # Given
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=3000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="你好", start=1000, end=1500),
                    WordTimestamp(text="世界", start=1500, end=2000),
                ]
            )
        ]
        
        processor = ChineseProcessor()
        
        # When
        is_chinese = processor.detect_language(utterances)
        
        # Then
        assert is_chinese is True
    
    def test_english_language_detection(self):
        """Test English language detection with common words."""
        # Given
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=3000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="the", start=1000, end=1200),
                    WordTimestamp(text="quick", start=1200, end=1500),
                    WordTimestamp(text="brown", start=1500, end=1800),
                ]
            )
        ]
        
        processor = EnglishProcessor()
        
        # When
        is_english = processor.detect_language(utterances)
        
        # Then
        assert is_english is True
    
    def test_auto_language_detection_chinese(self):
        """Test auto-detection for Chinese content."""
        # Given
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=3000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="然後", start=1000, end=1300),
                    WordTimestamp(text="我們", start=1300, end=1600),
                    WordTimestamp(text="就", start=1600, end=1800),
                ]
            )
        ]
        
        # When
        detected_language = LanguageProcessorFactory.detect_language(utterances)
        
        # Then
        assert detected_language == SupportedLanguage.CHINESE


class TestChineseProcessor:
    """Test Chinese-specific processing."""
    
    def test_chinese_terminal_punctuation_detection(self):
        """Test Chinese terminal punctuation detection."""
        processor = ChineseProcessor()
        
        # Test cases with expected results
        test_cases = [
            ("你好。", True),
            ("真的！", True),
            ("是嗎？", True),
            ("等等…", True),
            ("然後我們", False),
            ("", False),
        ]
        
        for text, expected in test_cases:
            result = processor.has_terminal_punctuation(text)
            assert result == expected, f"Failed for text: '{text}'"
    
    def test_chinese_punctuation_determination(self):
        """Test Chinese punctuation determination logic."""
        processor = ChineseProcessor()
        
        test_cases = [
            ("你覺得怎麼樣呢", "？"),  # Question word
            ("真的太厲害了", "！"),    # Exclamation
            ("之類的", "…"),          # Ellipsis
            ("我覺得很好", "。"),      # Default period
        ]
        
        for text, expected_punct in test_cases:
            result = processor.determine_punctuation(text)
            assert result == expected_punct, f"Failed for text: '{text}'"
    
    def test_chinese_punctuation_normalization(self):
        """Test Chinese punctuation normalization."""
        processor = ChineseProcessor()
        
        test_cases = [
            ("你好,世界", "你好，世界"),
            ("真的!", "真的！"),
            ("是嗎?", "是嗎？"),
            ("(括號)", "（括號）"),
        ]
        
        for input_text, expected in test_cases:
            result = processor.normalize_punctuation(input_text)
            assert result == expected, f"Failed for input: '{input_text}'"
    
    def test_chinese_smart_quotes(self):
        """Test Chinese smart quote processing."""
        processor = ChineseProcessor()
        
        # Test quote conversion
        input_text = '他說"這樣很好"我同意'
        expected = '他說"這樣很好"我同意'
        result = processor.process_smart_quotes(input_text)
        assert result == expected


class TestEnglishProcessor:
    """Test English-specific processing."""
    
    def test_english_terminal_punctuation_detection(self):
        """Test English terminal punctuation detection."""
        processor = EnglishProcessor()
        
        test_cases = [
            ("Hello world.", True),
            ("Really!", True),
            ("Is it?", True),
            ("And then we", False),
            ("", False),
        ]
        
        for text, expected in test_cases:
            result = processor.has_terminal_punctuation(text)
            assert result == expected, f"Failed for text: '{text}'"
    
    def test_english_punctuation_determination(self):
        """Test English punctuation determination logic."""
        processor = EnglishProcessor()
        
        test_cases = [
            ("What do you think", "?"),    # Question word
            ("That's amazing", "!"),       # Exclamation
            ("I think it's good", "."),    # Default period
        ]
        
        for text, expected_punct in test_cases:
            result = processor.determine_punctuation(text)
            assert result == expected_punct, f"Failed for text: '{text}'"


class TestSpeakerBoundarySmoother:
    """Test speaker boundary smoothing logic."""
    
    def test_short_head_backfill_should_merge(self):
        """Test that short head segments are properly backfilled."""
        # Given
        config = ChineseSmoothingConfig()
        processor = ChineseProcessor()
        smoother = SpeakerBoundarySmoother(config, processor)
        
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=3000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="然後", start=1000, end=1500),
                    WordTimestamp(text="我們", start=1500, end=2000),
                    WordTimestamp(text="就", start=2000, end=2300),
                    WordTimestamp(text="先", start=2300, end=2600),
                    WordTimestamp(text="這樣", start=2600, end=3000),
                ]
            ),
            Utterance(
                speaker="B",
                start=3100,
                end=3600,
                confidence=0.8,
                words=[
                    WordTimestamp(text="嗯", start=3100, end=3300),
                    WordTimestamp(text="對", start=3300, end=3600),
                ]
            )
        ]
        
        # When
        result = smoother.smooth_boundaries(utterances)
        
        # Then
        assert len(result) == 1  # Should merge into one utterance
        assert result[0].speaker == "A"
        assert len(result[0].words) == 7  # 5 + 2 words
        assert smoother.stats.short_first_segment == 1
    
    def test_terminal_punctuation_should_not_merge(self):
        """Test that segments with terminal punctuation don't merge."""
        # Given
        config = ChineseSmoothingConfig()
        processor = ChineseProcessor()
        smoother = SpeakerBoundarySmoother(config, processor)
        
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=3000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="好", start=1000, end=1300),
                    WordTimestamp(text="的", start=1300, end=1600),
                    WordTimestamp(text="。", start=1600, end=1700),
                ]
            ),
            Utterance(
                speaker="B",
                start=3100,
                end=3400,
                confidence=0.8,
                words=[
                    WordTimestamp(text="嗯", start=3100, end=3400),
                ]
            )
        ]
        
        # When
        result = smoother.smooth_boundaries(utterances)
        
        # Then
        assert len(result) == 2  # Should not merge
        assert smoother.stats.short_first_segment == 0
    
    def test_filler_word_backfill(self):
        """Test filler word backfill functionality."""
        # Given
        config = ChineseSmoothingConfig()
        processor = ChineseProcessor()
        smoother = SpeakerBoundarySmoother(config, processor)
        
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=2000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="我", start=1000, end=1200),
                    WordTimestamp(text="覺得", start=1200, end=1600),
                    WordTimestamp(text="。", start=1600, end=1700),  # Terminal punctuation to avoid short head rule
                ]
            ),
            Utterance(
                speaker="B",
                start=2100,
                end=2400,
                confidence=0.8,
                words=[
                    WordTimestamp(text="嗯", start=2100, end=2400),  # Filler word, short duration
                ]
            )
        ]
        
        # When
        result = smoother.smooth_boundaries(utterances)
        
        # Then
        assert len(result) == 2  # Should NOT merge because of terminal punctuation
        assert smoother.stats.filler_words == 0  # Should not trigger filler word rule
    
    def test_filler_word_backfill_without_terminal_punct(self):
        """Test filler word backfill when previous segment has no terminal punctuation."""
        # Given
        config = ChineseSmoothingConfig()
        # Adjust config to prevent short head backfill from triggering
        config.th_short_head_sec = 0.1  # Very short to avoid short head rule
        processor = ChineseProcessor()
        smoother = SpeakerBoundarySmoother(config, processor)
        
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=2000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="我", start=1000, end=1200),
                    WordTimestamp(text="想", start=1200, end=1600),
                    # No terminal punctuation
                ]
            ),
            Utterance(
                speaker="B",
                start=2500,  # Longer gap to avoid short head rule
                end=2800,
                confidence=0.8,
                words=[
                    WordTimestamp(text="嗯", start=2500, end=2800),  # Filler word, 0.3 sec duration
                ]
            )
        ]
        
        # When
        result = smoother.smooth_boundaries(utterances)
        
        # Then
        assert len(result) == 1  # Should merge due to filler word
        assert result[0].speaker == "A"
        assert smoother.stats.filler_words == 1


class TestPunctuationRepairer:
    """Test punctuation repair functionality."""
    
    def test_sentence_splitting_by_pause(self):
        """Test sentence splitting based on pause timing."""
        # Given
        config = ChineseProcessorConfig().punctuation
        processor = ChineseProcessor()
        repairer = PunctuationRepairer(config, processor)
        
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=8000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="我", start=1000, end=1200),
                    WordTimestamp(text="覺得", start=1200, end=1600),
                    WordTimestamp(text="這個", start=1600, end=2000),
                    WordTimestamp(text="方案", start=2000, end=2400),
                    # 0.8 second pause
                    WordTimestamp(text="應該", start=3200, end=3600),
                    WordTimestamp(text="可以", start=3600, end=4000),
                    WordTimestamp(text="考慮", start=4000, end=4400),
                ]
            )
        ]
        
        # When
        result = repairer.repair_punctuation(utterances)
        
        # Then
        assert len(result) == 2  # Should split into 2 sentences
        assert result[0].text.endswith("。")
        assert result[1].text.endswith("。")
    
    def test_punctuation_assignment(self):
        """Test appropriate punctuation assignment."""
        # Given
        config = ChineseProcessorConfig().punctuation
        processor = ChineseProcessor()
        repairer = PunctuationRepairer(config, processor)
        
        utterances = [
            Utterance(
                speaker="A",
                start=1000,
                end=3000,
                confidence=0.9,
                words=[
                    WordTimestamp(text="你", start=1000, end=1200),
                    WordTimestamp(text="覺得", start=1200, end=1600),
                    WordTimestamp(text="怎麼樣", start=1600, end=2200),
                    WordTimestamp(text="呢", start=2200, end=2400),
                ]
            )
        ]
        
        # When
        result = repairer.repair_punctuation(utterances)
        
        # Then
        assert len(result) == 1
        assert result[0].text == "你覺得怎麼樣呢？"


class TestTranscriptSmoothingService:
    """Test the main smoothing service."""
    
    def test_complete_processing_pipeline(self):
        """Test the complete processing pipeline."""
        # Given
        service = TranscriptSmoothingService()
        
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 5000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "然後", "start": 1000, "end": 1500},
                        {"text": "我們", "start": 1500, "end": 2000},
                        {"text": "就", "start": 2000, "end": 2300},
                        {"text": "先", "start": 2300, "end": 2600},
                        {"text": "這樣", "start": 2600, "end": 3000},
                    ]
                },
                {
                    "speaker": "B",
                    "start": 3100,
                    "end": 3600,
                    "confidence": 0.8,
                    "words": [
                        {"text": "嗯", "start": 3100, "end": 3300},
                        {"text": "對", "start": 3300, "end": 3600},
                    ]
                }
            ]
        }
        
        # When
        result = service.smooth_and_punctuate(transcript_json, language="chinese")
        
        # Then
        assert len(result.segments) >= 1
        assert result.stats.language_detected == "chinese"
        assert result.stats.processor_used == "ChineseProcessor"
        assert result.stats.moved_word_count >= 0
    
    def test_auto_language_detection(self):
        """Test automatic language detection."""
        # Given
        service = TranscriptSmoothingService()
        
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "你好", "start": 1000, "end": 1500},
                        {"text": "世界", "start": 1500, "end": 2000},
                    ]
                }
            ]
        }
        
        # When
        result = service.smooth_and_punctuate(transcript_json, language="auto")
        
        # Then
        assert result.stats.language_detected == "chinese"
    
    def test_convenience_function(self):
        """Test the convenience function."""
        # Given
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "Hello", "start": 1000, "end": 1300},
                        {"text": "world", "start": 1300, "end": 1600},
                    ]
                }
            ]
        }
        
        # When
        result = smooth_and_punctuate(transcript_json, language="english")
        
        # Then
        assert isinstance(result, dict)
        assert "segments" in result
        assert "stats" in result
        assert len(result["segments"]) >= 1


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_missing_utterances_error(self):
        """Test error when utterances are missing."""
        service = TranscriptSmoothingService()
        
        with pytest.raises(TranscriptProcessingError, match="Utterances missing"):
            service.smooth_and_punctuate({})
    
    def test_empty_utterances_error(self):
        """Test error when utterances list is empty."""
        service = TranscriptSmoothingService()
        
        with pytest.raises(TranscriptProcessingError, match="Empty utterances list"):
            service.smooth_and_punctuate({"utterances": []})
    
    def test_missing_words_error(self):
        """Test error when words are missing from utterances."""
        service = TranscriptSmoothingService()
        
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": []  # Empty words
                }
            ]
        }
        
        with pytest.raises(MissingWordsError, match="Words missing"):
            service.smooth_and_punctuate(transcript_json)
    
    def test_unsupported_language_error(self):
        """Test error for unsupported languages."""
        with pytest.raises(UnsupportedLanguageError):
            LanguageProcessorFactory.create_processor(SupportedLanguage.AUTO)  # AUTO is not a processor
    
    def test_empty_sentence_error(self):
        """Test error when creating segment with empty sentence."""
        config = ChineseProcessorConfig().punctuation
        processor = ChineseProcessor()
        repairer = PunctuationRepairer(config, processor)
        
        with pytest.raises(ValueError, match="Empty sentence cannot create segment"):
            repairer._create_segment_with_punctuation([])


class TestPerformanceAndEdgeCases:
    """Test performance and edge cases."""
    
    def test_single_word_utterance(self):
        """Test processing with single word utterances."""
        service = TranscriptSmoothingService()
        
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 1500,
                    "confidence": 0.9,
                    "words": [
                        {"text": "嗯", "start": 1000, "end": 1500},
                    ]
                }
            ]
        }
        
        # Should not raise error
        result = service.smooth_and_punctuate(transcript_json)
        assert len(result.segments) == 1
    
    def test_no_smoothing_needed(self):
        """Test case where no smoothing is needed."""
        service = TranscriptSmoothingService()
        
        transcript_json = {
            "utterances": [
                {
                    "speaker": "A",
                    "start": 1000,
                    "end": 3000,
                    "confidence": 0.9,
                    "words": [
                        {"text": "你好", "start": 1000, "end": 1500},
                        {"text": "世界", "start": 1500, "end": 2000},
                        {"text": "。", "start": 2000, "end": 2100},
                    ]
                },
                {
                    "speaker": "B",
                    "start": 5000,  # Long gap, different speaker
                    "end": 6000,
                    "confidence": 0.8,
                    "words": [
                        {"text": "謝謝", "start": 5000, "end": 5500},
                        {"text": "。", "start": 5500, "end": 5600},
                    ]
                }
            ]
        }
        
        result = service.smooth_and_punctuate(transcript_json)
        
        # Should preserve original structure when no smoothing needed
        assert result.stats.moved_word_count == 0
        assert result.stats.merged_segments == 0


# Test data creation helpers
def create_test_utterance(speaker: str, words_data: List[Dict[str, Any]], start_offset: int = 0) -> Utterance:
    """Helper to create test utterances."""
    words = []
    for word_data in words_data:
        word = WordTimestamp(
            text=word_data["text"],
            start=word_data["start"] + start_offset,
            end=word_data["end"] + start_offset,
            confidence=word_data.get("confidence", 1.0)
        )
        words.append(word)
    
    return Utterance(
        speaker=speaker,
        start=words[0].start if words else start_offset,
        end=words[-1].end if words else start_offset + 1000,
        confidence=0.9,
        words=words
    )