"""Transcript upload use cases following Clean Architecture principles.

This module contains business logic for uploading and processing transcript files,
creating transcription sessions, and linking them to coaching sessions.
"""

import logging
import re
from dataclasses import dataclass
from typing import List, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime

from ..models.transcript import TranscriptSegment, SpeakerRole
from ..models.session import Session as TranscriptionSession, SessionStatus
from ..models.coaching_session import CoachingSession
from ..repositories.ports import (
    CoachingSessionRepoPort,
    SessionRepoPort,
    TranscriptRepoPort,
    SpeakerRoleRepoPort,
)

logger = logging.getLogger(__name__)


@dataclass
class TranscriptUploadResult:
    """Result of transcript upload operation."""

    transcription_session_id: UUID
    segments_count: int
    total_duration: float
    speaker_roles_created: int


@dataclass
class ParsedSegment:
    """Parsed segment data before domain model creation."""

    start_seconds: float
    end_seconds: float
    content: str
    speaker_id: int
    speaker_role: str
    speaker_name: Optional[str] = None


class TranscriptParsingService:
    """Service for parsing VTT and SRT transcript files."""

    def parse_vtt_content(self, content: str, speaker_role_mapping: Dict[str, str] = None) -> List[ParsedSegment]:
        """Parse VTT file content and return segments."""
        segments = []
        lines = content.strip().split("\n")

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Skip header and empty lines
            if line == "WEBVTT" or line == "" or line.startswith("NOTE"):
                i += 1
                continue

            # Look for timestamp line
            if "-->" in line:
                timestamp_match = self._parse_timestamp_line(line)
                if timestamp_match:
                    start_time, end_time = timestamp_match

                    # Get the content (next line)
                    i += 1
                    if i < len(lines):
                        content_line = lines[i].strip()
                        parsed_segment = self._parse_content_line(
                            content_line, start_time, end_time, speaker_role_mapping
                        )
                        if parsed_segment:
                            segments.append(parsed_segment)
                            logger.debug(
                                f"Parsed VTT segment: {start_time:.2f}-{end_time:.2f}s, "
                                f"speaker_id: {parsed_segment.speaker_id}, content: {parsed_segment.content[:50]}..."
                            )
            i += 1

        return segments

    def parse_srt_content(self, content: str, speaker_role_mapping: Dict[str, str] = None) -> List[ParsedSegment]:
        """Parse SRT file content and return segments."""
        segments = []

        # Split by double newline to get individual subtitle blocks
        blocks = re.split(r"\n\s*\n", content.strip())

        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue

            # Parse timestamp (line 1)
            timestamp_line = lines[1].strip()
            timestamp_match = self._parse_timestamp_line(timestamp_line)

            if timestamp_match:
                start_time, end_time = timestamp_match

                # Content (lines 2+)
                content_lines = lines[2:]
                content_text = " ".join(content_lines).strip()

                parsed_segment = self._parse_content_line(
                    content_text, start_time, end_time, speaker_role_mapping
                )
                if parsed_segment:
                    segments.append(parsed_segment)
                    logger.debug(
                        f"Parsed SRT segment: {start_time:.2f}-{end_time:.2f}s, "
                        f"speaker_id: {parsed_segment.speaker_id}, content: {parsed_segment.content[:50]}..."
                    )

        return segments

    def _parse_timestamp_line(self, line: str) -> Optional[tuple[float, float]]:
        """Parse timestamp line and return start/end times in seconds."""
        timestamp_patterns = [
            r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})",  # HH:MM:SS.mmm
            r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})",  # HH:MM:SS,mmm (SRT format)
            r"(\d{1,2}:\d{2}:\d{2}\.\d{3}) --> (\d{1,2}:\d{2}:\d{2}\.\d{3})",  # H:MM:SS.mmm
            r"(\d{1,2}:\d{2}:\d{2}) --> (\d{1,2}:\d{2}:\d{2})",  # H:MM:SS (no milliseconds)
        ]

        for pattern in timestamp_patterns:
            timestamp_match = re.match(pattern, line)
            if timestamp_match:
                try:
                    start_time = self._parse_timestamp(
                        timestamp_match.group(1).replace(",", ".")
                    )
                    end_time = self._parse_timestamp(
                        timestamp_match.group(2).replace(",", ".")
                    )
                    return start_time, end_time
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse timestamp: {line}, error: {e}")
                    break

        return None

    def _parse_content_line(
        self,
        content_line: str,
        start_time: float,
        end_time: float,
        speaker_role_mapping: Dict[str, str] = None
    ) -> Optional[ParsedSegment]:
        """Parse content line and extract speaker info."""
        speaker_id = 1
        content_text = content_line
        speaker_key = None
        speaker_name = None

        # Format 1: VTT format like "<v jolly shih>content</v>" or "<v Speaker>content</v>"
        speaker_match = re.match(r"<v\s+([^>]+)>\s*(.*?)(?:</v>)?$", content_line)
        if speaker_match:
            speaker_name = speaker_match.group(1).strip()
            content_text = speaker_match.group(2)
            # Create speaker key matching frontend format
            normalized_name = re.sub(
                r"[^\w_]", "", speaker_name.lower().replace(" ", "_")
            )
            speaker_key = f"speaker_{normalized_name}"

        # Format 2: Simple prefix format like "Coach: content" or "Client: content"
        elif ":" in content_line:
            prefix_match = re.match(r"^([^:]+):\s*(.+)$", content_line)
            if prefix_match:
                speaker_name = prefix_match.group(1).strip()
                content_text = prefix_match.group(2).strip()
                normalized_name = re.sub(
                    r"[^\w_]", "", speaker_name.lower().replace(" ", "_")
                )
                speaker_key = f"speaker_{normalized_name}"

        # Apply role mapping if provided
        final_speaker_id = speaker_id
        final_speaker_role = "coach"  # default

        if speaker_role_mapping and speaker_key:
            final_speaker_role = speaker_role_mapping.get(speaker_key, "coach")
            final_speaker_id = 1 if final_speaker_role == "coach" else 2
            logger.info(
                f"Applied role mapping: {speaker_key} -> {final_speaker_role} (speaker_id: {final_speaker_id})"
            )
        elif speaker_name:
            # Fallback to name-based assignment when no role mapping is provided
            if any(keyword in speaker_name.lower() for keyword in ["client", "客戶", "學員"]):
                final_speaker_id = 2
                final_speaker_role = "client"
            elif any(keyword in speaker_name.lower() for keyword in ["coach", "教練", "老師"]):
                final_speaker_id = 1
                final_speaker_role = "coach"
            else:
                final_speaker_id = 1  # Default to coach if unclear
                final_speaker_role = "coach"

            logger.info(
                f"Name-based assignment: {speaker_name} -> {final_speaker_role} (speaker_id: {final_speaker_id})"
            )

        return ParsedSegment(
            start_seconds=start_time,
            end_seconds=end_time,
            content=content_text,
            speaker_id=final_speaker_id,
            speaker_role=final_speaker_role,
            speaker_name=speaker_name,
        )

    def _parse_timestamp(self, timestamp_str: str) -> float:
        """Convert timestamp string to seconds."""
        time_parts = timestamp_str.split(":")
        if len(time_parts) != 3:
            raise ValueError(f"Invalid timestamp format: {timestamp_str}")

        try:
            hours = int(time_parts[0])
            minutes = int(time_parts[1])
            seconds_str = time_parts[2]

            # Handle seconds with milliseconds
            if "." in seconds_str:
                seconds_part, milliseconds_part = seconds_str.split(".")
                seconds = int(seconds_part)
                # Pad or truncate milliseconds to 3 digits
                milliseconds_part = milliseconds_part.ljust(3, "0")[:3]
                milliseconds = int(milliseconds_part)
                total_seconds = hours * 3600 + minutes * 60 + seconds + milliseconds / 1000
            else:
                total_seconds = hours * 3600 + minutes * 60 + int(seconds_str)

            return total_seconds
        except (ValueError, IndexError) as e:
            raise ValueError(f"Failed to parse timestamp '{timestamp_str}': {e}")


class TranscriptUploadUseCase:
    """Use case for uploading transcript files to coaching sessions."""

    def __init__(
        self,
        coaching_session_repo: CoachingSessionRepoPort,
        session_repo: SessionRepoPort,
        transcript_repo: TranscriptRepoPort,
        speaker_role_repo: SpeakerRoleRepoPort,
    ):
        """Initialize use case with repository dependencies."""
        self.coaching_session_repo = coaching_session_repo
        self.session_repo = session_repo
        self.transcript_repo = transcript_repo
        self.speaker_role_repo = speaker_role_repo
        self.parser = TranscriptParsingService()

    def upload_transcript(
        self,
        coaching_session_id: UUID,
        user_id: UUID,
        file_content: str,
        file_name: str,
        speaker_role_mapping: Dict[str, str] = None,
        convert_to_traditional_chinese: bool = False,
    ) -> TranscriptUploadResult:
        """Upload and process a transcript file for a coaching session.

        Args:
            coaching_session_id: UUID of the coaching session
            user_id: UUID of the user uploading the transcript
            file_content: Content of the transcript file
            file_name: Name of the uploaded file
            speaker_role_mapping: Optional mapping of speaker IDs to roles
            convert_to_traditional_chinese: Whether to convert to traditional Chinese

        Returns:
            TranscriptUploadResult with details of the upload

        Raises:
            ValueError: If coaching session not found or not owned by user
            ValueError: If file format is not supported or parsing fails
        """
        logger.info(
            f"🔍 Starting transcript upload: session_id={coaching_session_id}, "
            f"user_id={user_id}, filename={file_name}"
        )

        # Verify coaching session exists and belongs to user
        coaching_session = self.coaching_session_repo.get_with_ownership_check(
            coaching_session_id, user_id
        )
        if not coaching_session:
            raise ValueError(f"Coaching session {coaching_session_id} not found or not accessible")

        # Parse transcript content based on file extension
        file_extension = file_name.lower().split(".")[-1] if "." in file_name else ""

        if file_extension == "vtt":
            parsed_segments = self.parser.parse_vtt_content(file_content, speaker_role_mapping)
        elif file_extension == "srt":
            parsed_segments = self.parser.parse_srt_content(file_content, speaker_role_mapping)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Only VTT and SRT files are supported.")

        if not parsed_segments:
            raise ValueError("No valid segments found in the transcript file")

        # Calculate total duration
        total_duration = max(segment.end_seconds for segment in parsed_segments) if parsed_segments else 0

        # Create transcription session
        transcription_session_id = uuid4()
        transcription_session = TranscriptionSession(
            id=transcription_session_id,
            user_id=user_id,
            title=f"Manual Upload - {coaching_session.session_date}",
            status=SessionStatus.COMPLETED,
            language="auto",  # Will be determined from content
            duration_seconds=int(total_duration),
            audio_filename=file_name.replace(".vtt", ".manual").replace(".srt", ".manual"),
        )

        # Save transcription session
        saved_session = self.session_repo.save(transcription_session)

        # Convert parsed segments to domain models
        transcript_segments = []
        speaker_roles_to_create = set()

        for parsed_segment in parsed_segments:
            segment = TranscriptSegment(
                id=uuid4(),
                session_id=transcription_session_id,
                speaker_id=parsed_segment.speaker_id,
                start_seconds=parsed_segment.start_seconds,
                end_seconds=parsed_segment.end_seconds,
                content=parsed_segment.content,
                confidence=1.0,  # Manual upload, assume high confidence
                speaker_role=SpeakerRole.COACH if parsed_segment.speaker_role == "coach" else SpeakerRole.CLIENT,
            )
            transcript_segments.append(segment)
            speaker_roles_to_create.add((parsed_segment.speaker_id, parsed_segment.speaker_role))

        # Save transcript segments
        saved_segments = self.transcript_repo.save_segments(transcript_segments)

        # Create speaker role assignments
        # Note: This will need to be implemented when SpeakerRoleRepoPort is available
        speaker_roles_created = len(speaker_roles_to_create)
        logger.info(f"Created {speaker_roles_created} speaker role assignments")

        # Update coaching session to reference the transcription session
        coaching_session.transcription_session_id = str(transcription_session_id)
        updated_coaching_session = self.coaching_session_repo.save(coaching_session)

        logger.info(
            f"✅ Successfully uploaded transcript: {len(transcript_segments)} segments, "
            f"{total_duration:.2f}s duration"
        )

        return TranscriptUploadResult(
            transcription_session_id=transcription_session_id,
            segments_count=len(transcript_segments),
            total_duration=total_duration,
            speaker_roles_created=speaker_roles_created,
        )