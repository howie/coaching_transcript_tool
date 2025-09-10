"""
AssemblyAI Transcript Smoothing Service with Multi-Language Support.

This module provides a language-agnostic framework for:
1. Smoothing speaker boundaries in AssemblyAI transcripts
2. Repairing punctuation based on language-specific rules
3. Maintaining timing information and speaker assignments

Uses Factory Pattern to support different languages with specialized processors.
"""

import re
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Tuple, Union
from pydantic import BaseModel, field_validator
from enum import Enum

logger = logging.getLogger(__name__)


# Enums and Constants
class SupportedLanguage(Enum):
    """Supported languages for transcript processing."""

    CHINESE = "chinese"
    ENGLISH = "english"
    JAPANESE = "japanese"
    AUTO = "auto"


# Common Data Structures
class WordTimestamp(BaseModel):
    """Word-level timestamp from AssemblyAI transcript."""

    text: str
    start: Union[int, float]  # milliseconds - accept both int and float
    end: Union[int, float]  # milliseconds - accept both int and float
    confidence: Optional[float] = 1.0

    @field_validator("start", "end")
    @classmethod
    def convert_to_int(cls, v):
        """Convert float timestamps to integers."""
        return int(round(v))


class Utterance(BaseModel):
    """Single utterance from AssemblyAI transcript."""

    speaker: str
    start: Union[int, float]  # milliseconds - accept both int and float
    end: Union[int, float]  # milliseconds - accept both int and float
    confidence: float
    words: List[WordTimestamp]

    @field_validator("start", "end")
    @classmethod
    def convert_to_int(cls, v):
        """Convert float timestamps to integers."""
        return int(round(v))

    @field_validator("words")
    @classmethod
    def words_not_empty(cls, v):
        if not v:
            raise ValueError("words 缺失，無法做時間戳平滑")
        return v


class TranscriptInput(BaseModel):
    """Input format for transcript smoothing."""

    utterances: List[Utterance]
    language: str = "auto"  # Language hint for processing

    @field_validator("utterances")
    @classmethod
    def utterances_not_empty(cls, v):
        if not v:
            raise ValueError("utterances 缺失")
        return v


class ProcessedSegment(BaseModel):
    """Output segment after smoothing and punctuation repair."""

    speaker: str
    start_ms: int
    end_ms: int
    text: str
    source_utterance_indices: List[int]
    note: Optional[str] = None


class HeuristicStats(BaseModel):
    """Statistics for different heuristic rules applied."""

    short_first_segment: int = 0
    filler_words: int = 0
    no_terminal_punct: int = 0
    echo_backfill: int = 0


class ProcessingStats(BaseModel):
    """Overall processing statistics."""

    moved_word_count: int
    merged_segments: int
    split_segments: int
    heuristic_hits: HeuristicStats
    language_detected: str
    processor_used: str


class ProcessingResult(BaseModel):
    """Complete result from transcript smoothing."""

    segments: List[ProcessedSegment]
    stats: ProcessingStats


# Configuration Classes
@dataclass
class BaseSmoothingConfig:
    """Base configuration for speaker boundary smoothing."""

    th_short_head_sec: float = 0.9
    th_gap_sec: float = 0.25
    th_max_move_sec: float = 1.5
    n_pass: int = 2


@dataclass
class BasePunctuationConfig:
    """Base configuration for punctuation repair."""

    th_sent_gap_sec: float = 0.6
    min_sentence_length: int = 3


@dataclass
class BaseProcessorConfig:
    """Base processor configuration."""

    smoothing: BaseSmoothingConfig = field(default_factory=BaseSmoothingConfig)
    punctuation: BasePunctuationConfig = field(
        default_factory=BasePunctuationConfig
    )


# Internal helper classes
@dataclass
class WordWithSpeaker:
    """Word with speaker and timing information."""

    text: str
    start: int  # milliseconds
    end: int  # milliseconds
    speaker: str
    utterance_index: int
    confidence: float = 1.0


# Custom Exceptions
class TranscriptProcessingError(Exception):
    """Base class for transcript processing errors."""


class MissingWordsError(TranscriptProcessingError):
    """Raised when words data is missing from utterances."""


class UnsupportedLanguageError(TranscriptProcessingError):
    """Raised when language is not supported."""


# Abstract Base Classes
class LanguageProcessor(ABC):
    """Abstract base class for language-specific processing."""

    @abstractmethod
    def get_supported_language(self) -> SupportedLanguage:
        """Get the language this processor supports."""

    @abstractmethod
    def detect_language(self, utterances: List[Utterance]) -> bool:
        """Detect if utterances are in this processor's language."""

    @abstractmethod
    def get_filler_words(self) -> List[str]:
        """Get language-specific filler words."""

    @abstractmethod
    def has_terminal_punctuation(self, text: str) -> bool:
        """Check if text has terminal punctuation."""

    @abstractmethod
    def determine_punctuation(self, text: str) -> str:
        """Determine appropriate punctuation for text."""

    @abstractmethod
    def normalize_punctuation(self, text: str) -> str:
        """Normalize punctuation for language."""

    @abstractmethod
    def process_smart_quotes(self, text: str) -> str:
        """Process smart quotes appropriately."""


# Language-Specific Configurations
@dataclass
class ChineseSmoothingConfig(BaseSmoothingConfig):
    """Chinese-specific smoothing configuration."""

    th_filler_max_sec: float = 0.6
    th_echo_max_sec: float = 1.2
    th_echo_gap_sec: float = 1.2
    echo_jaccard_tau: float = 0.6
    filler_whitelist: List[str] = field(
        default_factory=lambda: [
            "嗯",
            "呃",
            "唉",
            "喔",
            "哦",
            "唔",
            "啊",
            "欸",
            "對",
            "好",
            "唉呀",
            "唉呦",
            "哦對",
            "欸對",
        ]
    )


@dataclass
class EnglishSmoothingConfig(BaseSmoothingConfig):
    """English-specific smoothing configuration."""

    th_filler_max_sec: float = 0.5
    th_echo_max_sec: float = 1.0
    th_echo_gap_sec: float = 1.0
    echo_jaccard_tau: float = 0.7
    filler_whitelist: List[str] = field(
        default_factory=lambda: [
            "um",
            "uh",
            "er",
            "ah",
            "yeah",
            "okay",
            "right",
            "well",
            "you know",
            "like",
            "so",
        ]
    )


@dataclass
class ChineseProcessorConfig(BaseProcessorConfig):
    """Chinese processor configuration."""

    smoothing: ChineseSmoothingConfig = field(
        default_factory=ChineseSmoothingConfig
    )


@dataclass
class EnglishProcessorConfig(BaseProcessorConfig):
    """English processor configuration."""

    smoothing: EnglishSmoothingConfig = field(
        default_factory=EnglishSmoothingConfig
    )


# Language-Specific Processors
class ChineseProcessor(LanguageProcessor):
    """Chinese language processor."""

    def get_supported_language(self) -> SupportedLanguage:
        return SupportedLanguage.CHINESE

    def detect_language(self, utterances: List[Utterance]) -> bool:
        """Detect Chinese language by checking character patterns."""
        chinese_char_count = 0
        total_char_count = 0

        for utterance in utterances[:3]:  # Check first 3 utterances
            for word in utterance.words:
                for char in word.text:
                    total_char_count += 1
                    if "\u4e00" <= char <= "\u9fff":  # Chinese characters
                        chinese_char_count += 1

        if total_char_count == 0:
            return False

        chinese_ratio = chinese_char_count / total_char_count
        return chinese_ratio > 0.3  # 30% Chinese characters threshold

    def get_filler_words(self) -> List[str]:
        return ["嗯", "呃", "唉", "喔", "哦", "唔", "啊", "欸", "對", "好"]

    def has_terminal_punctuation(self, text: str) -> bool:
        """Check if text ends with Chinese terminal punctuation."""
        if not text:
            return False
        return text.strip().endswith(("。", "！", "？", "…"))

    def determine_punctuation(self, text: str) -> str:
        """Determine appropriate Chinese punctuation."""
        # Question indicators
        question_patterns = [
            "嗎",
            "呢",
            "是不是",
            "對不對",
            "好不好",
            "怎麼",
            "什麼",
            "哪裡",
            "為什麼",
        ]
        if any(pattern in text for pattern in question_patterns):
            return "？"

        # Exclamation indicators
        exclamation_patterns = [
            "真的",
            "太",
            "非常",
            "超級",
            "哇",
            "哎呀",
            "天啊",
            "不行",
            "一定要",
        ]
        if any(pattern in text for pattern in exclamation_patterns):
            return "！"

        # Ellipsis indicators
        ellipsis_patterns = ["之類的", "什麼的", "等等", "等等等"]
        if any(text.endswith(pattern) for pattern in ellipsis_patterns):
            return "…"

        return "。"

    def normalize_punctuation(self, text: str) -> str:
        """Convert to full-width Chinese punctuation."""
        punctuation_map = {
            ",": "，",
            ".": "。",
            "?": "？",
            "!": "！",
            ":": "：",
            ";": "；",
            "(": "（",
            ")": "）",
        }

        for half, full in punctuation_map.items():
            text = text.replace(half, full)

        return text

    def process_smart_quotes(self, text: str) -> str:
        """Process smart quotes for Chinese."""
        result = []
        quote_count = 0

        for char in text:
            if char == '"':
                if quote_count % 2 == 0:
                    result.append('"')  # Opening quote
                else:
                    result.append('"')  # Closing quote
                quote_count += 1
            else:
                result.append(char)

        return "".join(result)


class EnglishProcessor(LanguageProcessor):
    """English language processor."""

    def get_supported_language(self) -> SupportedLanguage:
        return SupportedLanguage.ENGLISH

    def detect_language(self, utterances: List[Utterance]) -> bool:
        """Detect English language by checking patterns."""
        english_words = {
            "the",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "a",
            "an",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "can",
            "may",
            "this",
            "that",
            "these",
            "those",
            "i",
            "you",
            "he",
            "she",
            "it",
            "we",
            "they",
            "me",
            "him",
            "her",
            "us",
            "them",
            "my",
            "your",
            "his",
            "our",
            "their",
            "what",
            "when",
            "where",
            "why",
            "how",
            "who",
            "which",
            "so",
            "about",
        }
        total_words = 0
        english_word_count = 0

        for utterance in utterances[:3]:  # Check first 3 utterances
            for word in utterance.words:
                total_words += 1
                if word.text.lower() in english_words:
                    english_word_count += 1

        if total_words == 0:
            return False

        english_ratio = english_word_count / total_words
        return english_ratio > 0.1  # 10% common English words threshold

    def get_filler_words(self) -> List[str]:
        return ["um", "uh", "er", "ah", "yeah", "okay", "right", "well"]

    def has_terminal_punctuation(self, text: str) -> bool:
        """Check if text ends with English terminal punctuation."""
        if not text:
            return False
        return text.strip().endswith((".", "!", "?"))

    def determine_punctuation(self, text: str) -> str:
        """Determine appropriate English punctuation."""
        # Question indicators
        question_words = [
            "what",
            "where",
            "when",
            "why",
            "how",
            "who",
            "which",
            "do",
            "does",
            "did",
            "can",
            "could",
            "should",
            "would",
        ]
        text_lower = text.lower()

        if any(
            text_lower.startswith(word) for word in question_words
        ) or text_lower.endswith("?"):
            return "?"

        # Exclamation indicators
        if any(
            word in text_lower
            for word in ["wow", "amazing", "incredible", "fantastic"]
        ):
            return "!"

        return "."

    def normalize_punctuation(self, text: str) -> str:
        """Normalize English punctuation (no changes needed)."""
        return text

    def process_smart_quotes(self, text: str) -> str:
        """Process smart quotes for English."""
        # Simple quote normalization
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(""", "'").replace(""", "'")
        return text


# Factory for Language Processors
class LanguageProcessorFactory:
    """Factory for creating language-specific processors."""

    _processors = {
        SupportedLanguage.CHINESE: ChineseProcessor,
        SupportedLanguage.ENGLISH: EnglishProcessor,
    }

    @classmethod
    def create_processor(
        cls, language: SupportedLanguage
    ) -> LanguageProcessor:
        """Create a processor for the specified language."""
        if language not in cls._processors:
            raise UnsupportedLanguageError(
                f"Language {language} is not supported"
            )

        return cls._processors[language]()

    @classmethod
    def detect_language(cls, utterances: List[Utterance]) -> SupportedLanguage:
        """Auto-detect language from utterances."""
        for lang, processor_class in cls._processors.items():
            processor = processor_class()
            if processor.detect_language(utterances):
                logger.info(f"Auto-detected language: {lang.value}")
                return lang

        # Default to Chinese if no detection
        logger.warning("Could not detect language, defaulting to Chinese")
        return SupportedLanguage.CHINESE

    @classmethod
    def get_supported_languages(cls) -> List[SupportedLanguage]:
        """Get list of supported languages."""
        return list(cls._processors.keys())


# Language-Agnostic Core Classes
class SpeakerBoundarySmoother:
    """Handles speaker boundary smoothing logic with language support."""

    def __init__(
        self,
        config: BaseSmoothingConfig,
        language_processor: LanguageProcessor,
    ):
        self.config = config
        self.language_processor = language_processor
        self.stats = HeuristicStats()

    def smooth_boundaries(
        self, utterances: List[Utterance]
    ) -> List[Utterance]:
        """Apply multi-pass iterative smoothing to speaker boundaries."""
        smoothed = utterances.copy()

        for pass_num in range(self.config.n_pass):
            logger.debug(
                f"Starting smoothing pass {pass_num + 1}/{self.config.n_pass}"
            )
            changed = False
            new_smoothed = []

            i = 0
            while i < len(smoothed):
                if i < len(smoothed) - 1:
                    current, next_utt = smoothed[i], smoothed[i + 1]
                    merge_result = self._try_merge_segments(current, next_utt)

                    if merge_result:
                        merged_utterance, remaining_utterance = merge_result
                        new_smoothed.append(merged_utterance)

                        # If there's a remaining utterance, we need to consider it in next iteration
                        if remaining_utterance:
                            # Replace the next utterance with the remaining one
                            smoothed[i + 1] = remaining_utterance
                        else:
                            # No remaining utterance, skip the next one completely
                            i += 1

                        changed = True
                        i += 1
                    else:
                        new_smoothed.append(current)
                        i += 1
                else:
                    new_smoothed.append(smoothed[i])
                    i += 1

            smoothed = new_smoothed
            if not changed:
                logger.debug(
                    f"No changes in pass {pass_num + 1}, stopping early"
                )
                break

        logger.info(f"Boundary smoothing completed. Stats: {self.stats}")
        return smoothed

    def _try_merge_segments(
        self, current: Utterance, next_utt: Utterance
    ) -> Optional[Tuple[Utterance, Optional[Utterance]]]:
        """Try to merge two adjacent segments based on heuristic rules.

        Returns:
            Tuple of (merged_utterance, remaining_utterance) if merge occurred, None otherwise.
            remaining_utterance can be None if all words were moved.
        """
        if current.speaker == next_utt.speaker:
            return None

        # Rule 1: Short head backfill
        merge_result = self._check_short_head_backfill(current, next_utt)
        if merge_result:
            self.stats.short_first_segment += 1
            return merge_result

        # Rule 2: Filler word backfill
        merge_result = self._check_filler_backfill(current, next_utt)
        if merge_result:
            self.stats.filler_words += 1
            return merge_result

        # Rule 3: Echo/quote backfill (if supported by language config)
        if hasattr(self.config, "echo_jaccard_tau"):
            merge_result = self._check_echo_backfill(current, next_utt)
            if merge_result:
                self.stats.echo_backfill += 1
                return merge_result

        return None

    def _check_short_head_backfill(
        self, current: Utterance, next_utt: Utterance
    ) -> Optional[Tuple[Utterance, Optional[Utterance]]]:
        """Check if next segment's head should be backfilled to current speaker."""
        head_duration = self._calculate_head_duration(next_utt)

        if (
            head_duration < self.config.th_short_head_sec
            and not self.language_processor.has_terminal_punctuation(
                current.words[-1].text if current.words else ""
            )
        ):

            words_to_move = self._get_words_within_duration(
                next_utt.words, self.config.th_short_head_sec
            )

            if (
                self._calculate_total_duration(words_to_move)
                <= self.config.th_max_move_sec
            ):
                return self._merge_words_to_previous(
                    current, next_utt, words_to_move
                )

        return None

    def _check_filler_backfill(
        self, current: Utterance, next_utt: Utterance
    ) -> Optional[Tuple[Utterance, Optional[Utterance]]]:
        """Check if next segment starts with a filler word that should be moved back."""
        if not next_utt.words:
            return None

        # Check if current segment ends with terminal punctuation
        if self.language_processor.has_terminal_punctuation(
            current.words[-1].text if current.words else ""
        ):
            return None  # Don't backfill if previous segment has terminal punctuation

        first_word = next_utt.words[0]
        word_duration = (first_word.end - first_word.start) / 1000.0

        filler_words = self.language_processor.get_filler_words()
        th_filler_max_sec = getattr(self.config, "th_filler_max_sec", 0.6)

        if (
            first_word.text in filler_words
            and word_duration < th_filler_max_sec
        ):

            return self._merge_words_to_previous(
                current, next_utt, [first_word]
            )

        return None

    def _check_echo_backfill(
        self, current: Utterance, next_utt: Utterance
    ) -> Optional[Tuple[Utterance, Optional[Utterance]]]:
        """Check for echo/quoted content that should be backfilled."""
        if not hasattr(self.config, "echo_jaccard_tau"):
            return None

        # Check for quotation marks
        if self._has_quotation_marks(next_utt.words):
            quoted_content = self._extract_quoted_content(next_utt.words)
            if self._find_echo_in_previous(current.words, quoted_content):
                words_to_move = self._get_quoted_words(next_utt.words)

                if (
                    self._calculate_total_duration(words_to_move)
                    <= self.config.th_echo_max_sec
                ):
                    return self._merge_words_to_previous(
                        current, next_utt, words_to_move
                    )

        # Check for content similarity (Jaccard similarity)
        similarity = self._calculate_jaccard_similarity(
            current.words[-6:] if len(current.words) >= 6 else current.words,
            next_utt.words[:6] if len(next_utt.words) >= 6 else next_utt.words,
        )

        if similarity >= self.config.echo_jaccard_tau:
            echo_words = self._find_echo_words(current.words, next_utt.words)

            if (
                self._calculate_total_duration(echo_words)
                <= self.config.th_echo_max_sec
            ):
                return self._merge_words_to_previous(
                    current, next_utt, echo_words
                )

        return None

    # Helper methods (implementation similar to before but language-agnostic)
    def _calculate_head_duration(self, utterance: Utterance) -> float:
        """Calculate duration of the head portion of an utterance."""
        if not utterance.words:
            return 0.0

        total_duration = (utterance.end - utterance.start) / 1000.0
        return min(total_duration, self.config.th_short_head_sec)

    def _get_words_within_duration(
        self, words: List[WordTimestamp], max_duration: float
    ) -> List[WordTimestamp]:
        """Get words from start of list within specified duration."""
        if not words:
            return []

        result = []
        start_time = words[0].start

        for word in words:
            duration = (word.end - start_time) / 1000.0
            if duration <= max_duration:
                result.append(word)
            else:
                break

        return result

    def _calculate_total_duration(self, words: List[WordTimestamp]) -> float:
        """Calculate total duration of a list of words."""
        if not words:
            return 0.0
        return (words[-1].end - words[0].start) / 1000.0

    def _has_quotation_marks(self, words: List[WordTimestamp]) -> bool:
        """Check if words contain quotation marks."""
        for word in words:
            if '"' in word.text or '"' in word.text or '"' in word.text:
                return True
        return False

    def _extract_quoted_content(self, words: List[WordTimestamp]) -> str:
        """Extract content within quotation marks."""
        text = "".join(word.text for word in words)
        match = re.search(r'["""](.*?)["""]', text)
        return match.group(1) if match else ""

    def _find_echo_in_previous(
        self, previous_words: List[WordTimestamp], quoted_content: str
    ) -> bool:
        """Check if quoted content appears in previous words."""
        if not quoted_content:
            return False

        previous_text = "".join(word.text for word in previous_words)
        return quoted_content in previous_text

    def _get_quoted_words(
        self, words: List[WordTimestamp]
    ) -> List[WordTimestamp]:
        """Get words that are within quotation marks."""
        result = []
        in_quote = False

        for word in words:
            if '"' in word.text or '"' in word.text:
                in_quote = not in_quote
                result.append(word)
            elif in_quote:
                result.append(word)

        return result

    def _calculate_jaccard_similarity(
        self, words1: List[WordTimestamp], words2: List[WordTimestamp]
    ) -> float:
        """Calculate Jaccard similarity between two word sequences."""
        if not words1 or not words2:
            return 0.0

        set1 = set(word.text.lower() for word in words1)
        set2 = set(word.text.lower() for word in words2)

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def _find_echo_words(
        self,
        previous_words: List[WordTimestamp],
        current_words: List[WordTimestamp],
    ) -> List[WordTimestamp]:
        """Find echoed words in current that match previous."""
        echo_words = []
        previous_texts = [word.text.lower() for word in previous_words]

        for word in current_words:
            if word.text.lower() in previous_texts:
                echo_words.append(word)

        return echo_words

    def _merge_words_to_previous(
        self,
        current: Utterance,
        next_utt: Utterance,
        words_to_move: List[WordTimestamp],
    ) -> Tuple[Utterance, Optional[Utterance]]:
        """Create merged utterance by moving words from next to current.

        Returns:
            Tuple of (merged_utterance, remaining_utterance).
            remaining_utterance is None if all words were moved.
        """
        if not words_to_move:
            return current, next_utt

        # Create new merged utterance with moved words
        new_words = current.words + words_to_move
        new_end = words_to_move[-1].end if words_to_move else current.end

        merged = Utterance(
            speaker=current.speaker,
            start=current.start,
            end=new_end,
            confidence=min(current.confidence, next_utt.confidence),
            words=new_words,
        )

        # Create remaining utterance with words that weren't moved
        remaining_words = [w for w in next_utt.words if w not in words_to_move]

        if remaining_words:
            remaining = Utterance(
                speaker=next_utt.speaker,
                start=remaining_words[0].start,
                end=remaining_words[-1].end,
                confidence=next_utt.confidence,
                words=remaining_words,
            )
            return merged, remaining
        else:
            # All words were moved, no remaining utterance
            return merged, None


class PunctuationRepairer:
    """Handles punctuation repair with language support."""

    def __init__(
        self,
        config: BasePunctuationConfig,
        language_processor: LanguageProcessor,
    ):
        self.config = config
        self.language_processor = language_processor

    def repair_punctuation(
        self, utterances: List[Utterance]
    ) -> List[ProcessedSegment]:
        """Repair punctuation and split sentences based on pause timing."""
        all_words = self._flatten_words_with_speaker(utterances)
        sentences = self._split_into_sentences(all_words)

        segments = []
        for sentence_words in sentences:
            if sentence_words:
                segment = self._create_segment_with_punctuation(sentence_words)
                segments.append(segment)

        logger.info(
            f"Punctuation repair completed. Created {len(segments)} segments from {len(utterances)} utterances"
        )
        return segments

    def _flatten_words_with_speaker(
        self, utterances: List[Utterance]
    ) -> List[WordWithSpeaker]:
        """Convert utterances to flat word list with speaker info."""
        words = []

        for utt_idx, utterance in enumerate(utterances):
            for word in utterance.words:
                word_with_speaker = WordWithSpeaker(
                    text=word.text,
                    start=word.start,
                    end=word.end,
                    speaker=utterance.speaker,
                    utterance_index=utt_idx,
                    confidence=word.confidence or 1.0,
                )
                words.append(word_with_speaker)

        return words

    def _split_into_sentences(
        self, words: List[WordWithSpeaker]
    ) -> List[List[WordWithSpeaker]]:
        """Split words into sentences based on pause timing."""
        sentences = []
        current_sentence = []

        for i, word in enumerate(words):
            current_sentence.append(word)

            if i < len(words) - 1:
                gap = (words[i + 1].start - word.end) / 1000.0

                if gap > self.config.th_sent_gap_sec:
                    sentence_text = "".join(w.text for w in current_sentence)
                    if (
                        len(sentence_text.strip())
                        >= self.config.min_sentence_length
                    ):
                        sentences.append(current_sentence)
                        current_sentence = []

        if current_sentence:
            sentences.append(current_sentence)

        return sentences

    def _create_segment_with_punctuation(
        self, words: List[WordWithSpeaker]
    ) -> ProcessedSegment:
        """Create a segment with appropriate punctuation."""
        if not words:
            raise ValueError("Empty sentence cannot create segment")

        text = "".join(word.text for word in words)
        punctuation = self.language_processor.determine_punctuation(text)
        text_with_punct = self.language_processor.normalize_punctuation(
            text + punctuation
        )
        text_with_punct = self.language_processor.process_smart_quotes(
            text_with_punct
        )

        return ProcessedSegment(
            speaker=words[0].speaker,
            start_ms=words[0].start,
            end_ms=words[-1].end,
            text=text_with_punct,
            source_utterance_indices=list(
                set(word.utterance_index for word in words)
            ),
            note=f"添加標點：{punctuation}",
        )


# Main Service Class
class TranscriptSmoothingService:
    """Main service for transcript smoothing with multi-language support."""

    def __init__(
        self,
        language: Optional[str] = None,
        config: Optional[BaseProcessorConfig] = None,
    ):
        self.language = language
        self.config = config

    def smooth_and_punctuate(
        self, transcript_json: dict, language: str = "auto", **kwargs
    ) -> ProcessingResult:
        """
        Main function to smooth speaker boundaries and repair punctuation.

        Args:
            transcript_json: AssemblyAI transcript with utterances and words
            language: Language hint ("auto", "chinese", "english", etc.)
            **kwargs: Additional configuration parameters

        Returns:
            ProcessingResult with smoothed segments and statistics
        """
        # Validate input
        self._validate_input(transcript_json)

        # Parse input
        transcript_input = TranscriptInput(
            **transcript_json, language=language
        )

        # Detect/determine language
        if language == "auto":
            detected_language = LanguageProcessorFactory.detect_language(
                transcript_input.utterances
            )
        else:
            try:
                detected_language = SupportedLanguage(language.lower())
            except ValueError:
                logger.warning(
                    f"Unsupported language '{language}', falling back to auto-detection"
                )
                detected_language = LanguageProcessorFactory.detect_language(
                    transcript_input.utterances
                )

        # Create language processor
        language_processor = LanguageProcessorFactory.create_processor(
            detected_language
        )

        # Create configuration based on language
        if detected_language == SupportedLanguage.CHINESE:
            config = ChineseProcessorConfig()
        elif detected_language == SupportedLanguage.ENGLISH:
            config = EnglishProcessorConfig()
        else:
            config = BaseProcessorConfig()

        # Update config with kwargs
        self._update_config_from_kwargs(config, **kwargs)

        # Create processors
        boundary_smoother = SpeakerBoundarySmoother(
            config.smoothing, language_processor
        )
        punctuation_repairer = PunctuationRepairer(
            config.punctuation, language_processor
        )

        logger.info(
            f"Starting transcript smoothing for language: {detected_language.value}"
        )

        # Process
        smoothed_utterances = boundary_smoother.smooth_boundaries(
            transcript_input.utterances
        )
        final_segments = punctuation_repairer.repair_punctuation(
            smoothed_utterances
        )

        # Calculate statistics
        original_word_count = sum(
            len(utt.words) for utt in transcript_input.utterances
        )
        moved_word_count = (
            boundary_smoother.stats.short_first_segment
            + boundary_smoother.stats.filler_words
        )
        merged_segments = len(transcript_input.utterances) - len(
            smoothed_utterances
        )
        split_segments = len(final_segments) - len(smoothed_utterances)

        stats = ProcessingStats(
            moved_word_count=moved_word_count,
            merged_segments=merged_segments,
            split_segments=split_segments,
            heuristic_hits=boundary_smoother.stats,
            language_detected=detected_language.value,
            processor_used=language_processor.__class__.__name__,
        )

        logger.info(f"Processing completed. Stats: {stats}")

        return ProcessingResult(segments=final_segments, stats=stats)

    def _validate_input(self, transcript_json: dict) -> None:
        """Validate input transcript data."""
        if "utterances" not in transcript_json:
            raise TranscriptProcessingError(
                "Utterances missing from transcript"
            )

        utterances = transcript_json["utterances"]
        if not utterances:
            raise TranscriptProcessingError("Empty utterances list")

        for i, utterance in enumerate(utterances):
            if "words" not in utterance or not utterance["words"]:
                raise MissingWordsError(
                    f"Words missing in utterance {i}; cannot perform smoothing"
                )

    def _update_config_from_kwargs(
        self, config: BaseProcessorConfig, **kwargs
    ):
        """Update configuration from keyword arguments."""
        # Update smoothing config
        for key, value in kwargs.items():
            if hasattr(config.smoothing, key):
                setattr(config.smoothing, key, value)
            elif hasattr(config.punctuation, key):
                setattr(config.punctuation, key, value)


# Convenience function for external access
def smooth_and_punctuate(
    transcript_json: dict, language: str = "auto", **kwargs
) -> dict:
    """
    Convenience function for transcript smoothing and punctuation repair.

    Args:
        transcript_json: AssemblyAI transcript data
        language: Language hint ("auto", "chinese", "english")
        **kwargs: Additional configuration parameters

    Returns:
        Result as dictionary for easy serialization
    """
    service = TranscriptSmoothingService()
    result = service.smooth_and_punctuate(
        transcript_json=transcript_json, language=language, **kwargs
    )

    return {
        "segments": [segment.model_dump() for segment in result.segments],
        "stats": result.stats.model_dump(),
    }
