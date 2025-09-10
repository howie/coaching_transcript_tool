"""Comprehensive tests for the permission system."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock
from fastapi import HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4

from coaching_assistant.models.user import User, UserRole
from coaching_assistant.models.role_audit_log import RoleAuditLog
from coaching_assistant.services.permissions import PermissionService


class TestUserRoleHierarchy:
    """Test role hierarchy and permission checks."""

    def test_role_hierarchy_comparison(self):
        """Test that role hierarchy works correctly."""
        # Create users with different roles
        regular_user = User(role=UserRole.USER)
        staff_user = User(role=UserRole.STAFF)
        admin_user = User(role=UserRole.ADMIN)
        super_admin_user = User(role=UserRole.SUPER_ADMIN)

        # Test USER role
        assert regular_user.has_role(UserRole.USER) == True
        assert regular_user.has_role(UserRole.STAFF) == False
        assert regular_user.has_role(UserRole.ADMIN) == False
        assert regular_user.has_role(UserRole.SUPER_ADMIN) == False

        # Test STAFF role
        assert staff_user.has_role(UserRole.USER) == True
        assert staff_user.has_role(UserRole.STAFF) == True
        assert staff_user.has_role(UserRole.ADMIN) == False
        assert staff_user.has_role(UserRole.SUPER_ADMIN) == False

        # Test ADMIN role
        assert admin_user.has_role(UserRole.USER) == True
        assert admin_user.has_role(UserRole.STAFF) == True
        assert admin_user.has_role(UserRole.ADMIN) == True
        assert admin_user.has_role(UserRole.SUPER_ADMIN) == False

        # Test SUPER_ADMIN role
        assert super_admin_user.has_role(UserRole.USER) == True
        assert super_admin_user.has_role(UserRole.STAFF) == True
        assert super_admin_user.has_role(UserRole.ADMIN) == True
        assert super_admin_user.has_role(UserRole.SUPER_ADMIN) == True

    def test_is_admin_method(self):
        """Test is_admin helper method."""
        regular_user = User(role=UserRole.USER)
        staff_user = User(role=UserRole.STAFF)
        admin_user = User(role=UserRole.ADMIN)
        super_admin_user = User(role=UserRole.SUPER_ADMIN)

        assert regular_user.is_admin() == False
        assert staff_user.is_admin() == False
        assert admin_user.is_admin() == True
        assert super_admin_user.is_admin() == True

    def test_is_staff_method(self):
        """Test is_staff helper method."""
        regular_user = User(role=UserRole.USER)
        staff_user = User(role=UserRole.STAFF)
        admin_user = User(role=UserRole.ADMIN)
        super_admin_user = User(role=UserRole.SUPER_ADMIN)

        assert regular_user.is_staff() == False
        assert staff_user.is_staff() == True
        assert admin_user.is_staff() == True
        assert super_admin_user.is_staff() == True

    def test_is_super_admin_method(self):
        """Test is_super_admin helper method."""
        regular_user = User(role=UserRole.USER)
        staff_user = User(role=UserRole.STAFF)
        admin_user = User(role=UserRole.ADMIN)
        super_admin_user = User(role=UserRole.SUPER_ADMIN)

        assert regular_user.is_super_admin() == False
        assert staff_user.is_super_admin() == False
        assert admin_user.is_super_admin() == False
        assert super_admin_user.is_super_admin() == True


class TestPermissionService:
    """Test PermissionService functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_db = Mock(spec=Session)
        self.service = PermissionService(self.mock_db)

    def test_require_role_with_sufficient_permissions(self):
        """Test require_role when user has sufficient permissions."""
        admin_user = User(role=UserRole.ADMIN)

        # Should not raise exception
        self.service.require_role(admin_user, UserRole.STAFF)
        self.service.require_role(admin_user, UserRole.ADMIN)

    def test_require_role_with_insufficient_permissions(self):
        """Test require_role when user lacks permissions."""
        regular_user = User(role=UserRole.USER)

        with pytest.raises(HTTPException) as exc_info:
            self.service.require_role(regular_user, UserRole.ADMIN)

        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail

    def test_require_admin_session_valid(self):
        """Test admin session validation with valid session."""
        admin_user = User(
            role=UserRole.ADMIN,
            admin_access_expires=datetime.utcnow() + timedelta(hours=1),
        )

        # Should not raise exception
        self.service.require_admin_session(admin_user)

    def test_require_admin_session_expired(self):
        """Test admin session validation with expired session."""
        admin_user = User(
            role=UserRole.ADMIN,
            admin_access_expires=datetime.utcnow() - timedelta(hours=1),
        )

        with pytest.raises(HTTPException) as exc_info:
            self.service.require_admin_session(admin_user)

        assert exc_info.value.status_code == 401
        assert "Admin session expired" in exc_info.value.detail

    def test_grant_role_success(self):
        """Test successful role granting."""
        super_admin = User(id=uuid4(), role=UserRole.SUPER_ADMIN)
        target_user = User(id=uuid4(), role=UserRole.USER)

        # Mock database query
        self.mock_db.query().filter().first.return_value = target_user

        # Grant role
        result = self.service.grant_role(
            user_id=target_user.id,
            new_role=UserRole.ADMIN,
            granted_by=super_admin,
            reason="Test promotion",
        )

        # Verify role was updated
        assert target_user.role == UserRole.ADMIN
        assert result == target_user

        # Verify audit log was created
        self.mock_db.add.assert_called_once()
        audit_log = self.mock_db.add.call_args[0][0]
        assert isinstance(audit_log, RoleAuditLog)
        assert audit_log.new_role == "admin"
        assert audit_log.reason == "Test promotion"

        # Verify commit was called
        self.mock_db.commit.assert_called_once()

    def test_grant_role_non_super_admin(self):
        """Test that non-super admins cannot grant roles."""
        admin_user = User(id=uuid4(), role=UserRole.ADMIN)
        target_user = User(id=uuid4(), role=UserRole.USER)

        with pytest.raises(HTTPException) as exc_info:
            self.service.grant_role(
                user_id=target_user.id,
                new_role=UserRole.ADMIN,
                granted_by=admin_user,
                reason="Test",
            )

        assert exc_info.value.status_code == 403
        assert (
            "Only super administrators can grant roles"
            in exc_info.value.detail
        )

    def test_grant_role_user_not_found(self):
        """Test granting role to non-existent user."""
        super_admin = User(id=uuid4(), role=UserRole.SUPER_ADMIN)

        # Mock database query to return None
        self.mock_db.query().filter().first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            self.service.grant_role(
                user_id=str(uuid4()),
                new_role=UserRole.ADMIN,
                granted_by=super_admin,
                reason="Test",
            )

        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail

    def test_revoke_role(self):
        """Test role revocation."""
        super_admin = User(id=uuid4(), role=UserRole.SUPER_ADMIN)
        admin_user = User(id=uuid4(), role=UserRole.ADMIN)

        # Mock database query
        self.mock_db.query().filter().first.return_value = admin_user

        # Revoke role
        result = self.service.revoke_role(
            user_id=admin_user.id,
            granted_by=super_admin,
            reason="Test revocation",
        )

        # Verify role was revoked
        assert admin_user.role == UserRole.USER
        assert result == admin_user

    def test_refresh_admin_session(self):
        """Test admin session refresh."""
        admin_user = User(
            role=UserRole.ADMIN,
            admin_access_expires=datetime.utcnow() - timedelta(hours=1),
        )

        # Refresh session
        self.service.refresh_admin_session(admin_user)

        # Verify session was refreshed
        assert admin_user.last_admin_login is not None
        assert admin_user.admin_access_expires > datetime.utcnow()
        self.mock_db.commit.assert_called_once()

    def test_check_ip_allowlist_no_restriction(self):
        """Test IP allowlist when no restriction is configured."""
        user = User(allowed_ip_addresses=None)

        assert self.service.check_ip_allowlist(user, "192.168.1.1") == True
        assert self.service.check_ip_allowlist(user, "10.0.0.1") == True

    def test_check_ip_allowlist_with_restriction(self):
        """Test IP allowlist with configured restrictions."""
        user = User(allowed_ip_addresses=["192.168.1.1", "10.0.0.1"])

        assert self.service.check_ip_allowlist(user, "192.168.1.1") == True
        assert self.service.check_ip_allowlist(user, "10.0.0.1") == True
        assert self.service.check_ip_allowlist(user, "172.16.0.1") == False

    def test_get_users_by_role(self):
        """Test getting users by role."""
        admin_users = [
            User(id=uuid4(), role=UserRole.ADMIN),
            User(id=uuid4(), role=UserRole.ADMIN),
        ]

        # Mock database query
        self.mock_db.query().filter().all.return_value = admin_users

        result = self.service.get_users_by_role(UserRole.ADMIN)

        assert result == admin_users
        assert len(result) == 2

    def test_get_admin_stats(self):
        """Test getting admin statistics."""
        # Mock count queries
        self.mock_db.query().count.return_value = 100  # Total users
        self.mock_db.query().filter().count.side_effect = [
            1,
            3,
            5,
            91,
        ]  # super_admin, admin, staff, user

        stats = self.service.get_admin_stats()

        assert stats["total_users"] == 100
        assert stats["super_admins"] == 1
        assert stats["admins"] == 3
        assert stats["staff"] == 5
        assert stats["regular_users"] == 91

    def test_get_role_audit_log(self):
        """Test retrieving role audit logs."""
        logs = [
            RoleAuditLog(
                id=uuid4(),
                user_id=uuid4(),
                changed_by_id=uuid4(),
                old_role="user",
                new_role="admin",
                reason="Test",
                created_at=datetime.utcnow(),
            )
        ]

        # Mock database query
        query_mock = Mock()
        query_mock.order_by().limit().all.return_value = logs
        self.mock_db.query.return_value = query_mock

        result = self.service.get_role_audit_log(limit=10)

        assert result == logs
        assert len(result) == 1


class TestPermissionIntegration:
    """Integration tests for permission system."""

    @pytest.mark.integration
    def test_full_role_lifecycle(self, db_session):
        """Test complete role lifecycle from creation to audit."""
        # Create users
        super_admin = User(
            email="super@example.com",
            name="Super Admin",
            role=UserRole.SUPER_ADMIN,
        )
        regular_user = User(
            email="user@example.com", name="Regular User", role=UserRole.USER
        )

        db_session.add_all([super_admin, regular_user])
        db_session.commit()

        # Create permission service
        service = PermissionService(db_session)

        # Grant admin role
        updated_user = service.grant_role(
            user_id=regular_user.id,
            new_role=UserRole.ADMIN,
            granted_by=super_admin,
            reason="Promotion to admin",
        )

        # Verify role was granted
        assert updated_user.role == UserRole.ADMIN
        assert updated_user.is_admin() == True

        # Check audit log
        audit_logs = service.get_role_audit_log(user_id=regular_user.id)
        assert len(audit_logs) == 1
        assert audit_logs[0].new_role == "admin"
        assert audit_logs[0].reason == "Promotion to admin"

        # Revoke role
        revoked_user = service.revoke_role(
            user_id=regular_user.id,
            granted_by=super_admin,
            reason="Test completed",
        )

        # Verify role was revoked
        assert revoked_user.role == UserRole.USER
        assert revoked_user.is_admin() == False

        # Check updated audit log
        audit_logs = service.get_role_audit_log(user_id=regular_user.id)
        assert len(audit_logs) == 2
        assert audit_logs[0].new_role == "user"  # Most recent first
        assert audit_logs[0].reason == "Test completed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
