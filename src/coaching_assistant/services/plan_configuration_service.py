"""
Plan Configuration Service - Phase 2 Implementation
Provides centralized access to plan configurations from database.
Replaces hardcoded plan limits with database-driven configuration.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..core.database import SessionLocal
from ..core.exceptions import PlanNotFoundError
from ..models.plan_configuration import PlanConfiguration
from ..models.user import UserPlan

logger = logging.getLogger(__name__)


class PlanConfigurationService:
    """
    Service for managing plan configurations from database.
    Provides caching, fallback mechanisms, and validation.
    """

    # Cache timeout in seconds (5 minutes)
    CACHE_TTL = 300

    # Fallback configurations if database is unavailable
    FALLBACK_CONFIGS = {
        UserPlan.FREE: {
            "plan_name": "free",
            "display_name": "免費試用方案",
            "description": "開始您的教練旅程",
            "limits": {
                "max_sessions": -1,
                "max_total_minutes": 200,
                "max_transcription_count": -1,
                "max_file_size_mb": 60,
                "export_formats": ["json", "txt"],
                "concurrent_processing": 1,
                "retention_days": 30,
            },
            "pricing": {
                "monthly_twd": 0,
                "annual_twd": 0,
                "monthly_usd": 0,
                "annual_usd": 0,
                "currency": "TWD",
            },
            "features": {
                "priority_support": False,
                "team_collaboration": False,
                "api_access": False,
                "advanced_analytics": False,
            },
        },
        UserPlan.STUDENT: {
            "plan_name": "student",
            "display_name": "學習方案",
            "description": "學生專屬優惠方案",
            "limits": {
                "max_sessions": -1,
                "max_total_minutes": 500,
                "max_transcription_count": -1,
                "max_file_size_mb": 100,
                "export_formats": ["json", "txt", "vtt", "srt"],
                "concurrent_processing": 2,
                "retention_days": 180,
            },
            "pricing": {
                "monthly_twd": 299,
                "annual_twd": 2990,
                "monthly_usd": 10,
                "annual_usd": 100,
                "currency": "TWD",
            },
            "features": {
                "priority_support": False,
                "team_collaboration": False,
                "api_access": False,
                "advanced_analytics": False,
            },
        },
        UserPlan.PRO: {
            "plan_name": "pro",
            "display_name": "專業方案",
            "description": "專業教練的最佳選擇",
            "limits": {
                "max_sessions": -1,
                "max_total_minutes": 3000,
                "max_transcription_count": -1,
                "max_file_size_mb": 200,
                "export_formats": ["json", "txt", "vtt", "srt", "docx"],
                "concurrent_processing": 3,
                "retention_days": 365,
            },
            "pricing": {
                "monthly_twd": 899,
                "annual_twd": 7641,
                "monthly_usd": 30,
                "annual_usd": 255,
                "currency": "TWD",
            },
            "features": {
                "priority_support": True,
                "team_collaboration": False,
                "api_access": False,
                "advanced_analytics": True,
            },
        },
        UserPlan.COACHING_SCHOOL: {
            "plan_name": "coaching_school",
            "display_name": "認證學校方案",
            "description": "專為 ICF 認證教練學校設計",
            "limits": {
                "max_sessions": -1,
                "max_total_minutes": -1,
                "max_transcription_count": -1,
                "max_file_size_mb": 500,
                "export_formats": [
                    "json",
                    "txt",
                    "vtt",
                    "srt",
                    "docx",
                    "xlsx",
                    "pdf",
                ],
                "concurrent_processing": 10,
                "retention_days": -1,
            },
            "pricing": {
                "monthly_twd": 5000,
                "annual_twd": 42500,
                "monthly_usd": 169,
                "annual_usd": 1436,
                "currency": "TWD",
            },
            "features": {
                "priority_support": True,
                "team_collaboration": True,
                "api_access": True,
                "advanced_analytics": True,
                "custom_branding": True,
                "sso": True,
            },
        },
    }

    def __init__(self, db: Optional[Session] = None):
        """Initialize service with optional database session."""
        self._db = db
        self._cache = {}
        self._cache_timestamp = {}

    def get_db(self) -> Session:
        """Get database session."""
        if self._db:
            return self._db
        return SessionLocal()

    def _is_cache_valid(self, key: str) -> bool:
        """Check if cache entry is still valid."""
        if key not in self._cache_timestamp:
            return False

        import time

        age = time.time() - self._cache_timestamp[key]
        return age < self.CACHE_TTL

    def _set_cache(self, key: str, value: Any):
        """Set cache entry with timestamp."""
        import time

        self._cache[key] = value
        self._cache_timestamp[key] = time.time()

    def _get_from_db(self, plan_type: UserPlan) -> Optional[PlanConfiguration]:
        """Get plan configuration from database."""
        db = self.get_db()
        try:
            config = (
                db.query(PlanConfiguration)
                .filter(
                    PlanConfiguration.plan_type == plan_type,
                    PlanConfiguration.is_active.is_(True),
                )
                .first()
            )
            return config
        except SQLAlchemyError as e:
            logger.error(f"Database error getting plan {plan_type}: {e}")
            return None
        finally:
            if not self._db:  # Only close if we created the session
                db.close()

    def get_plan_config(self, plan_type: UserPlan) -> Dict[str, Any]:
        """
        Get plan configuration by type.
        Uses cache and fallback for reliability.

        Args:
            plan_type: UserPlan enum value

        Returns:
            Dict containing plan configuration

        Raises:
            PlanNotFoundError: If plan type is invalid
        """
        cache_key = f"plan_config_{plan_type.value}"

        # Check cache first
        if self._is_cache_valid(cache_key):
            logger.debug(f"Cache hit for plan {plan_type}")
            return self._cache[cache_key]

        # Try database
        db_config = self._get_from_db(plan_type)

        if db_config:
            # Convert database model to service format
            config = self._convert_db_to_dict(db_config)
            self._set_cache(cache_key, config)
            logger.debug(f"Database hit for plan {plan_type}")
            return config

        # Fall back to hardcoded config
        if plan_type in self.FALLBACK_CONFIGS:
            config = self.FALLBACK_CONFIGS[plan_type].copy()
            logger.warning(f"Using fallback config for plan {plan_type}")
            return config

        # Plan not found anywhere
        logger.error(f"Plan configuration not found: {plan_type}")
        raise PlanNotFoundError(f"Plan {plan_type} not found")

    def _convert_db_to_dict(self, db_config: PlanConfiguration) -> Dict[str, Any]:
        """Convert database model to service dictionary format."""
        return {
            "id": str(db_config.id),
            "plan_name": db_config.plan_name,
            "display_name": db_config.display_name,
            "description": db_config.description,
            "tagline": db_config.tagline,
            "limits": self._normalize_limits(db_config.limits),
            "features": db_config.features or {},
            "pricing": {
                "monthly_twd": (
                    db_config.monthly_price_twd_cents / 100
                    if db_config.monthly_price_twd_cents
                    else 0
                ),
                "annual_twd": (
                    db_config.annual_price_twd_cents / 100
                    if db_config.annual_price_twd_cents
                    else 0
                ),
                "monthly_usd": (
                    db_config.monthly_price_cents / 100
                    if db_config.monthly_price_cents
                    else 0
                ),
                "annual_usd": (
                    db_config.annual_price_cents / 100
                    if db_config.annual_price_cents
                    else 0
                ),
                "currency": db_config.currency or "TWD",
                "annual_discount_percentage": (db_config._calculate_annual_discount()),
                "annual_savings_usd": db_config._calculate_annual_savings(),
            },
            "display": {
                "is_popular": db_config.is_popular or False,
                "is_enterprise": db_config.is_enterprise or False,
                "color_scheme": db_config.color_scheme or "gray",
                "sort_order": db_config.sort_order or 0,
            },
            "status": {
                "is_active": db_config.is_active or True,
                "is_visible": db_config.is_visible or True,
            },
            "extra_data": db_config.extra_data or {},
            "timestamps": {
                "created_at": (
                    db_config.created_at.isoformat() if db_config.created_at else None
                ),
                "updated_at": (
                    db_config.updated_at.isoformat() if db_config.updated_at else None
                ),
            },
        }

    def _normalize_limits(self, limits: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize limits to consistent format."""
        if not limits:
            return {}

        # Ensure consistent key names
        normalized = {}

        # Handle different possible key formats
        key_mappings = {
            "max_sessions": ["max_sessions", "maxSessions"],
            "max_total_minutes": [
                "max_total_minutes",
                "maxTotalMinutes",
                "maxMinutes",
                "max_minutes",
            ],
            "max_transcription_count": [
                "max_transcription_count",
                "maxTranscriptionCount",
                "maxTranscriptions",
            ],
            "max_file_size_mb": [
                "max_file_size_mb",
                "maxFileSizeMb",
                "maxFileSize",
            ],
            "export_formats": ["export_formats", "exportFormats"],
            "concurrent_processing": [
                "concurrent_processing",
                "concurrentProcessing",
                "concurrentJobs",
            ],
            "retention_days": ["retention_days", "retentionDays"],
        }

        for standard_key, possible_keys in key_mappings.items():
            for key in possible_keys:
                if key in limits:
                    normalized[standard_key] = limits[key]
                    break

            # Set defaults if not found
            if standard_key not in normalized:
                defaults = {
                    "max_sessions": -1,
                    "max_total_minutes": 0,
                    "max_transcription_count": -1,
                    "max_file_size_mb": 60,
                    "export_formats": ["json", "txt"],
                    "concurrent_processing": 1,
                    "retention_days": 30,
                }
                normalized[standard_key] = defaults[standard_key]

        return normalized

    def get_all_plans(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all plan configurations.

        Args:
            include_inactive: Whether to include inactive plans

        Returns:
            List of plan configuration dictionaries
        """
        cache_key = f"all_plans_active_{not include_inactive}"

        if self._is_cache_valid(cache_key):
            return self._cache[cache_key]

        db = self.get_db()
        try:
            query = db.query(PlanConfiguration)

            if not include_inactive:
                query = query.filter(PlanConfiguration.is_active.is_(True))

            db_configs = query.order_by(PlanConfiguration.sort_order).all()

            plans = []
            for db_config in db_configs:
                try:
                    plan_dict = self._convert_db_to_dict(db_config)
                    plans.append(plan_dict)
                except Exception as e:
                    logger.error(f"Error converting plan {db_config.plan_name}: {e}")
                    continue

            self._set_cache(cache_key, plans)
            logger.info(f"Retrieved {len(plans)} plans from database")
            return plans

        except SQLAlchemyError as e:
            logger.error(f"Database error getting all plans: {e}")

            # Fallback to all fallback configs
            plans = []
            for plan_type in [
                UserPlan.FREE,
                UserPlan.STUDENT,
                UserPlan.PRO,
                UserPlan.COACHING_SCHOOL,
            ]:
                if plan_type in self.FALLBACK_CONFIGS:
                    plans.append(self.FALLBACK_CONFIGS[plan_type].copy())

            logger.warning(f"Using {len(plans)} fallback plan configurations")
            return plans

        finally:
            if not self._db:
                db.close()

    def get_plan_limits(self, plan_type: UserPlan) -> Dict[str, Any]:
        """
        Get only the limits portion of a plan configuration.
        Used by legacy services that expect limits format.

        Args:
            plan_type: UserPlan enum value

        Returns:
            Dict containing plan limits
        """
        config = self.get_plan_config(plan_type)
        return config.get("limits", {})

    def get_plan_pricing(self, plan_type: UserPlan) -> Dict[str, Any]:
        """
        Get only the pricing portion of a plan configuration.

        Args:
            plan_type: UserPlan enum value

        Returns:
            Dict containing plan pricing
        """
        config = self.get_plan_config(plan_type)
        return config.get("pricing", {})

    def is_feature_available(self, plan_type: UserPlan, feature: str) -> bool:
        """
        Check if a specific feature is available for a plan.

        Args:
            plan_type: UserPlan enum value
            feature: Feature name to check

        Returns:
            True if feature is available, False otherwise
        """
        try:
            config = self.get_plan_config(plan_type)
            features = config.get("features", {})
            limits = config.get("limits", {})

            # Check feature flags
            if feature in features:
                return features[feature]

            # Check derived features from limits
            if feature == "unlimited_sessions":
                return limits.get("max_sessions", 0) == -1
            elif feature == "unlimited_minutes":
                return limits.get("max_total_minutes", 0) == -1
            elif feature == "unlimited_transcriptions":
                return limits.get("max_transcription_count", 0) == -1
            elif feature == "permanent_retention":
                return limits.get("retention_days", 0) == -1
            elif feature.endswith("_export"):
                export_format = feature.replace("_export", "")
                return export_format in limits.get("export_formats", [])

            return False

        except Exception as e:
            logger.error(f"Error checking feature {feature} for plan {plan_type}: {e}")
            return False

    def validate_usage(
        self,
        plan_type: UserPlan,
        action: str,
        current_usage: Dict[str, Any],
        action_params: Dict[str, Any] = None,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate if an action is allowed under plan limits.

        Args:
            plan_type: UserPlan enum value
            action: Action to validate (create_session, transcribe, check_minutes, etc.)
            current_usage: Current user usage counters
            action_params: Parameters for the action (e.g., file_size_mb, duration_min)

        Returns:
            Tuple of (allowed: bool, message: str, limit_info: dict)
        """
        try:
            limits = self.get_plan_limits(plan_type)
            action_params = action_params or {}

            # Phase 2: Only validate minutes and file size
            if action == "check_minutes":
                max_minutes = limits.get("max_total_minutes", 0)
                if max_minutes == -1:  # Unlimited
                    return (
                        True,
                        "Minutes usage allowed (unlimited)",
                        {"type": "minutes", "limit": -1},
                    )

                current_minutes = current_usage.get("minutes", 0)
                requested_minutes = action_params.get("duration_min", 0)
                projected_usage = current_minutes + requested_minutes

                if projected_usage > max_minutes:
                    return (
                        False,
                        f"Monthly minutes limit exceeded ({max_minutes} minutes)",
                        {
                            "type": "minutes",
                            "current": current_minutes,
                            "limit": max_minutes,
                            "requested": requested_minutes,
                            "projected": projected_usage,
                        },
                    )

                return (
                    True,
                    "Minutes usage allowed",
                    {
                        "type": "minutes",
                        "current": current_minutes,
                        "limit": max_minutes,
                        "remaining": max_minutes - projected_usage,
                    },
                )

            elif action == "upload_file":
                max_size = limits.get("max_file_size_mb", 60)
                file_size = action_params.get("file_size_mb", 0)

                if file_size > max_size:
                    return (
                        False,
                        f"File size exceeds limit ({max_size}MB)",
                        {
                            "type": "file_size",
                            "current": file_size,
                            "limit": max_size,
                        },
                    )

                return (
                    True,
                    "File size allowed",
                    {
                        "type": "file_size",
                        "current": file_size,
                        "limit": max_size,
                    },
                )

            elif action == "export_transcript":
                export_format = action_params.get("format", "").lower()
                available_formats = limits.get("export_formats", ["json", "txt"])

                if export_format not in available_formats:
                    return (
                        False,
                        f"Export format '{export_format}' not available",
                        {
                            "type": "export_format",
                            "requested": export_format,
                            "available": available_formats,
                        },
                    )

                return (
                    True,
                    "Export format allowed",
                    {
                        "type": "export_format",
                        "requested": export_format,
                        "available": available_formats,
                    },
                )

            # Phase 2: Sessions and transcriptions are unlimited
            elif action in ["create_session", "transcribe"]:
                return (
                    True,
                    f"{action} allowed (unlimited in Phase 2)",
                    {"type": action, "limit": -1},
                )

            else:
                logger.warning(f"Unknown action for validation: {action}")
                return (
                    True,
                    "Action allowed (unknown action)",
                    {"type": "unknown"},
                )

        except Exception as e:
            logger.error(
                f"Error validating usage for {plan_type}, action {action}: {e}"
            )
            # Fail open - allow action on error
            return (
                True,
                "Validation temporarily unavailable",
                {"type": "error"},
            )

    def get_upgrade_suggestion(
        self, current_plan: UserPlan
    ) -> Optional[Dict[str, Any]]:
        """
        Get upgrade suggestion for current plan.

        Args:
            current_plan: Current UserPlan enum value

        Returns:
            Dict with upgrade suggestion or None if no upgrade available
        """
        upgrade_paths = {
            UserPlan.FREE: UserPlan.STUDENT,
            UserPlan.STUDENT: UserPlan.PRO,
            UserPlan.PRO: UserPlan.COACHING_SCHOOL,
        }

        if current_plan not in upgrade_paths:
            return None

        try:
            suggested_plan = upgrade_paths[current_plan]
            suggested_config = self.get_plan_config(suggested_plan)

            # Build benefits comparison
            current_config = self.get_plan_config(current_plan)
            current_limits = current_config.get("limits", {})
            suggested_limits = suggested_config.get("limits", {})

            benefits = []

            # Compare minutes
            current_minutes = current_limits.get("max_total_minutes", 0)
            suggested_minutes = suggested_limits.get("max_total_minutes", 0)

            if suggested_minutes == -1:
                benefits.append("無限制音檔分鐘數")
            elif current_minutes != -1 and suggested_minutes > current_minutes:
                ratio = (
                    suggested_minutes / current_minutes if current_minutes > 0 else 0
                )
                if ratio >= 2:
                    benefits.append(
                        f"{int(ratio)}x 音檔分鐘數 ({suggested_minutes} 分鐘/月)"
                    )
                else:
                    benefits.append(f"更多音檔分鐘數 ({suggested_minutes} 分鐘/月)")

            # Compare file size
            current_size = current_limits.get("max_file_size_mb", 0)
            suggested_size = suggested_limits.get("max_file_size_mb", 0)
            if suggested_size > current_size:
                benefits.append(f"更大檔案支援 ({suggested_size}MB)")

            # Compare features
            current_features = current_config.get("features", {})
            suggested_features = suggested_config.get("features", {})

            new_features = []
            for feature, available in suggested_features.items():
                if available and not current_features.get(feature, False):
                    feature_names = {
                        "priority_support": "優先客服支援",
                        "advanced_analytics": "進階分析報告",
                        "team_collaboration": "團隊協作功能",
                        "api_access": "API 存取權限",
                        "custom_branding": "客製化品牌",
                        "sso": "單一登入 (SSO)",
                    }
                    if feature in feature_names:
                        new_features.append(feature_names[feature])

            benefits.extend(new_features)

            return {
                "suggested_plan": suggested_plan.value,
                "display_name": suggested_config.get("display_name"),
                "tagline": suggested_config.get("tagline"),
                "benefits": benefits,
                "pricing": suggested_config.get("pricing"),
                "comparison_url": (
                    f"/billing/compare?from={current_plan.value}&to={suggested_plan.value}"
                ),
            }

        except Exception as e:
            logger.error(f"Error getting upgrade suggestion for {current_plan}: {e}")
            return None

    def clear_cache(self):
        """Clear all cached configurations."""
        self._cache.clear()
        self._cache_timestamp.clear()
        logger.info("Plan configuration cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring."""
        import time

        current_time = time.time()

        stats = {
            "cache_size": len(self._cache),
            "valid_entries": 0,
            "expired_entries": 0,
            "oldest_entry_age": 0,
            "newest_entry_age": 0,
        }

        if self._cache_timestamp:
            ages = [current_time - ts for ts in self._cache_timestamp.values()]
            stats["oldest_entry_age"] = max(ages)
            stats["newest_entry_age"] = min(ages)
            stats["valid_entries"] = sum(1 for age in ages if age < self.CACHE_TTL)
            stats["expired_entries"] = len(ages) - stats["valid_entries"]

        return stats


# Global service instance
plan_service = PlanConfigurationService()


def get_plan_service(db: Optional[Session] = None) -> PlanConfigurationService:
    """
    Get plan configuration service instance.

    Args:
        db: Optional database session

    Returns:
        PlanConfigurationService instance
    """
    if db:
        return PlanConfigurationService(db=db)
    return plan_service
