"""SQLAlchemy implementation of UserRepoPort with domain model conversion.

This module provides the concrete implementation of user repository
operations using SQLAlchemy ORM with proper domain ↔ ORM conversion,
following Clean Architecture principles.
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import and_

from ....core.repositories.ports import UserRepoPort
from ....core.models.user import User, UserPlan, UserRole
from ..models.user_model import UserModel


class SQLAlchemyUserRepository(UserRepoPort):
    """SQLAlchemy implementation of the UserRepoPort interface with domain conversion."""

    def __init__(self, session: Session):
        """Initialize repository with database session.

        Args:
            session: SQLAlchemy session for database operations
        """
        self.session = session

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID.

        Args:
            user_id: UUID of the user to retrieve

        Returns:
            User domain entity or None if not found
        """
        try:
            orm_user = self.session.get(UserModel, user_id)
            return orm_user.to_domain() if orm_user else None
        except SQLAlchemyError as e:
            # Log error in production
            raise RuntimeError(f"Database error retrieving user {user_id}") from e

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.

        Args:
            email: Email address to search for

        Returns:
            User domain entity or None if not found
        """
        try:
            orm_user = (
                self.session.query(UserModel)
                .filter(UserModel.email == email)
                .first()
            )
            return orm_user.to_domain() if orm_user else None
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error retrieving user by email {email}") from e

    def exists_by_email(self, email: str) -> bool:
        """Check if user exists by email.

        Args:
            email: Email address to check

        Returns:
            True if user exists, False otherwise
        """
        try:
            return (
                self.session.query(UserModel.id)
                .filter(UserModel.email == email)
                .first()
            ) is not None
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error checking user existence for {email}") from e

    def save(self, user: User) -> User:
        """Save or update user entity.

        Args:
            user: User domain entity to save

        Returns:
            Saved User domain entity with updated fields
        """
        try:
            if user.id:
                # Update existing user
                orm_user = self.session.get(UserModel, user.id)
                if orm_user:
                    orm_user.update_from_domain(user)
                else:
                    # User ID exists but not found in DB - create new
                    orm_user = UserModel.from_domain(user)
                    self.session.add(orm_user)
            else:
                # Create new user
                orm_user = UserModel.from_domain(user)
                self.session.add(orm_user)

            self.session.flush()  # Get the ID without committing
            return orm_user.to_domain()

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving user {user.email}") from e

    def delete(self, user_id: UUID) -> bool:
        """Delete user by ID.

        Args:
            user_id: UUID of the user to delete

        Returns:
            True if user was deleted, False if not found
        """
        try:
            orm_user = self.session.get(UserModel, user_id)
            if orm_user:
                self.session.delete(orm_user)
                self.session.flush()
                return True
            return False
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error deleting user {user_id}") from e

    def list_all(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[User]:
        """List all users with optional pagination.

        Args:
            limit: Maximum number of users to return
            offset: Number of users to skip

        Returns:
            List of User domain entities
        """
        try:
            query = self.session.query(UserModel).order_by(UserModel.created_at.desc())

            if offset:
                query = query.offset(offset)
            if limit:
                query = query.limit(limit)

            orm_users = query.all()
            return [orm_user.to_domain() for orm_user in orm_users]

        except SQLAlchemyError as e:
            raise RuntimeError("Database error listing users") from e

    def get_by_plan(self, plan: UserPlan) -> List[User]:
        """Get users by plan type.

        Args:
            plan: User plan to filter by

        Returns:
            List of User domain entities with the specified plan
        """
        try:
            orm_users = (
                self.session.query(UserModel)
                .filter(UserModel.plan == plan)
                .order_by(UserModel.created_at.desc())
                .all()
            )
            return [orm_user.to_domain() for orm_user in orm_users]

        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting users by plan {plan}") from e

    def count_by_plan(self, plan: UserPlan) -> int:
        """Count users by plan type.

        Args:
            plan: User plan to count

        Returns:
            Number of users with the specified plan
        """
        try:
            return (
                self.session.query(UserModel)
                .filter(UserModel.plan == plan)
                .count()
            )
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error counting users by plan {plan}") from e

    def get_by_role(self, role: UserRole) -> List[User]:
        """Get users by role.

        Args:
            role: User role to filter by

        Returns:
            List of User domain entities with the specified role
        """
        try:
            orm_users = (
                self.session.query(UserModel)
                .filter(UserModel.role == role)
                .order_by(UserModel.created_at.desc())
                .all()
            )
            return [orm_user.to_domain() for orm_user in orm_users]

        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error getting users by role {role}") from e

    def update_usage_stats(self, user_id: UUID, usage_minutes: int, session_count: int) -> Optional[User]:
        """Update user usage statistics.

        Args:
            user_id: UUID of the user to update
            usage_minutes: New usage minutes total
            session_count: New session count total

        Returns:
            Updated User domain entity or None if not found
        """
        try:
            orm_user = self.session.get(UserModel, user_id)
            if orm_user:
                orm_user.usage_minutes = usage_minutes
                orm_user.session_count = session_count
                orm_user.mark_active()  # Update last active timestamp
                self.session.flush()
                return orm_user.to_domain()
            return None

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error updating usage stats for user {user_id}") from e

    def update_plan(self, user_id: UUID, new_plan: UserPlan) -> Optional[User]:
        """Update user plan.

        Args:
            user_id: UUID of the user to update
            new_plan: New plan to assign

        Returns:
            Updated User domain entity or None if not found
        """
        try:
            orm_user = self.session.get(UserModel, user_id)
            if orm_user:
                # Use domain model for business rule validation
                domain_user = orm_user.to_domain()
                domain_user.upgrade_plan(new_plan)  # This validates the upgrade

                # Update ORM model with validated domain data
                orm_user.update_from_domain(domain_user)
                self.session.flush()
                return orm_user.to_domain()
            return None

        except ValueError as e:
            # Business rule violation (e.g., invalid plan upgrade)
            raise ValueError(f"Plan upgrade validation failed: {e}") from e
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error updating plan for user {user_id}") from e

    def search_by_email_prefix(self, email_prefix: str, limit: int = 10) -> List[User]:
        """Search users by email prefix.

        Args:
            email_prefix: Email prefix to search for
            limit: Maximum number of results to return

        Returns:
            List of User domain entities matching the email prefix
        """
        try:
            orm_users = (
                self.session.query(UserModel)
                .filter(UserModel.email.ilike(f"{email_prefix}%"))
                .order_by(UserModel.email)
                .limit(limit)
                .all()
            )
            return [orm_user.to_domain() for orm_user in orm_users]

        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error searching users by email prefix {email_prefix}") from e

    def get_admin_users(self) -> List[User]:
        """Get all admin users (ADMIN and SUPER_ADMIN roles).

        Returns:
            List of User domain entities with admin privileges
        """
        try:
            orm_users = (
                self.session.query(UserModel)
                .filter(UserModel.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]))
                .order_by(UserModel.created_at.desc())
                .all()
            )
            return [orm_user.to_domain() for orm_user in orm_users]

        except SQLAlchemyError as e:
            raise RuntimeError("Database error getting admin users") from e

    def get_users_with_active_subscriptions(self) -> List[User]:
        """Get users with active subscriptions.

        Returns:
            List of User domain entities with active subscriptions
        """
        try:
            orm_users = (
                self.session.query(UserModel)
                .filter(UserModel.subscription_status.in_(["active", "trialing"]))
                .order_by(UserModel.created_at.desc())
                .all()
            )
            return [orm_user.to_domain() for orm_user in orm_users]

        except SQLAlchemyError as e:
            raise RuntimeError("Database error getting users with active subscriptions") from e

    def reset_monthly_usage_for_all(self) -> int:
        """Reset monthly usage counters for all users (called during billing cycle).

        Returns:
            Number of users updated
        """
        try:
            updated_count = (
                self.session.query(UserModel)
                .update({
                    UserModel.usage_minutes: 0,
                    UserModel.session_count: 0,
                })
            )
            self.session.flush()
            return updated_count

        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError("Database error resetting monthly usage for all users") from e