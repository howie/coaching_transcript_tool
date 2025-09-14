"""SQLAlchemy implementation of UserRepoPort.

This module provides the concrete implementation of user repository
operations using SQLAlchemy ORM, following the Repository pattern.
"""

from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from ....core.repositories.ports import UserRepoPort
from ....models.user import User, UserPlan


class SQLAlchemyUserRepository(UserRepoPort):
    """SQLAlchemy implementation of the UserRepoPort interface."""

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
            User entity or None if not found
        """
        try:
            return self.session.get(User, user_id)
        except SQLAlchemyError as e:
            # Log error in production
            raise RuntimeError(f"Database error retrieving user {user_id}") from e

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            User entity or None if not found
        """
        try:
            return (
                self.session.query(User)
                .filter(User.email == email)
                .first()
            )
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
                self.session.query(User)
                .filter(User.email == email)
                .first()
            ) is not None
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database error checking user existence by email {email}") from e

    def save(self, user: User) -> User:
        """Save or update user entity.
        
        Args:
            user: User entity to save
            
        Returns:
            Saved user entity with updated fields
        """
        try:
            # Add to session if it's a new entity
            if user.id is None or not self._is_attached(user):
                self.session.add(user)
            
            self.session.commit()
            self.session.refresh(user)  # Get updated timestamp, etc.
            return user
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error saving user") from e

    def delete(self, user_id: UUID) -> bool:
        """Delete user by ID.
        
        Args:
            user_id: UUID of user to delete
            
        Returns:
            True if user was deleted, False if not found
        """
        try:
            user = self.session.get(User, user_id)
            if user is None:
                return False
            
            self.session.delete(user)
            self.session.commit()
            return True
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error deleting user {user_id}") from e

    def get_all_active_users(self) -> List[User]:
        """Get all active users.
        
        Returns:
            List of active user entities
        """
        try:
            return (
                self.session.query(User)
                .filter(User.is_active == True)  # noqa: E712
                .order_by(User.created_at)
                .all()
            )
        except SQLAlchemyError as e:
            raise RuntimeError("Database error retrieving active users") from e

    def update_plan(self, user_id: UUID, plan: UserPlan) -> User:
        """Update user's subscription plan.
        
        Args:
            user_id: UUID of user to update
            plan: New plan to assign
            
        Returns:
            Updated user entity
            
        Raises:
            ValueError: If user not found
            RuntimeError: If database error occurs
        """
        try:
            user = self.session.get(User, user_id)
            if user is None:
                raise ValueError(f"User {user_id} not found")
            
            user.plan = plan
            self.session.commit()
            self.session.refresh(user)
            return user
        except SQLAlchemyError as e:
            self.session.rollback()
            raise RuntimeError(f"Database error updating user plan for {user_id}") from e

    def _is_attached(self, user: User) -> bool:
        """Check if user entity is attached to current session.
        
        Args:
            user: User entity to check
            
        Returns:
            True if attached to session
        """
        return user in self.session


def create_user_repository(session: Session) -> UserRepoPort:
    """Factory function to create a user repository.
    
    Args:
        session: SQLAlchemy session
        
    Returns:
        UserRepoPort implementation
    """
    return SQLAlchemyUserRepository(session)