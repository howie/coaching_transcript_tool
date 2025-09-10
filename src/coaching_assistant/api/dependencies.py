"""API dependencies for authentication and authorization."""

from functools import wraps
from typing import Callable
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.user import User, UserRole
from ..services.permissions import PermissionService
from .auth import get_current_user_dependency


def require_role(required_role: UserRole):
    """Decorator to require specific role for endpoint access."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user_dependency),
            db: Session = Depends(get_db),
            **kwargs,
        ):
            permission_service = PermissionService(db)
            permission_service.require_role(current_user, required_role)
            return await func(
                *args, current_user=current_user, db=db, **kwargs
            )

        return wrapper

    return decorator


def require_admin(
    current_user: User = Depends(get_current_user_dependency),
) -> User:
    """Dependency to require admin role for endpoint access."""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


def require_staff(
    current_user: User = Depends(get_current_user_dependency),
) -> User:
    """Dependency to require staff role or higher for endpoint access."""
    if not current_user.is_staff():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required",
        )
    return current_user


def require_super_admin(
    current_user: User = Depends(get_current_user_dependency),
) -> User:
    """Dependency to require super admin role for endpoint access."""
    if not current_user.is_super_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required",
        )
    return current_user


async def get_current_user_with_permissions(
    request: Request,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
) -> User:
    """Get current user and refresh admin session if applicable."""
    permission_service = PermissionService(db)

    # Check IP allowlist if configured
    client_ip = request.client.host if request.client else None
    if client_ip and not permission_service.check_ip_allowlist(
        current_user, client_ip
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied from this IP address",
        )

    # Refresh admin session if user is admin/staff
    if current_user.is_admin() or current_user.is_staff():
        permission_service.refresh_admin_session(current_user)

    return current_user
