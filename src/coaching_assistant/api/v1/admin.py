"""Admin API endpoints for role management and system administration."""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Body, status, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ...core.database import get_db
from ...models.user import User, UserRole
from ...services.permissions import PermissionService
from .dependencies import (
    require_super_admin,
    require_admin,
    get_current_user_with_permissions,
)


router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


class RoleUpdateRequest(BaseModel):
    """Request model for updating user role."""

    role: UserRole
    reason: str


class RoleUpdateResponse(BaseModel):
    """Response model for role update."""

    user_id: UUID
    email: str
    name: str
    role: UserRole
    updated_at: datetime


class RoleAuditLogResponse(BaseModel):
    """Response model for role audit log entry."""

    id: UUID
    user_id: UUID
    user_email: str
    changed_by_id: UUID
    changed_by_email: str
    old_role: Optional[str]
    new_role: str
    reason: Optional[str]
    ip_address: Optional[str]
    created_at: datetime


class AdminStatsResponse(BaseModel):
    """Response model for admin statistics."""

    total_users: int
    super_admins: int
    admins: int
    staff: int
    regular_users: int


class UserRoleInfo(BaseModel):
    """Response model for user role information."""

    id: UUID
    email: str
    name: str
    role: UserRole
    is_admin: bool
    is_staff: bool
    is_super_admin: bool
    admin_access_expires: Optional[datetime]
    allowed_ip_addresses: Optional[List[str]]


@router.post("/users/{user_id}/role", response_model=RoleUpdateResponse)
async def update_user_role(
    user_id: UUID,
    request: RoleUpdateRequest,
    current_request: Request,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """
    Update user role (Super Admin only).

    - **user_id**: UUID of the user to update
    - **role**: New role to assign
    - **reason**: Reason for the role change
    """

    # Get client IP for audit log
    client_ip = current_request.client.host if current_request.client else None

    permission_service = PermissionService(db)
    try:
        updated_user = permission_service.grant_role(
            user_id=str(user_id),
            new_role=request.role,
            granted_by=current_user,
            reason=request.reason,
            ip_address=client_ip,
        )

        return RoleUpdateResponse(
            user_id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            role=updated_user.role,
            updated_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}",
        )


@router.delete("/users/{user_id}/role", response_model=RoleUpdateResponse)
async def revoke_user_role(
    user_id: UUID,
    reason: str = Body(..., embed=True),
    current_request: Request = None,
    current_user: User = Depends(require_super_admin),
    db: Session = Depends(get_db),
):
    """
    Revoke admin/staff role from user (Super Admin only).
    Sets the user role back to USER.

    - **user_id**: UUID of the user to update
    - **reason**: Reason for revoking the role
    """

    # Get client IP for audit log
    client_ip = (
        current_request.client.host
        if current_request and current_request.client
        else None
    )

    permission_service = PermissionService(db)
    try:
        updated_user = permission_service.revoke_role(
            user_id=str(user_id),
            granted_by=current_user,
            reason=reason,
            ip_address=client_ip,
        )

        return RoleUpdateResponse(
            user_id=updated_user.id,
            email=updated_user.email,
            name=updated_user.name,
            role=updated_user.role,
            updated_at=datetime.utcnow(),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to revoke role: {str(e)}",
        )


@router.get("/role-audit-log", response_model=List[RoleAuditLogResponse])
async def get_role_audit_log(
    user_id: Optional[UUID] = None,
    changed_by_id: Optional[UUID] = None,
    limit: int = 100,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get role change audit log (Admin only).

    - **user_id**: Filter by user whose role was changed (optional)
    - **changed_by_id**: Filter by admin who made the change (optional)
    - **limit**: Maximum number of entries to return (default: 100)
    """

    permission_service = PermissionService(db)
    audit_logs = permission_service.get_role_audit_log(
        user_id=str(user_id) if user_id else None,
        changed_by_id=str(changed_by_id) if changed_by_id else None,
        limit=limit,
    )

    result = []
    for log in audit_logs:
        # Get user details for better display
        user = db.query(User).filter(User.id == log.user_id).first()
        changed_by = (
            db.query(User).filter(User.id == log.changed_by_id).first()
        )

        result.append(
            RoleAuditLogResponse(
                id=log.id,
                user_id=log.user_id,
                user_email=user.email if user else "Unknown",
                changed_by_id=log.changed_by_id,
                changed_by_email=changed_by.email if changed_by else "Unknown",
                old_role=log.old_role,
                new_role=log.new_role,
                reason=log.reason,
                ip_address=str(log.ip_address) if log.ip_address else None,
                created_at=log.created_at,
            )
        )

    return result


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """
    Get statistics about user roles (Admin only).
    """

    permission_service = PermissionService(db)
    stats = permission_service.get_admin_stats()

    return AdminStatsResponse(**stats)


@router.get("/users/{user_id}/role", response_model=UserRoleInfo)
async def get_user_role_info(
    user_id: UUID,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get detailed role information for a specific user (Admin only).

    - **user_id**: UUID of the user to query
    """

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return UserRoleInfo(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        is_admin=user.is_admin(),
        is_staff=user.is_staff(),
        is_super_admin=user.is_super_admin(),
        admin_access_expires=user.admin_access_expires,
        allowed_ip_addresses=user.allowed_ip_addresses,
    )


@router.get("/users/by-role/{role}", response_model=List[UserRoleInfo])
async def get_users_by_role(
    role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get all users with a specific role (Admin only).

    - **role**: Role to filter by (user, staff, admin, super_admin)
    """

    permission_service = PermissionService(db)
    users = permission_service.get_users_by_role(role)

    result = []
    for user in users:
        result.append(
            UserRoleInfo(
                id=user.id,
                email=user.email,
                name=user.name,
                role=user.role,
                is_admin=user.is_admin(),
                is_staff=user.is_staff(),
                is_super_admin=user.is_super_admin(),
                admin_access_expires=user.admin_access_expires,
                allowed_ip_addresses=user.allowed_ip_addresses,
            )
        )

    return result


@router.post("/refresh-session")
async def refresh_admin_session(
    current_user: User = Depends(get_current_user_with_permissions),
    db: Session = Depends(get_db),
):
    """
    Refresh admin session expiry time.
    Only available for users with admin or staff roles.
    """

    if not (current_user.is_admin() or current_user.is_staff()):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or staff users can refresh their session",
        )

    permission_service = PermissionService(db)
    permission_service.refresh_admin_session(current_user)

    return {
        "message": "Session refreshed successfully",
        "expires_at": (
            current_user.admin_access_expires.isoformat()
            if current_user.admin_access_expires
            else None
        ),
    }
