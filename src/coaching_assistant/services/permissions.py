"""Permission service for role-based access control."""

from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from ..models.user import User, UserRole
from ..models.role_audit_log import RoleAuditLog


class PermissionService:
    """Handle role-based permissions and authorization."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def require_role(self, user: User, required_role: UserRole):
        """Verify user has required role or raise exception."""
        if not user.has_role(required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required role: {required_role.value}"
            )
    
    def require_admin_session(self, user: User):
        """Verify admin session is valid (not expired)."""
        if not user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        # Check if admin session expired (2 hours timeout)
        if user.admin_access_expires and user.admin_access_expires < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin session expired. Please re-authenticate."
            )
    
    def grant_role(
        self,
        user_id: str,
        new_role: UserRole,
        granted_by: User,
        reason: str,
        ip_address: Optional[str] = None
    ) -> User:
        """Grant role to user with audit logging."""
        
        # Only super_admin can grant roles
        if not granted_by.has_role(UserRole.SUPER_ADMIN):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super administrators can grant roles"
            )
        
        # Get target user
        target_user = self.db.query(User).filter(User.id == user_id).first()
        if not target_user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Cannot modify super_admin role unless you are super_admin
        if target_user.role == UserRole.SUPER_ADMIN and granted_by.id != target_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot modify super administrator role"
            )
        
        # Create audit log
        audit_log = RoleAuditLog(
            user_id=target_user.id,
            changed_by_id=granted_by.id,
            old_role=target_user.role.value if target_user.role else None,
            new_role=new_role.value,
            reason=reason,
            ip_address=ip_address
        )
        self.db.add(audit_log)
        
        # Update user role
        old_role = target_user.role
        target_user.role = new_role
        
        # If granting admin/staff, set session expiry
        if new_role in [UserRole.ADMIN, UserRole.STAFF]:
            target_user.admin_access_expires = datetime.utcnow() + timedelta(hours=2)
        
        self.db.commit()
        
        # TODO: Send notification email (implement separately)
        # self._send_role_change_notification(target_user, old_role, new_role)
        
        return target_user
    
    def revoke_role(
        self,
        user_id: str,
        granted_by: User,
        reason: str,
        ip_address: Optional[str] = None
    ) -> User:
        """Revoke admin/staff role and set back to USER."""
        return self.grant_role(
            user_id=user_id,
            new_role=UserRole.USER,
            granted_by=granted_by,
            reason=reason,
            ip_address=ip_address
        )
    
    def get_role_audit_log(
        self,
        user_id: Optional[str] = None,
        changed_by_id: Optional[str] = None,
        limit: int = 100
    ) -> List[RoleAuditLog]:
        """Get role change audit log."""
        query = self.db.query(RoleAuditLog)
        
        if user_id:
            query = query.filter(RoleAuditLog.user_id == user_id)
        if changed_by_id:
            query = query.filter(RoleAuditLog.changed_by_id == changed_by_id)
        
        return query.order_by(RoleAuditLog.created_at.desc()).limit(limit).all()
    
    def refresh_admin_session(self, user: User):
        """Refresh admin session expiry time."""
        if user.is_admin() or user.is_staff():
            user.last_admin_login = datetime.utcnow()
            user.admin_access_expires = datetime.utcnow() + timedelta(hours=2)
            self.db.commit()
    
    def check_ip_allowlist(self, user: User, ip_address: str) -> bool:
        """Check if IP address is in user's allowlist (if configured)."""
        if not user.allowed_ip_addresses:
            return True  # No allowlist configured, allow all
        
        return ip_address in user.allowed_ip_addresses
    
    def get_users_by_role(self, role: UserRole) -> List[User]:
        """Get all users with a specific role."""
        return self.db.query(User).filter(User.role == role).all()
    
    def get_admin_stats(self) -> dict:
        """Get statistics about admin users."""
        total_users = self.db.query(User).count()
        super_admins = self.db.query(User).filter(User.role == UserRole.SUPER_ADMIN).count()
        admins = self.db.query(User).filter(User.role == UserRole.ADMIN).count()
        staff = self.db.query(User).filter(User.role == UserRole.STAFF).count()
        regular_users = self.db.query(User).filter(User.role == UserRole.USER).count()
        
        return {
            "total_users": total_users,
            "super_admins": super_admins,
            "admins": admins,
            "staff": staff,
            "regular_users": regular_users
        }