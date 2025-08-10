"""Processing status model for detailed session tracking."""

from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from .base import BaseModel


class ProcessingStatus(BaseModel):
    """Detailed processing status tracking for sessions."""
    
    # Foreign key to session
    session_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("session.id", ondelete="CASCADE"), 
        nullable=False,
        index=True
    )
    
    # Status information
    status = Column(String(20), nullable=False, index=True)  # pending, processing, completed, failed
    progress = Column(Integer, default=0)  # 0-100 percentage
    message = Column(Text, nullable=True)  # Human-readable status message
    
    # Progress details
    duration_processed = Column(Integer, default=0)  # Seconds of audio processed
    duration_total = Column(Integer, nullable=True)  # Total seconds of audio
    
    # Time estimates
    started_at = Column(DateTime, nullable=True)  # When processing actually started
    estimated_completion = Column(DateTime, nullable=True)  # Estimated completion time
    
    # Performance metrics
    processing_speed = Column(Float, nullable=True)  # Actual processing speed multiplier (e.g., 4.0 = 4x real-time)
    
    # Relationships
    session = relationship("Session", back_populates="status_history")
    
    def __repr__(self):
        return f"<ProcessingStatus(session_id={self.session_id}, status={self.status}, progress={self.progress}%)>"
    
    @property
    def progress_percentage(self) -> int:
        """Get progress as percentage (0-100)."""
        return max(0, min(100, self.progress or 0))
    
    @property
    def duration_processed_minutes(self) -> float:
        """Get processed duration in minutes."""
        return (self.duration_processed or 0) / 60.0
    
    @property
    def duration_total_minutes(self) -> float:
        """Get total duration in minutes."""
        return (self.duration_total or 0) / 60.0
    
    @property
    def time_remaining_minutes(self) -> float:
        """Estimate time remaining in minutes."""
        if not self.estimated_completion:
            return 0.0
        
        now = datetime.utcnow()
        if self.estimated_completion <= now:
            return 0.0
        
        return (self.estimated_completion - now).total_seconds() / 60.0
    
    def update_progress(self, progress: int, message: str = None, 
                       duration_processed: int = None, estimated_completion: datetime = None):
        """Update progress information."""
        self.progress = max(0, min(100, progress))
        if message:
            self.message = message
        if duration_processed is not None:
            self.duration_processed = duration_processed
        if estimated_completion:
            self.estimated_completion = estimated_completion
        self.updated_at = datetime.utcnow()
    
    def calculate_processing_speed(self) -> float:
        """Calculate current processing speed based on elapsed time."""
        if not self.started_at or not self.duration_processed:
            return 0.0
        
        elapsed_seconds = (datetime.utcnow() - self.started_at).total_seconds()
        if elapsed_seconds <= 0:
            return 0.0
        
        # Processing speed = (audio processed) / (time elapsed)
        return self.duration_processed / elapsed_seconds
    
    def estimate_completion_time(self) -> datetime:
        """Estimate completion time based on current progress."""
        if self.progress >= 100 or not self.duration_total:
            return datetime.utcnow()
        
        # Calculate based on current processing speed
        speed = self.calculate_processing_speed()
        if speed <= 0:
            # Fallback to 4x real-time estimate
            speed = 4.0
        
        remaining_audio = self.duration_total - (self.duration_processed or 0)
        estimated_seconds_remaining = remaining_audio * speed
        
        return datetime.utcnow() + datetime.timedelta(seconds=estimated_seconds_remaining)