"""
Simple role assignment based on speaking ratio.

This module provides a simplified approach to coach/client role assignment
based primarily on speaking duration and word count ratios.

Future improvements could include:
- NLP-based analysis using libraries like spaCy or NLTK
- LLM-based semantic analysis for more accurate role detection
- Question pattern recognition using advanced NLP techniques
- Sentiment and conversation flow analysis
"""

import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SpeakerMetrics:
    """Basic metrics for a speaker."""

    speaker_id: int
    total_words: int
    total_duration: float
    segment_count: int

    @property
    def speaking_ratio(self) -> float:
        """Ratio of speaking time (used for comparison)."""
        return self.total_duration

    @property
    def word_ratio(self) -> float:
        """Ratio of words spoken (used for comparison)."""
        return self.total_words


class SimpleRoleAssigner:
    """
    Simple role assigner based on speaking ratios.

    Core assumption: In coaching conversations, clients typically speak more
    than coaches. Coaches guide with questions and brief interventions,
    while clients share their stories and thoughts in detail.
    """

    def __init__(self, client_speaking_threshold: float = 0.6):
        """
        Initialize the role assigner.

        Args:
            client_speaking_threshold: Minimum ratio of total speaking time
                                     for a speaker to be considered the client.
                                     Default is 0.6 (60% of conversation).
        """
        self.client_speaking_threshold = client_speaking_threshold
        logger.debug(
            f"SimpleRoleAssigner initialized with threshold: {client_speaking_threshold}"
        )

    def analyze_segments(self, segments: List) -> Dict[int, SpeakerMetrics]:
        """
        Analyze segments to extract speaker metrics.

        Args:
            segments: List of transcript segments with speaker_id, content,
                     start_seconds, and end_seconds

        Returns:
            Dictionary mapping speaker_id to their metrics
        """
        metrics = {}

        for segment in segments:
            speaker_id = segment.speaker_id

            if speaker_id not in metrics:
                metrics[speaker_id] = {
                    "total_words": 0,
                    "total_duration": 0,
                    "segment_count": 0,
                }

            # Calculate segment duration
            duration = segment.end_seconds - segment.start_seconds

            # Count words (simple split for now)
            # For Chinese text, we count characters as a proxy for words
            content = segment.content
            if self._is_chinese_text(content):
                word_count = len([c for c in content if "\u4e00" <= c <= "\u9fff"])
            else:
                word_count = len(content.split())

            metrics[speaker_id]["total_words"] += word_count
            metrics[speaker_id]["total_duration"] += duration
            metrics[speaker_id]["segment_count"] += 1

        # Convert to SpeakerMetrics objects
        return {
            speaker_id: SpeakerMetrics(
                speaker_id=speaker_id,
                total_words=data["total_words"],
                total_duration=data["total_duration"],
                segment_count=data["segment_count"],
            )
            for speaker_id, data in metrics.items()
        }

    def assign_roles(self, segments: List) -> Tuple[Dict[int, str], Dict[str, float]]:
        """
        Assign coach/client roles based on speaking ratios.

        Args:
            segments: List of transcript segments

        Returns:
            Tuple of (role_assignments, confidence_metrics)
            - role_assignments: Dict mapping speaker_id to 'coach' or 'client'
            - confidence_metrics: Dict with confidence scores and ratios
        """
        if not segments:
            logger.warning("No segments provided for role assignment")
            return {}, {"confidence": 0.0, "reason": "no_segments"}

        # Analyze speakers
        speaker_metrics = self.analyze_segments(segments)

        if len(speaker_metrics) == 0:
            logger.warning("No speakers found in segments")
            return {}, {"confidence": 0.0, "reason": "no_speakers"}

        if len(speaker_metrics) == 1:
            # Only one speaker - cannot determine roles
            speaker_id = list(speaker_metrics.keys())[0]
            logger.info(
                f"Only one speaker detected (ID: {speaker_id}), cannot assign roles"
            )
            return {}, {"confidence": 0.0, "reason": "single_speaker"}

        if len(speaker_metrics) == 2:
            # Two speakers - use speaking ratio to determine roles
            speakers = list(speaker_metrics.items())
            speaker1_id, metrics1 = speakers[0]
            speaker2_id, metrics2 = speakers[1]

            # Calculate total duration and words
            total_duration = metrics1.total_duration + metrics2.total_duration
            total_words = metrics1.total_words + metrics2.total_words

            # Calculate ratios for each speaker
            duration_ratio1 = metrics1.total_duration / max(total_duration, 1)
            duration_ratio2 = metrics2.total_duration / max(total_duration, 1)
            word_ratio1 = metrics1.total_words / max(total_words, 1)
            word_ratio2 = metrics2.total_words / max(total_words, 1)

            # Combined ratio (average of duration and word ratios)
            combined_ratio1 = (duration_ratio1 + word_ratio1) / 2
            combined_ratio2 = (duration_ratio2 + word_ratio2) / 2

            # Determine roles based on who speaks more
            if combined_ratio1 > combined_ratio2:
                # Speaker 1 talks more -> likely the client
                roles = {speaker1_id: "client", speaker2_id: "coach"}
                client_ratio = combined_ratio1
                coach_ratio = combined_ratio2
            else:
                # Speaker 2 talks more -> likely the client
                roles = {speaker2_id: "client", speaker1_id: "coach"}
                client_ratio = combined_ratio2
                coach_ratio = combined_ratio1

            # Calculate confidence based on the difference in ratios
            ratio_difference = abs(client_ratio - coach_ratio)

            # Confidence calculation
            if ratio_difference > 0.3:  # Clear difference (e.g., 70/30 split)
                confidence = 0.9
            elif ratio_difference > 0.2:  # Moderate difference (e.g., 60/40 split)
                confidence = 0.7
            elif ratio_difference > 0.1:  # Small difference (e.g., 55/45 split)
                confidence = 0.5
            else:  # Very small difference
                confidence = 0.3

            # Log the decision
            logger.info(
                f"Role assignment based on speaking ratios:\n"
                f"  Client (ID {[k for k,v in roles.items() if v=='client'][0]}): "
                f"{client_ratio:.1%} of conversation\n"
                f"  Coach (ID {[k for k,v in roles.items() if v=='coach'][0]}): "
                f"{coach_ratio:.1%} of conversation\n"
                f"  Confidence: {confidence:.1%}"
            )

            # Return roles and detailed metrics
            confidence_metrics = {
                "confidence": confidence,
                "client_speaking_ratio": client_ratio,
                "coach_speaking_ratio": coach_ratio,
                "ratio_difference": ratio_difference,
                "method": "speaking_ratio",
                "speaker_count": len(speaker_metrics),
            }

            return roles, confidence_metrics

        else:
            # More than 2 speakers - find the one who speaks most as client
            # This is a simplified approach for group sessions
            speakers_sorted = sorted(
                speaker_metrics.items(), key=lambda x: x[1].total_duration, reverse=True
            )

            # Assign the most talkative as client, others as participants
            roles = {}
            for i, (speaker_id, metrics) in enumerate(speakers_sorted):
                if i == 0:
                    roles[speaker_id] = "client"  # Most talkative
                elif i == len(speakers_sorted) - 1:
                    roles[speaker_id] = "coach"  # Least talkative
                else:
                    roles[speaker_id] = "participant"  # Others

            logger.info(
                f"Multi-speaker session: {len(speaker_metrics)} speakers detected"
            )

            return roles, {
                "confidence": 0.5,  # Lower confidence for multi-speaker
                "method": "speaking_ratio_multi",
                "speaker_count": len(speaker_metrics),
            }

    def _is_chinese_text(self, text: str) -> bool:
        """Check if text contains Chinese characters."""
        return any("\u4e00" <= c <= "\u9fff" for c in text)


# Convenience function for backward compatibility
def assign_roles_simple(
    segments: List, threshold: float = 0.6
) -> Tuple[Dict[int, str], Dict[str, float]]:
    """
    Simple convenience function to assign roles based on speaking ratio.

    Args:
        segments: List of transcript segments
        threshold: Client speaking threshold (default 0.6)

    Returns:
        Tuple of (role_assignments, confidence_metrics)
    """
    assigner = SimpleRoleAssigner(client_speaking_threshold=threshold)
    return assigner.assign_roles(segments)
