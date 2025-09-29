"""Bulk operations use cases for administrative tasks."""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List
from uuid import UUID

logger = logging.getLogger(__name__)


class BulkUsageResetUseCase:
    """Use case for bulk usage reset operations."""

    def __init__(self, usage_history_repository, user_repository):
        """Initialize with repository dependencies."""
        self.usage_history_repo = usage_history_repository
        self.user_repo = user_repository

    def reset_all_monthly_usage(self) -> Dict[str, Any]:
        """Reset monthly usage for all users."""
        try:
            logger.info("🔄 Starting bulk monthly usage reset operation")

            # Get all active users
            active_users = self.user_repo.get_all_active_users()
            reset_count = 0
            failed_resets = []

            for user in active_users:
                try:
                    # Reset user's monthly usage
                    self.usage_history_repo.reset_monthly_usage(user.id)
                    reset_count += 1

                    if reset_count % 100 == 0:  # Log progress every 100 users
                        logger.info(f"📊 Reset progress: {reset_count} users processed")

                except Exception as user_error:
                    logger.error(
                        f"❌ Failed to reset usage for user {user.id}: {user_error}"
                    )
                    failed_resets.append(str(user.id))

            logger.info(f"✅ Bulk usage reset completed: {reset_count} users reset")

            return {
                "success": True,
                "users_reset": reset_count,
                "total_users": len(active_users),
                "failed_resets": failed_resets,
                "operation_time": datetime.now(UTC).isoformat(),
                "operation_type": "monthly_usage_reset",
            }

        except Exception as e:
            logger.error(f"❌ Bulk usage reset operation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "users_reset": 0,
                "operation_time": datetime.now(UTC).isoformat(),
            }

    def reset_specific_users_usage(self, user_ids: List[UUID]) -> Dict[str, Any]:
        """Reset monthly usage for specific users."""
        try:
            logger.info(f"🔄 Starting targeted usage reset for {len(user_ids)} users")

            reset_count = 0
            failed_resets = []

            for user_id in user_ids:
                try:
                    # Verify user exists
                    user = self.user_repo.get_user_by_id(user_id)
                    if not user:
                        logger.warning(f"⚠️ User {user_id} not found, skipping")
                        failed_resets.append(f"User {user_id} not found")
                        continue

                    # Reset user's monthly usage
                    self.usage_history_repo.reset_monthly_usage(user_id)
                    reset_count += 1

                except Exception as user_error:
                    logger.error(
                        f"❌ Failed to reset usage for user {user_id}: {user_error}"
                    )
                    failed_resets.append(f"User {user_id}: {str(user_error)}")

            logger.info(f"✅ Targeted usage reset completed: {reset_count} users reset")

            return {
                "success": True,
                "users_reset": reset_count,
                "requested_users": len(user_ids),
                "failed_resets": failed_resets,
                "operation_time": datetime.now(UTC).isoformat(),
                "operation_type": "targeted_usage_reset",
            }

        except Exception as e:
            logger.error(f"❌ Targeted usage reset operation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "users_reset": 0,
                "operation_time": datetime.now(UTC).isoformat(),
            }


class BulkUserManagementUseCase:
    """Use case for bulk user management operations."""

    def __init__(self, user_repository, usage_history_repository):
        """Initialize with repository dependencies."""
        self.user_repo = user_repository
        self.usage_history_repo = usage_history_repository

    def bulk_plan_update(self, user_ids: List[UUID], new_plan: str) -> Dict[str, Any]:
        """Update plan for multiple users."""
        try:
            logger.info(
                f"🔄 Starting bulk plan update to {new_plan} for {len(user_ids)} users"
            )

            updated_count = 0
            failed_updates = []

            for user_id in user_ids:
                try:
                    # Verify user exists and update plan
                    success = self.user_repo.update_user_plan(user_id, new_plan)
                    if success:
                        updated_count += 1
                    else:
                        failed_updates.append(f"User {user_id}: Plan update failed")

                except Exception as user_error:
                    logger.error(
                        f"❌ Failed to update plan for user {user_id}: {user_error}"
                    )
                    failed_updates.append(f"User {user_id}: {str(user_error)}")

            logger.info(f"✅ Bulk plan update completed: {updated_count} users updated")

            return {
                "success": True,
                "users_updated": updated_count,
                "requested_users": len(user_ids),
                "new_plan": new_plan,
                "failed_updates": failed_updates,
                "operation_time": datetime.now(UTC).isoformat(),
                "operation_type": "bulk_plan_update",
            }

        except Exception as e:
            logger.error(f"❌ Bulk plan update operation failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "users_updated": 0,
                "operation_time": datetime.now(UTC).isoformat(),
            }

    def get_bulk_operation_status(self, operation_id: str) -> Dict[str, Any]:
        """Get status of a bulk operation (placeholder for future async operations)."""
        return {
            "operation_id": operation_id,
            "status": "completed",  # For now, all operations are synchronous
            "message": "Bulk operations are currently synchronous",
        }
