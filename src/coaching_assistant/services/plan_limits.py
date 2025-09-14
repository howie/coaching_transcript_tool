"""
Plan limits configuration and management.
Defines limits for different subscription tiers.
"""

from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
import logging

# Import the centralized plan configuration service
from .plan_configuration_service import PlanConfigurationService
from ..models.user import UserPlan

logger = logging.getLogger(__name__)


class PlanName(Enum):
    """Available subscription plans."""

    FREE = "free"
    STUDENT = "student"
    PRO = "pro"
    ENTERPRISE = "enterprise"  # Deprecated
    COACHING_SCHOOL = "coaching_school"


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
    
    def __init__(self):
        """Initialize with PlanConfigurationService."""
        self.plan_service = PlanConfigurationService()
        
        # Fallback limits for backward compatibility (Phase 2 Configuration)
        # Only minutes-based limits, removed session/transcription limits
        self._FALLBACK_LIMITS = {
        PlanName.FREE: PlanLimit(
            max_sessions=-1,  # No session limit
            max_transcriptions=-1,  # No transcription limit
            max_minutes=200,  # 200 minutes per month
            max_file_size_mb=60,  # 60MB per file
            export_formats=["txt", "json"],
            concurrent_processing=1,
            retention_days=30,
            monthly_price_twd=0,
            annual_price_twd=0,
            monthly_price_usd=0,
            annual_price_usd=0,
        ),
        PlanName.STUDENT: PlanLimit(
            max_sessions=-1,  # No session limit
            max_transcriptions=-1,  # No transcription limit
            max_minutes=500,  # 500 minutes per month
            max_file_size_mb=100,  # 100MB per file
            export_formats=["txt", "json", "vtt", "srt"],
            concurrent_processing=2,
            retention_days=180,  # 6 months
            monthly_price_twd=299,  # 299 TWD/month
            annual_price_twd=3000,  # 3000 TWD/year (10 months price)
            monthly_price_usd=10,
            annual_price_usd=100,
        ),
        PlanName.PRO: PlanLimit(
            max_sessions=-1,  # No session limit
            max_transcriptions=-1,  # No transcription limit
            max_minutes=3000,  # 3000 minutes per month (50 hours)
            max_file_size_mb=200,  # 200MB per file
            export_formats=["txt", "json", "vtt", "srt", "docx"],
            concurrent_processing=3,
            retention_days=365,  # 1 year
            monthly_price_twd=899,  # 899 TWD/month
            annual_price_twd=8990,  # 8990 TWD/year (10 months price)
            monthly_price_usd=29,
            annual_price_usd=290,
        ),
        # Keep ENTERPRISE for backward compatibility
        PlanName.ENTERPRISE: PlanLimit(
            max_sessions=-1,  # No session limit
            max_transcriptions=-1,  # No transcription limit
            max_minutes=1500,  # Legacy limit (25 hours)
            max_file_size_mb=500,  # 500MB per file
            export_formats=["txt", "json", "vtt", "srt", "docx", "xlsx"],
            concurrent_processing=5,
            retention_days=-1,  # Unlimited retention
            monthly_price_twd=3040,  # ~$99 USD
            annual_price_twd=30400,  # ~$990 USD
            monthly_price_usd=99,
            annual_price_usd=990,
        ),
        PlanName.COACHING_SCHOOL: PlanLimit(
            max_sessions=-1,  # No session limit
            max_transcriptions=-1,  # No transcription limit
            max_minutes=-1,  # Unlimited minutes
            max_file_size_mb=1000,  # 1GB per file
            export_formats=["txt", "json", "vtt", "srt", "docx", "xlsx", "pdf"],
            concurrent_processing=10,
            retention_days=-1,  # Unlimited retention
            monthly_price_twd=5000,  # Custom pricing
            annual_price_twd=50000,
            monthly_price_usd=150,
            annual_price_usd=1500,
        ),
    }

    def _convert_db_config_to_plan_limit(self, config: Dict[str, Any]) -> PlanLimit:
        """Convert database configuration to PlanLimit object."""
        limits = config.get('limits', {})
        pricing = config.get('pricing', {})  # Get pricing from nested dictionary
        
        return PlanLimit(
            max_sessions=limits.get('max_sessions', -1),
            max_transcriptions=limits.get('max_transcription_count', -1),
            max_minutes=limits.get('max_total_minutes', -1),
            max_file_size_mb=limits.get('max_file_size_mb', 60),
            export_formats=limits.get('export_formats', ['txt', 'json']),
            concurrent_processing=limits.get('concurrent_processing', 1),
            retention_days=limits.get('retention_days', 30),
            # Convert from TWD/USD to cents (multiply by 100)
            monthly_price_twd=int(pricing.get('monthly_twd', 0) * 100),
            annual_price_twd=int(pricing.get('annual_twd', 0) * 100),
            monthly_price_usd=int(pricing.get('monthly_usd', 0) * 100),
            annual_price_usd=int(pricing.get('annual_usd', 0) * 100),
        )

    def _map_plan_name_to_user_plan(self, plan_name) -> UserPlan:
        """Map PlanName enum to UserPlan enum."""
        mapping = {
            PlanName.FREE: UserPlan.FREE,
            PlanName.STUDENT: UserPlan.STUDENT,
            PlanName.PRO: UserPlan.PRO,
            PlanName.ENTERPRISE: UserPlan.ENTERPRISE,
            PlanName.COACHING_SCHOOL: UserPlan.COACHING_SCHOOL,
        }
        return mapping.get(plan_name, UserPlan.FREE)

    def get_plan_limit(self, plan_name) -> PlanLimit:
        """Get limits for a specific plan from database or fallback."""
        try:
            # Handle both string and enum inputs
            if hasattr(plan_name, "value"):
                # It's already an enum, use its value
                plan_str = plan_name.value.lower()
            elif hasattr(plan_name, "lower"):
                # It's a string
                plan_str = plan_name.lower()
            else:
                # Convert to string and lowercase
                plan_str = str(plan_name).lower()

            plan_enum = PlanName(plan_str)
            
            # Try to get from database first
            try:
                user_plan = self._map_plan_name_to_user_plan(plan_enum)
                db_config = self.plan_service.get_plan_config(user_plan)
                logger.info(f"📋 Retrieved plan config for {plan_name} from database")
                return self._convert_db_config_to_plan_limit(db_config)
            except Exception as e:
                logger.warning(f"⚠️ Failed to get plan from database for {plan_name}: {e}")
                logger.info(f"🔄 Falling back to hardcoded limits for {plan_name}")
                # Fallback to hardcoded limits
                return self._FALLBACK_LIMITS.get(plan_enum, self._FALLBACK_LIMITS[PlanName.FREE])
                
        except (ValueError, AttributeError) as e:
            logger.warning(f"⚠️ Invalid plan name {plan_name}: {e}")
            # Default to free plan if invalid plan name
            return self._FALLBACK_LIMITS[PlanName.FREE]

    def from_user_plan(self, user_plan) -> PlanLimit:
        """Get plan limits from user's plan (string or enum). Alias for get_plan_limit."""
        return self.get_plan_limit(user_plan or "free")

    def get_upgrade_suggestion(
        self, current_plan: str
    ) -> Optional[Dict[str, Any]]:
        """Get upgrade suggestion based on current plan from database or fallback."""
        try:
            current = PlanName(current_plan.lower())
            
            # Try to get from database first
            try:
                user_plan = self._map_plan_name_to_user_plan(current)
                upgrade_suggestion = self.plan_service.get_upgrade_suggestion(user_plan)
                if upgrade_suggestion:
                    logger.info(f"📋 Retrieved upgrade suggestion for {current_plan} from database")
                    return upgrade_suggestion
            except Exception as e:
                logger.warning(f"⚠️ Failed to get upgrade suggestion from database: {e}")
                logger.info(f"🔄 Using fallback upgrade suggestions")

            # Fallback upgrade suggestions (Phase 2 - updated to minutes-only)
            if current == PlanName.FREE:
                return {
                    "plan_id": PlanName.PRO.value,
                    "display_name": "專業方案",
                    "benefits": [
                        "每月 3000 分鐘音檔處理",
                        "200MB 檔案上傳",
                        "支援 DOCX、SRT 匯出格式",
                        "1 年資料保留",
                        "優先支援",
                    ],
                }
            elif current == PlanName.STUDENT:
                return {
                    "plan_id": PlanName.PRO.value,
                    "display_name": "專業方案",
                    "benefits": [
                        "6 倍音檔分鐘數 (3000 vs 500)",
                        "200MB 檔案上傳 (vs 100MB)",
                        "支援更多匯出格式",
                        "1 年資料保留 (vs 6個月)",
                        "優先支援",
                    ],
                }
            elif current == PlanName.PRO:
                return {
                    "plan_id": PlanName.COACHING_SCHOOL.value,
                    "display_name": "認證學校方案",
                    "benefits": [
                        "無限音檔分鐘數",
                        "1GB 檔案上傳",
                        "所有匯出格式包含 PDF",
                        "永久資料保留",
                        "團隊協作功能",
                        "API 存取權限",
                    ],
                }
            else:
                return None

        except ValueError:
            return None

    @staticmethod
    def format_limit_message(
        limit_type: str, current: int, limit: int
    ) -> str:
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


# Global instance for backward compatibility
_global_plan_limits = None

def get_global_plan_limits() -> PlanLimits:
    """Get global PlanLimits instance (singleton pattern)."""
    global _global_plan_limits
    if _global_plan_limits is None:
        _global_plan_limits = PlanLimits()
    return _global_plan_limits
