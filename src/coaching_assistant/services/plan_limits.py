"""
Plan limits configuration and management.
Defines limits for different subscription tiers.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass


class PlanName(Enum):
    """Available subscription plans."""
    FREE = "free"
    PRO = "pro"
    ENTERPRISE = "enterprise"


@dataclass
class PlanLimit:
    """Configuration for a plan's usage limits."""
    max_sessions: int = -1  # -1 means unlimited
    max_transcriptions: int = -1
    max_minutes: int = -1
    max_file_size_mb: int = 500
    export_formats: list = None
    concurrent_processing: int = 1
    retention_days: int = 30
    
    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["txt", "json"]


class PlanLimits:
    """Central configuration for all plan limits."""
    
    LIMITS = {
        PlanName.FREE: PlanLimit(
            max_sessions=3,
            max_transcriptions=3,
            max_minutes=180,  # 3 hours
            max_file_size_mb=100,
            export_formats=["txt", "json"],
            concurrent_processing=1,
            retention_days=7
        ),
        PlanName.PRO: PlanLimit(
            max_sessions=50,
            max_transcriptions=50,
            max_minutes=3000,  # 50 hours
            max_file_size_mb=500,
            export_formats=["txt", "json", "docx", "pdf", "srt", "vtt"],
            concurrent_processing=3,
            retention_days=90
        ),
        PlanName.ENTERPRISE: PlanLimit(
            max_sessions=-1,  # Unlimited
            max_transcriptions=-1,
            max_minutes=-1,
            max_file_size_mb=2000,
            export_formats=["txt", "json", "docx", "pdf", "srt", "vtt", "xlsx"],
            concurrent_processing=10,
            retention_days=365
        )
    }
    
    @classmethod
    def get_plan_limit(cls, plan_name: str) -> PlanLimit:
        """Get limits for a specific plan."""
        try:
            plan_enum = PlanName(plan_name.lower())
            return cls.LIMITS.get(plan_enum, cls.LIMITS[PlanName.FREE])
        except ValueError:
            # Default to free plan if invalid plan name
            return cls.LIMITS[PlanName.FREE]
    
    @classmethod
    def get_upgrade_suggestion(cls, current_plan: str) -> Optional[Dict[str, Any]]:
        """Get upgrade suggestion based on current plan."""
        try:
            current = PlanName(current_plan.lower())
            
            if current == PlanName.FREE:
                return {
                    "plan_id": PlanName.PRO.value,
                    "display_name": "Pro Plan",
                    "benefits": [
                        "50 sessions per month",
                        "50 hours of transcription",
                        "500MB file uploads",
                        "Export to DOCX, PDF, SRT formats",
                        "90-day retention"
                    ]
                }
            elif current == PlanName.PRO:
                return {
                    "plan_id": PlanName.ENTERPRISE.value,
                    "display_name": "Enterprise Plan",
                    "benefits": [
                        "Unlimited sessions",
                        "Unlimited transcription",
                        "2GB file uploads",
                        "All export formats including XLSX",
                        "1-year retention",
                        "Priority support"
                    ]
                }
            else:
                return None
                
        except ValueError:
            return None
    
    @classmethod
    def format_limit_message(cls, limit_type: str, current: int, limit: int) -> str:
        """Format a user-friendly limit message."""
        if limit == -1:
            return f"You have used {current} {limit_type} (unlimited)"
        
        remaining = max(0, limit - current)
        percentage = min(100, int((current / limit) * 100))
        
        if remaining == 0:
            return f"You have reached your limit of {limit} {limit_type}"
        elif percentage >= 90:
            return f"Warning: Only {remaining} {limit_type} remaining out of {limit}"
        elif percentage >= 80:
            return f"You have used {current} out of {limit} {limit_type} ({percentage}%)"
        else:
            return f"{current}/{limit} {limit_type} used"