"""Speaker analysis utilities for automatic role assignment."""

import logging
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ..services.stt_provider import TranscriptSegment

logger = logging.getLogger(__name__)


@dataclass
class SpeakerStats:
    """Statistics for a speaker in a conversation."""

    speaker_id: int
    total_words: int
    total_duration: float
    segment_count: int
    question_count: int
    statement_count: int
    avg_segment_length: float

    @property
    def question_ratio(self) -> float:
        """Ratio of questions to total segments."""
        return self.question_count / max(self.segment_count, 1)

    @property
    def words_per_minute(self) -> float:
        """Speaking rate in words per minute."""
        return self.total_words / max(self.total_duration / 60.0, 0.01)


class SpeakerAnalyzer:
    """Analyze speaker patterns to automatically assign coach/client roles."""

    # Question markers for different languages
    QUESTION_PATTERNS = {
        "en": [
            r"\b(how|what|why|when|where|who|which|can|could|would|should|do|does|did|is|are|was|were|have|has|had)\b.*\?",
            r"^.*\?$",
            r"\bhow (are|do|did|would|could|should|might|can)\b",
            r"\bwhat (do|did|are|is|would|could|should)\b",
            r"\bwhy (do|did|are|is|would|could|should)\b",
        ],
        "zh": [
            r".*[？]$",
            r"^(什麼|什么|怎麼|怎么|為什麼|为什么|哪裡|哪里|誰|谁|何時|何时|如何|怎樣|怎样)",
            r".*(嗎|吗)[？]?$",
            r".*(呢)[？]?$",
            r"^(你|您).*(想|要|能|可以|會|会|覺得|觉得)",
        ],
    }

    # Coaching-specific question patterns
    COACHING_PATTERNS = {
        "en": [
            r"\b(how does that (feel|make you feel)|what comes up for you|what do you notice)\b",
            r"\b(tell me more about|help me understand|walk me through)\b",
            r"\b(what would|what might|what could|if you could)\b",
            r"\b(how important is|what matters most|what\'s most important)\b",
        ],
        "zh": [
            r".*(感覺如何|有什麼感受|你有什麼想法)",
            r".*(告訴我更多|幫我理解|讓我了解)",
            r".*(如果你可以|你會怎麼|你想要)",
            r".*(對你來說有多重要|什麼最重要|最重要的是什麼)",
        ],
    }

    def __init__(self, language: str = "auto"):
        """Initialize analyzer with language preference."""
        self.language = self._detect_primary_language(language)
        logger.debug(f"SpeakerAnalyzer initialized for language: {self.language}")

    def _detect_primary_language(self, language_code: str) -> str:
        """Detect primary language for pattern matching."""
        if language_code in [
            "cmn-Hant-TW",
            "zh-TW",
            "cmn-Hans-CN",
            "zh-CN",
            "zh",
        ]:
            return "zh"
        elif language_code in ["en-US", "en-GB", "en"]:
            return "en"
        else:
            # Default to English patterns
            return "en"

    def _count_words(self, text: str) -> int:
        """Count words in text, handling different languages."""
        if self.language == "zh":
            # For Chinese, count characters as rough word approximation
            chinese_chars = re.findall(r"[\u4e00-\u9fff]", text)
            return len(chinese_chars)
        else:
            # For English and other languages, split by whitespace
            return len(text.split())

    def _is_question(self, text: str) -> bool:
        """Determine if a text segment is a question."""
        text_lower = text.lower().strip()

        # Get patterns for the current language
        patterns = self.QUESTION_PATTERNS.get(
            self.language, self.QUESTION_PATTERNS["en"]
        )

        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def _is_coaching_question(self, text: str) -> bool:
        """Determine if a text segment contains coaching-style questions."""
        text_lower = text.lower().strip()

        # Get coaching patterns for the current language
        patterns = self.COACHING_PATTERNS.get(
            self.language, self.COACHING_PATTERNS["en"]
        )

        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return True

        return False

    def analyze_speakers(
        self, segments: List[TranscriptSegment]
    ) -> Dict[int, SpeakerStats]:
        """Analyze all speakers in the conversation."""
        speaker_data = {}

        # Collect data for each speaker
        for segment in segments:
            speaker_id = segment.speaker_id

            if speaker_id not in speaker_data:
                speaker_data[speaker_id] = {
                    "segments": [],
                    "total_words": 0,
                    "total_duration": 0,
                    "question_count": 0,
                    "coaching_question_count": 0,
                }

            # Add segment data
            words = self._count_words(segment.content)
            duration = segment.duration_sec
            is_question = self._is_question(segment.content)
            is_coaching = self._is_coaching_question(segment.content)

            speaker_data[speaker_id]["segments"].append(segment)
            speaker_data[speaker_id]["total_words"] += words
            speaker_data[speaker_id]["total_duration"] += duration

            if is_question:
                speaker_data[speaker_id]["question_count"] += 1
            if is_coaching:
                speaker_data[speaker_id]["coaching_question_count"] += 1

        # Create SpeakerStats objects
        stats = {}
        for speaker_id, data in speaker_data.items():
            segment_count = len(data["segments"])
            avg_length = data["total_words"] / max(segment_count, 1)
            statement_count = segment_count - data["question_count"]

            stats[speaker_id] = SpeakerStats(
                speaker_id=speaker_id,
                total_words=data["total_words"],
                total_duration=data["total_duration"],
                segment_count=segment_count,
                question_count=data["question_count"],
                statement_count=statement_count,
                avg_segment_length=avg_length,
            )

        return stats

    def assign_roles(self, segments: List[TranscriptSegment]) -> Dict[int, str]:
        """
        Automatically assign coach/client roles based on conversation patterns.

        Heuristics used:
        1. Speaker with more questions is likely the coach
        2. Speaker with longer responses is likely the client
        3. Speaker with coaching-style language patterns is likely the coach
        4. In case of ambiguity, assign based on speaking time ratio

        Returns:
            Dictionary mapping speaker_id to role ('coach' or 'client')
        """
        if not segments:
            return {}

        # Analyze all speakers
        speaker_stats = self.analyze_speakers(segments)

        if len(speaker_stats) == 1:
            # Only one speaker detected, assign as coach
            speaker_id = list(speaker_stats.keys())[0]
            logger.info(
                f"Single speaker detected, assigning speaker {speaker_id} as coach"
            )
            return {speaker_id: "coach"}

        elif len(speaker_stats) == 2:
            # Two speakers - use heuristics to assign roles
            speakers = list(speaker_stats.items())
            speaker1_id, stats1 = speakers[0]
            speaker2_id, stats2 = speakers[1]

            # Calculate confidence scores for coach assignment
            coach_score_1 = self._calculate_coach_score(stats1)
            coach_score_2 = self._calculate_coach_score(stats2)

            logger.info(
                f"Coach scores: Speaker {speaker1_id} = {coach_score_1:.3f}, Speaker {speaker2_id} = {coach_score_2:.3f}"
            )

            # Assign roles based on scores
            if coach_score_1 > coach_score_2:
                roles = {speaker1_id: "coach", speaker2_id: "client"}
            else:
                roles = {speaker2_id: "coach", speaker1_id: "client"}

            # Log the decision reasoning
            coach_id = speaker1_id if coach_score_1 > coach_score_2 else speaker2_id
            coach_stats = stats1 if coach_score_1 > coach_score_2 else stats2
            stats2 if coach_score_1 > coach_score_2 else stats1

            logger.info(
                f"Assigned speaker {coach_id} as coach: "
                f"{coach_stats.question_count} questions, {coach_stats.question_ratio:.2%} question ratio"
            )

            return roles

        else:
            # More than 2 speakers - assign most question-heavy as coach, others as participants
            # This is a fallback for group coaching scenarios
            speaker_items = list(speaker_stats.items())
            speaker_items.sort(
                key=lambda x: self._calculate_coach_score(x[1]), reverse=True
            )

            roles = {}
            for i, (speaker_id, stats) in enumerate(speaker_items):
                if i == 0:
                    roles[speaker_id] = "coach"
                else:
                    roles[speaker_id] = "client"  # or could be 'participant'

            logger.info(f"Multi-speaker session: assigned {len(roles)} speakers")
            return roles

    def _calculate_coach_score(self, stats: SpeakerStats) -> float:
        """
        Calculate a score indicating likelihood of being the coach.

        Higher score = more likely to be coach

        Key assumptions:
        - Coaches ask more questions
        - Clients typically speak more (longer total duration)
        - Coaches have shorter, more frequent interventions
        """
        score = 0.0

        # Question ratio (coaches ask more questions) - most important factor
        score += stats.question_ratio * 4.0

        # Shorter average segment length (coaches ask concise questions)
        if stats.avg_segment_length < 15:  # Very short segments (questions/prompts)
            score += 1.5
        elif stats.avg_segment_length < 30:  # Short segments
            score += 0.8
        elif stats.avg_segment_length > 40:  # Long segments (client sharing stories)
            score -= 1.0

        # Speaking time ratio (clients typically talk MORE)
        # Less total speaking time favors being the coach
        total_words_penalty = stats.total_words / 1000.0  # Normalize by word count
        if total_words_penalty > 1.0:  # More than 1000 words suggests client
            score -= total_words_penalty * 0.8
        elif total_words_penalty < 0.3:  # Less than 300 words suggests coach
            score += 0.5

        # Segment frequency (coaches make more frequent, shorter interventions)
        if stats.segment_count > 15:  # Many short interventions
            score += 0.5
        elif stats.segment_count > 10:
            score += 0.2

        # Word density per segment (coaches are more concise)
        if stats.avg_segment_length < 10:  # Very concise
            score += 0.3

        return score

    def get_confidence_metrics(
        self, segments: List[TranscriptSegment], roles: Dict[int, str]
    ) -> Dict[str, float]:
        """
        Calculate confidence metrics for the role assignments.

        Returns confidence scores and supporting metrics.
        """
        if not segments or not roles:
            return {"confidence": 0.0}

        stats = self.analyze_speakers(segments)

        # Find coach and client stats
        coach_stats = None
        client_stats = None

        for speaker_id, role in roles.items():
            if role == "coach" and speaker_id in stats:
                coach_stats = stats[speaker_id]
            elif role == "client" and speaker_id in stats:
                client_stats = stats[speaker_id]

        if not coach_stats or not client_stats:
            return {"confidence": 0.5}  # Neutral confidence

        # Calculate confidence based on role differentiation
        question_ratio_diff = coach_stats.question_ratio - client_stats.question_ratio
        avg_length_diff = (
            client_stats.avg_segment_length - coach_stats.avg_segment_length
        )

        confidence = 0.5  # Base confidence

        # Strong indicators increase confidence
        if question_ratio_diff > 0.2:  # Coach asks significantly more questions
            confidence += 0.3
        elif question_ratio_diff > 0.1:
            confidence += 0.15

        if avg_length_diff > 10:  # Client has longer segments
            confidence += 0.2
        elif avg_length_diff > 5:
            confidence += 0.1

        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)

        return {
            "confidence": confidence,
            "coach_question_ratio": coach_stats.question_ratio,
            "client_question_ratio": client_stats.question_ratio,
            "question_ratio_difference": question_ratio_diff,
            "coach_avg_segment_length": coach_stats.avg_segment_length,
            "client_avg_segment_length": client_stats.avg_segment_length,
            "segment_length_difference": avg_length_diff,
        }


def analyze_and_assign_roles(
    segments: List[TranscriptSegment], language: str = "auto"
) -> Tuple[Dict[int, str], Dict[str, float]]:
    """
    Convenience function to analyze speakers and assign roles.

    Args:
        segments: List of transcript segments
        language: Language code for pattern matching

    Returns:
        Tuple of (role_assignments, confidence_metrics)
    """
    analyzer = SpeakerAnalyzer(language)
    roles = analyzer.assign_roles(segments)
    confidence = analyzer.get_confidence_metrics(segments, roles)

    return roles, confidence
