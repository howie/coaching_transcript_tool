"""Role audit log model for tracking role changes."""

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
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

    # Security tracking
    ip_address = Column(INET, nullable=True)

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
