"""
Usage tracking service for monitoring and managing user plan usage.
Handles incrementing counters, checking limits, and resetting monthly usage.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

import redis
from sqlalchemy import text
from sqlalchemy.orm import Session

from coaching_assistant.core.config import settings
from coaching_assistant.models.user import User

logger = logging.getLogger(__name__)


class UsageTracker:
    """Service for tracking and managing user usage against plan limits."""

    def __init__(self, db_session: Session, redis_client: Optional[redis.Redis] = None):
        """
        Initialize usage tracker with database session and optional Redis client.

        Args:
            db_session: SQLAlchemy database session
            redis_client: Optional Redis client for caching
        """
        self.db = db_session
        self.redis = redis_client or self._get_redis_client()
        self.cache_ttl = 300  # 5 minutes cache TTL

    def _get_redis_client(self) -> Optional[redis.Redis]:
        """Get Redis client if available."""
        try:
            if hasattr(settings, "REDIS_URL") and settings.REDIS_URL:
                return redis.from_url(settings.REDIS_URL, decode_responses=True)
        except Exception as e:
            logger.warning(f"Redis not available, using database only: {e}")
        return None

    def get_current_usage(self, user_id: str) -> Dict[str, int]:
        """
        Get current usage statistics for a user.

        Args:
            user_id: User ID to get usage for

        Returns:
            Dictionary with usage metrics
        """
        # Try cache first
        cache_key = f"usage:{user_id}"
        if self.redis:
            try:
                cached = self.redis.get(cache_key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read failed: {e}")

        # Get from database
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        usage = {
            "session_count": user.session_count or 0,
            "transcription_count": user.transcription_count or 0,
            "usage_minutes": user.usage_minutes or 0,
            "plan": user.plan or "FREE",
        }

        # Cache the result
        if self.redis:
            try:
                self.redis.setex(cache_key, self.cache_ttl, json.dumps(usage))
            except Exception as e:
                logger.warning(f"Cache write failed: {e}")

        return usage

    def increment_usage(self, user_id: str, metric: str, amount: int = 1) -> int:
        """
        Increment a usage metric for a user.

        Args:
            user_id: User ID
            metric: Metric to increment (session_count, transcription_count, usage_minutes)
            amount: Amount to increment by

        Returns:
            New value after increment
        """
        # Validate metric
        valid_metrics = [
            "session_count",
            "transcription_count",
            "usage_minutes",
        ]
        if metric not in valid_metrics:
            raise ValueError(f"Invalid metric: {metric}")

        # Update in database
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Get current value and increment
        current_value = getattr(user, metric) or 0
        new_value = current_value + amount
        setattr(user, metric, new_value)

        # Commit changes
        self.db.commit()

        # Invalidate cache
        if self.redis:
            try:
                cache_key = f"usage:{user_id}"
                self.redis.delete(cache_key)
            except Exception as e:
                logger.warning(f"Cache invalidation failed: {e}")

        logger.info(
            f"Incremented {metric} for user {user_id}: {current_value} -> {new_value}"
        )

        return new_value

    def check_limit(
        self, user_id: str, metric: str, limit: int, additional_amount: int = 0
    ) -> bool:
        """
        Check if a user is within their plan limit for a metric.

        Args:
            user_id: User ID
            metric: Metric to check
            limit: Plan limit for this metric
            additional_amount: Additional amount to consider (for pre-check)

        Returns:
            True if within limit, False if exceeded
        """
        if limit == -1:  # Unlimited
            return True

        usage = self.get_current_usage(user_id)
        current = usage.get(metric.replace("_count", "_count"), 0)

        return (current + additional_amount) <= limit

    def reset_monthly_usage(self, user_id: str) -> None:
        """
        Reset monthly usage counters for a specific user.

        Args:
            user_id: User ID to reset
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Reset counters
        user.session_count = 0
        user.transcription_count = 0
        user.usage_minutes = 0

        # Update last reset timestamp if we track it
        if hasattr(user, "last_usage_reset"):
            user.last_usage_reset = datetime.utcnow()

        self.db.commit()

        # Clear cache
        if self.redis:
            try:
                cache_key = f"usage:{user_id}"
                self.redis.delete(cache_key)
            except Exception as e:
                logger.warning(f"Cache clear failed: {e}")

        logger.info(f"Reset monthly usage for user {user_id}")

    def reset_all_monthly_usage(self) -> int:
        """
        Reset monthly usage for all users.
        Typically called by a scheduled job at month start.

        Returns:
            Number of users reset
        """
        try:
            # Reset all users in database
            result = self.db.execute(
                text(
                    """
                    UPDATE users
                    SET session_count = 0,
                        transcription_count = 0,
                        usage_minutes = 0
                    WHERE session_count > 0
                       OR transcription_count > 0
                       OR usage_minutes > 0
                """
                )
            )

            affected_rows = result.rowcount
            self.db.commit()

            # Clear all usage cache entries
            if self.redis:
                try:
                    # Get all usage cache keys
                    for key in self.redis.scan_iter("usage:*"):
                        self.redis.delete(key)
                except Exception as e:
                    logger.warning(f"Cache clear failed: {e}")

            logger.info(f"Reset monthly usage for {affected_rows} users")
            return affected_rows

        except Exception as e:
            logger.error(f"Failed to reset all monthly usage: {e}")
            self.db.rollback()
            raise

    def get_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get a comprehensive usage summary for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with usage summary including percentages
        """
        from coaching_assistant.services.plan_limits import (
            PlanName,
            get_global_plan_limits,
        )

        usage = self.get_current_usage(user_id)
        plan_name = PlanName(usage.get("plan", "FREE"))
        plan_limits_service = get_global_plan_limits()
        limits = plan_limits_service.get_plan_limit(plan_name)

        def calculate_percentage(current: int, limit: int) -> float:
            if limit == -1:  # Unlimited
                return 0.0
            if limit == 0:
                return 100.0
            return min(100.0, (current / limit) * 100)

        summary = {
            "plan": plan_name.value,
            "sessions": {
                "used": usage["session_count"],
                "limit": limits.max_sessions_per_month,
                "percentage": calculate_percentage(
                    usage["session_count"], limits.max_sessions_per_month
                ),
                "remaining": (
                    max(
                        0,
                        limits.max_sessions_per_month - usage["session_count"],
                    )
                    if limits.max_sessions_per_month != -1
                    else -1
                ),
            },
            "transcriptions": {
                "used": usage["transcription_count"],
                "limit": limits.max_transcriptions_per_month,
                "percentage": calculate_percentage(
                    usage["transcription_count"],
                    limits.max_transcriptions_per_month,
                ),
                "remaining": (
                    max(
                        0,
                        limits.max_transcriptions_per_month
                        - usage["transcription_count"],
                    )
                    if limits.max_transcriptions_per_month != -1
                    else -1
                ),
            },
            "minutes": {
                "used": usage["usage_minutes"],
                "limit": limits.max_minutes_per_month,
                "percentage": calculate_percentage(
                    usage["usage_minutes"], limits.max_minutes_per_month
                ),
                "remaining": (
                    max(
                        0,
                        limits.max_minutes_per_month - usage["usage_minutes"],
                    )
                    if limits.max_minutes_per_month != -1
                    else -1
                ),
            },
            "reset_date": self._get_reset_date(),
            "days_until_reset": self._days_until_reset(),
        }

        return summary

    def _get_reset_date(self) -> str:
        """Get the next monthly reset date."""
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)
        return reset_date.isoformat() + "Z"

    def _days_until_reset(self) -> int:
        """Calculate days until next monthly reset."""
        now = datetime.utcnow()
        if now.month == 12:
            reset_date = datetime(now.year + 1, 1, 1)
        else:
            reset_date = datetime(now.year, now.month + 1, 1)
        return (reset_date - now).days

    def record_usage_history(
        self, user_id: str, action: str, metadata: Optional[Dict] = None
    ) -> None:
        """
        Record usage history for analytics.
        This can be used for detailed usage tracking and reporting.

        Args:
            user_id: User ID
            action: Action performed
            metadata: Additional metadata about the action
        """
        # This could write to a separate usage_history table
        # For now, just log it
        logger.info(
            f"Usage history: user={user_id}, action={action}, metadata={metadata}"
        )

        # If we have Redis, we can also track in a time-series format
        if self.redis:
            try:
                # Store in a sorted set with timestamp as score
                key = f"usage_history:{user_id}:{action}"
                timestamp = datetime.utcnow().timestamp()
                value = json.dumps({"timestamp": timestamp, "metadata": metadata or {}})

                # Keep only last 30 days of history
                self.redis.zadd(key, {value: timestamp})
                self.redis.expire(key, 30 * 24 * 3600)  # 30 days

            except Exception as e:
                logger.warning(f"Failed to record usage history: {e}")
