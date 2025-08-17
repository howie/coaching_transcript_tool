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
    monthly_price_twd: int = 0
    annual_price_twd: int = 0
    monthly_price_usd: int = 0
    annual_price_usd: int = 0
    
    def __post_init__(self):
        if self.export_formats is None:
            self.export_formats = ["txt", "json"]


class PlanLimits:
    """Central configuration for all plan limits."""
    
    # UPDATED PLAN LIMITS - Current production configuration
    LIMITS = {
        PlanName.FREE: PlanLimit(
            max_sessions=10,       # Updated: 10 sessions per month
            max_transcriptions=5,  # Updated: 5 transcriptions per month  
            max_minutes=200,       # Updated: 200 min of transcription per month
            max_file_size_mb=60,   # Updated: up to 40 min per recording (~60MB)
            export_formats=["txt", "json"],
            concurrent_processing=1,
            retention_days=30,
            monthly_price_twd=0,
            annual_price_twd=0,
            monthly_price_usd=0,
            annual_price_usd=0
        ),
        PlanName.PRO: PlanLimit(
            max_sessions=25,       # BETA: Reduced from 100 for safety
            max_transcriptions=50, # BETA: Reduced from 200 for safety
            max_minutes=300,       # BETA: Reduced from 1200 for safety (5 hours)
            max_file_size_mb=100,  # BETA: Reduced from 200MB for safety
            export_formats=["txt", "json", "vtt", "srt"],
            concurrent_processing=2,
            retention_days=365,
            monthly_price_twd=890,  # ~$29 USD
            annual_price_twd=8900,  # ~$290 USD 
            monthly_price_usd=29,
            annual_price_usd=290
        ),
        PlanName.ENTERPRISE: PlanLimit(
            max_sessions=500,      # BETA: Conservative limit (not unlimited)
            max_transcriptions=1000, # BETA: Conservative limit  
            max_minutes=1500,      # BETA: Conservative limit (25 hours)
            max_file_size_mb=500,  # BETA: Conservative limit
            export_formats=["txt", "json", "vtt", "srt", "docx", "xlsx"],
            concurrent_processing=5,
            retention_days=-1,     # Unlimited retention
            monthly_price_twd=3040, # ~$99 USD
            annual_price_twd=30400, # ~$990 USD
            monthly_price_usd=99,
            annual_price_usd=50
        )
    }
    
    @classmethod
    def get_plan_limit(cls, plan_name) -> PlanLimit:
        """Get limits for a specific plan."""
        try:
            # Handle both string and enum inputs
            if hasattr(plan_name, 'value'):
                # It's already an enum, use its value
                plan_str = plan_name.value.lower()
            elif hasattr(plan_name, 'lower'):
                # It's a string
                plan_str = plan_name.lower()
            else:
                # Convert to string and lowercase
                plan_str = str(plan_name).lower()
                
            plan_enum = PlanName(plan_str)
            return cls.LIMITS.get(plan_enum, cls.LIMITS[PlanName.FREE])
        except (ValueError, AttributeError):
            # Default to free plan if invalid plan name
            return cls.LIMITS[PlanName.FREE]
    
    @classmethod
    def from_user_plan(cls, user_plan) -> PlanLimit:
        """Get plan limits from user's plan (string or enum). Alias for get_plan_limit."""
        return cls.get_plan_limit(user_plan or 'free')
    
    @classmethod
    def get_upgrade_suggestion(cls, current_plan: str) -> Optional[Dict[str, Any]]:
        """Get upgrade suggestion based on current plan."""
        try:
            current = PlanName(current_plan.lower())
            
            if current == PlanName.FREE:
                return {
                    "plan_id": PlanName.PRO.value,
                    "display_name": "專業版",
                    "benefits": [
                        "每月 50 個會談",
                        "每月 50 小時轉錄額度",
                        "500MB 檔案上傳",
                        "支援 DOCX、PDF、SRT 匯出格式",
                        "90 天資料保留"
                    ]
                }
            elif current == PlanName.PRO:
                return {
                    "plan_id": PlanName.ENTERPRISE.value,
                    "display_name": "企業版",
                    "benefits": [
                        "無限會談數",
                        "無限轉錄額度",
                        "2GB 檔案上傳",
                        "所有匯出格式包含 XLSX",
                        "1 年資料保留",
                        "優先支援"
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