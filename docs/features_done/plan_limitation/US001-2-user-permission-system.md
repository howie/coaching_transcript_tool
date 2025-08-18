# US001-2: User Permission and Role System ✅

## 📋 User Story

**As a** platform administrator  
**I want** a proper role-based access control (RBAC) system  
**So that** I can securely manage admin-only features and protect sensitive business analytics

## 🎉 Implementation Status: COMPLETED

**Completion Date**: 2025-01-15  
**Developer**: Claude + Howie  
**Migration Applied**: `3c453ba97936_add_user_role_and_role_audit_log_table`

## 💼 Business Value

### Previous Problems (RESOLVED)
- ~~No formal permission system exists in the platform~~
- ~~Admin endpoints use temporary workaround (enterprise plan = admin access)~~
- ~~Security risk: All enterprise users incorrectly have admin privileges~~
- ~~Cannot delegate different levels of administrative access~~
- ~~No audit trail for administrative actions~~

### Value Delivered ✅
- **Secure Access Control**: 4-tier RBAC system implemented
- **Compliance Ready**: Full audit trail for SOC2/GDPR requirements
- **Operational Flexibility**: Role-based delegation working
- **Audit Trail**: Complete logging of all role changes
- **Data Protection**: Role-based access control enforced

## 🎯 Acceptance Criteria

### Core Requirements

1. **User Role System**
   - [x] Add role field to User model (enum: user, staff, admin, super_admin)
   - [x] Create database migration for role field
   - [x] Default all existing users to "user" role
   - [x] Set specific admin users via environment config or CLI

2. **Permission Decorators**
   - [x] Create @require_admin decorator for admin-only endpoints
   - [x] Create @require_staff decorator for staff+ endpoints
   - [x] Create @require_role(role) flexible decorator
   - [x] Update all existing admin endpoints to use proper decorators

3. **Role Management**
   - [x] CLI command to grant/revoke admin roles
   - [x] API endpoint for super_admin to manage other roles
   - [x] Audit log for all role changes
   - [ ] Email notification on role changes (future enhancement)

4. **Permission Checks**
   - [x] Replace enterprise plan check with proper role check
   - [x] Add role validation in get_current_user_dependency
   - [x] Create permission service for complex authorization logic
   - [x] Add role-based filtering for data access

5. **Security Enhancements**
   - [ ] Add rate limiting for admin endpoints (future)
   - [x] Implement session-based admin access (2-hour timeout)
   - [x] Add IP allowlist for admin access (optional)
   - [ ] Two-factor authentication for admin users (future)

## 🏗️ Technical Implementation

### Database Schema

```sql
-- Add role to user table
ALTER TABLE "user" ADD COLUMN role VARCHAR(20) DEFAULT 'user' NOT NULL;

-- Create index for role queries
CREATE INDEX idx_user_role ON "user"(role);

-- Audit log for role changes
CREATE TABLE role_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id),
    changed_by_id UUID NOT NULL REFERENCES "user"(id),
    old_role VARCHAR(20),
    new_role VARCHAR(20) NOT NULL,
    reason TEXT,
    ip_address INET,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_role_audit_user ON role_audit_log(user_id);
CREATE INDEX idx_role_audit_changed_by ON role_audit_log(changed_by_id);
```

### User Model Updates

```python
# src/coaching_assistant/models/user.py

class UserRole(enum.Enum):
    """User roles for access control."""
    USER = "user"          # Regular user
    STAFF = "staff"        # Support staff (read-only admin)
    ADMIN = "admin"        # Full admin (read/write)
    SUPER_ADMIN = "super_admin"  # System admin (manage other admins)

class User(BaseModel):
    # ... existing fields ...
    
    # Role-based access control
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, index=True)
    
    # Security fields
    last_admin_login = Column(DateTime(timezone=True), nullable=True)
    admin_access_expires = Column(DateTime(timezone=True), nullable=True)
    allowed_ip_addresses = Column(JSON, nullable=True)  # Optional IP allowlist
    
    def has_role(self, required_role: UserRole) -> bool:
        """Check if user has required role or higher."""
        role_hierarchy = {
            UserRole.USER: 0,
            UserRole.STAFF: 1,
            UserRole.ADMIN: 2,
            UserRole.SUPER_ADMIN: 3
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(required_role, 0)
    
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.has_role(UserRole.ADMIN)
    
    def is_staff(self) -> bool:
        """Check if user has staff privileges."""
        return self.has_role(UserRole.STAFF)
```

### Permission Service

```python
# src/coaching_assistant/services/permissions.py

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
            old_role=target_user.role.value,
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
        
        # Send notification email (implement separately)
        # self._send_role_change_notification(target_user, old_role, new_role)
        
        return target_user
    
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
```

### Updated Permission Decorators

```python
# src/coaching_assistant/api/auth.py

from functools import wraps
from typing import Callable
from fastapi import Depends, HTTPException, status
from ..models.user import User, UserRole
from ..services.permissions import PermissionService

def require_role(required_role: UserRole):
    """Decorator to require specific role for endpoint access."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(
            *args,
            current_user: User = Depends(get_current_user_dependency),
            db: Session = Depends(get_db),
            **kwargs
        ):
            permission_service = PermissionService(db)
            permission_service.require_role(current_user, required_role)
            return await func(*args, current_user=current_user, db=db, **kwargs)
        return wrapper
    return decorator

def require_admin(current_user: User = Depends(get_current_user_dependency)) -> User:
    """Require admin role for endpoint access."""
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_staff(current_user: User = Depends(get_current_user_dependency)) -> User:
    """Require staff role or higher for endpoint access."""
    if not current_user.is_staff():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return current_user
```

### CLI Commands

```python
# src/coaching_assistant/cli/admin.py

import click
from sqlalchemy.orm import Session
from ..core.database import get_db_session
from ..models.user import User, UserRole
from ..services.permissions import PermissionService

@click.group()
def admin():
    """Administrative commands."""
    pass

@admin.command()
@click.argument('email')
@click.argument('role', type=click.Choice(['user', 'staff', 'admin', 'super_admin']))
@click.option('--reason', '-r', required=True, help='Reason for role change')
def grant_role(email: str, role: str, reason: str):
    """Grant role to user by email."""
    
    with get_db_session() as db:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User not found: {email}")
            return
        
        # Get super admin (from environment or first super_admin)
        super_admin = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN
        ).first()
        
        if not super_admin:
            click.echo("❌ No super administrator found in system")
            return
        
        # Grant role
        permission_service = PermissionService(db)
        try:
            updated_user = permission_service.grant_role(
                user_id=str(user.id),
                new_role=UserRole[role.upper()],
                granted_by=super_admin,
                reason=reason
            )
            click.echo(f"✅ Role updated for {email}: {updated_user.role.value}")
        except Exception as e:
            click.echo(f"❌ Error granting role: {str(e)}")

@admin.command()
@click.argument('email')
def show_role(email: str):
    """Show current role for user."""
    
    with get_db_session() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User not found: {email}")
            return
        
        click.echo(f"User: {email}")
        click.echo(f"Role: {user.role.value}")
        click.echo(f"Is Admin: {user.is_admin()}")
        click.echo(f"Is Staff: {user.is_staff()}")

# Usage:
# python -m coaching_assistant admin grant-role user@example.com admin --reason "Promoted to admin"
# python -m coaching_assistant admin show-role user@example.com
```

### API Endpoints for Role Management

```python
# src/coaching_assistant/api/admin.py

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional, List
from ..dependencies import get_db, get_current_user_dependency
from ..models.user import User, UserRole
from ..services.permissions import PermissionService

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    role: UserRole = Body(...),
    reason: str = Body(...),
    current_user: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: Session = Depends(get_db)
):
    """Update user role (Super Admin only)."""
    
    permission_service = PermissionService(db)
    updated_user = permission_service.grant_role(
        user_id=user_id,
        new_role=role,
        granted_by=current_user,
        reason=reason
    )
    
    return {
        "user_id": str(updated_user.id),
        "email": updated_user.email,
        "role": updated_user.role.value,
        "updated_at": datetime.utcnow().isoformat()
    }

@router.get("/role-audit-log")
async def get_role_audit_log(
    user_id: Optional[str] = None,
    limit: int = 100,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get role change audit log (Admin only)."""
    
    permission_service = PermissionService(db)
    audit_logs = permission_service.get_role_audit_log(
        user_id=user_id,
        limit=limit
    )
    
    return {
        "total": len(audit_logs),
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id),
                "changed_by_id": str(log.changed_by_id),
                "old_role": log.old_role,
                "new_role": log.new_role,
                "reason": log.reason,
                "created_at": log.created_at.isoformat()
            }
            for log in audit_logs
        ]
    }
```

## 🧪 Test Scenarios

### Unit Tests

```python
def test_role_hierarchy():
    """Test role hierarchy comparison."""
    user = User(role=UserRole.STAFF)
    assert user.has_role(UserRole.USER) == True
    assert user.has_role(UserRole.STAFF) == True
    assert user.has_role(UserRole.ADMIN) == False
    assert user.has_role(UserRole.SUPER_ADMIN) == False

def test_grant_role_with_audit():
    """Test role granting with audit log."""
    super_admin = create_user(role=UserRole.SUPER_ADMIN)
    target_user = create_user(role=UserRole.USER)
    
    permission_service = PermissionService(db)
    updated_user = permission_service.grant_role(
        user_id=target_user.id,
        new_role=UserRole.ADMIN,
        granted_by=super_admin,
        reason="Test promotion"
    )
    
    assert updated_user.role == UserRole.ADMIN
    
    # Check audit log
    audit_logs = permission_service.get_role_audit_log(user_id=target_user.id)
    assert len(audit_logs) == 1
    assert audit_logs[0].new_role == "admin"

def test_permission_denied():
    """Test permission denial for insufficient role."""
    regular_user = create_user(role=UserRole.USER)
    
    with pytest.raises(HTTPException) as exc:
        require_admin(regular_user)
    
    assert exc.value.status_code == 403
```

## 📊 Success Metrics

- **Security**: 0 unauthorized admin access incidents
- **Compliance**: 100% of admin actions audited
- **Performance**: Role checks < 5ms
- **Adoption**: All admin endpoints using proper role checks

## 📋 Migration Plan

### Phase 1: Database Migration (Day 1)
1. Add role column to user table
2. Set all existing users to "user" role
3. Manually set admin users via CLI

### Phase 2: Permission System (Day 2-3)
1. Implement permission service
2. Create role decorators
3. Update existing admin endpoints

### Phase 3: Management Tools (Day 4-5)
1. Create CLI commands
2. Build admin API endpoints
3. Implement audit logging

### Phase 4: Testing & Rollout (Day 6-7)
1. Comprehensive testing
2. Update documentation
3. Train support staff
4. Production deployment

## 🔄 Dependencies

- User model exists ✅
- Authentication system working ✅
- Admin endpoints identified ✅
- Database migration framework ready ✅

## 📞 Stakeholders

**Product Owner**: Security Team  
**Technical Lead**: Backend Engineering  
**Reviewers**: Security Audit, Compliance Team  
**QA Focus**: Permission testing, Security audit

## ⚠️ Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Locking out all admins | Critical | Keep emergency super_admin access via environment variable |
| Performance impact | Medium | Index role column, cache permissions |
| Migration errors | High | Backup before migration, test in staging |
| Audit log growth | Low | Implement log rotation/archival |

## 🚀 Implementation Summary

### Files Created/Modified
1. **Database Migration**: `alembic/versions/3c453ba97936_add_user_role_and_role_audit_log_table.py`
2. **Models**:
   - `src/coaching_assistant/models/user.py` - Added UserRole enum and role methods
   - `src/coaching_assistant/models/role_audit_log.py` - New audit log model
3. **Services**: `src/coaching_assistant/services/permissions.py` - Permission management
4. **API**:
   - `src/coaching_assistant/api/dependencies.py` - Permission decorators
   - `src/coaching_assistant/api/admin.py` - Admin management endpoints
   - `src/coaching_assistant/api/usage.py` - Updated to use new permissions
5. **CLI**: `src/coaching_assistant/cli/admin.py` - Admin management commands
6. **Tests**: `tests/test_permissions.py` - Comprehensive test suite

### Key Features Implemented
- **4-Tier Role Hierarchy**: USER → STAFF → ADMIN → SUPER_ADMIN
- **Admin Session Management**: 2-hour timeout with refresh capability
- **Complete Audit Trail**: All role changes logged with reason and IP
- **CLI Management**: Full suite of admin commands
- **API Endpoints**: RESTful role management APIs
- **IP Allowlist**: Optional IP-based access control
- **SQLAlchemy Enum Fix**: Proper handling of PostgreSQL enum types

### Known Issues Resolved
- Fixed SQLAlchemy enum serialization issue with PostgreSQL
- Added `values_callable` parameter to properly map enum values

### CLI Commands Available
```bash
# Create first super admin
python -m coaching_assistant.cli.admin create-super-admin user@example.com

# Grant roles
python -m coaching_assistant.cli.admin grant-role user@example.com admin --reason "Promotion"

# Revoke roles
python -m coaching_assistant.cli.admin revoke-role user@example.com --reason "Role change"

# View user permissions
python -m coaching_assistant.cli.admin show-role user@example.com

# List all admins
python -m coaching_assistant.cli.admin list-admins

# View audit log
python -m coaching_assistant.cli.admin audit-log user@example.com
```

### API Endpoints
- `POST /api/v1/admin/users/{user_id}/role` - Update user role
- `DELETE /api/v1/admin/users/{user_id}/role` - Revoke role
- `GET /api/v1/admin/role-audit-log` - Get audit logs
- `GET /api/v1/admin/stats` - System statistics
- `GET /api/v1/admin/users/{user_id}/role` - User role info
- `GET /api/v1/admin/users/by-role/{role}` - List users by role
- `POST /api/v1/admin/refresh-session` - Refresh admin session

### Current System Status
- Super Admin: howie.yu@gmail.com ✅
- Test Admin: test@example.com ✅
- All existing users migrated to "user" role ✅
- Permission system fully operational ✅

**Implementation completed successfully. System ready for production use.**