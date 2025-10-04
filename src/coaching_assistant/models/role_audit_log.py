"""Role audit log model for tracking role changes."""

from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class RoleAuditLog(BaseModel):
    """Audit log for tracking user role changes."""

    __tablename__ = "role_audit_log"

    # User whose role was changed
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )

    # Admin who made the change
    changed_by_id = Column(
        UUID(as_uuid=True), ForeignKey("user.id"), nullable=False, index=True
    )

    # Role change details
    old_role = Column(String(20), nullable=True)
    new_role = Column(String(20), nullable=False)
    reason = Column(Text, nullable=True)

    # Security tracking - using String for SQLite compatibility
    # PostgreSQL INET would be ideal but we need SQLite support for tests
    ip_address = Column(String(45), nullable=True)  # IPv6 max length

    # Relationships
    user = relationship(
        "User", foreign_keys=[user_id], backref="role_changes", lazy="joined"
    )

    changed_by = relationship(
        "User",
        foreign_keys=[changed_by_id],
        backref="role_changes_made",
        lazy="joined",
    )

    def __repr__(self):
        return f"<RoleAuditLog(user_id={self.user_id}, old={self.old_role}, new={self.new_role})>"
