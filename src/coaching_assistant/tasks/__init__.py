"""Celery tasks module."""

from .transcription_tasks import transcribe_audio

__all__ = ["transcribe_audio"]
