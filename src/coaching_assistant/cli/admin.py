"""Administrative CLI commands for role management."""

import click
import sys
from sqlalchemy.orm import Session, sessionmaker
from ..models.user import User, UserRole
from ..services.permissions import PermissionService
from ..core.config import settings
from ..core.database import create_database_engine


def get_db_session() -> Session:
    """Create a database session for CLI operations."""
    engine = create_database_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()


@click.group()
def admin():
    """Administrative commands for role management."""
    pass


@admin.command()
@click.argument('email')
@click.argument('role', type=click.Choice(['user', 'staff', 'admin', 'super_admin']))
@click.option('--reason', '-r', required=True, help='Reason for role change')
@click.option('--force', '-f', is_flag=True, help='Force the operation without confirmation')
def grant_role(email: str, role: str, reason: str, force: bool):
    """Grant role to user by email."""
    
    if not force:
        click.confirm(f'Grant {role} role to {email}?', abort=True)
    
    with get_db_session() as db:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User not found: {email}")
            sys.exit(1)
        
        # Get super admin (from environment or first super_admin)
        super_admin = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN
        ).first()
        
        if not super_admin:
            # If no super admin exists, check if we're creating the first one
            if role == 'super_admin':
                click.echo("⚠️  No super administrator found. Creating first super admin...")
                user.role = UserRole.SUPER_ADMIN
                db.commit()
                click.echo(f"✅ First super admin created: {email}")
                return
            else:
                click.echo("❌ No super administrator found in system. Create one first.")
                sys.exit(1)
        
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
            sys.exit(1)


@admin.command()
@click.argument('email')
@click.option('--reason', '-r', required=True, help='Reason for role revocation')
def revoke_role(email: str, reason: str):
    """Revoke admin/staff role from user (set back to USER)."""
    
    click.confirm(f'Revoke admin/staff role from {email}?', abort=True)
    
    with get_db_session() as db:
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User not found: {email}")
            sys.exit(1)
        
        if user.role == UserRole.USER:
            click.echo(f"ℹ️  User {email} already has regular user role")
            return
        
        # Get super admin
        super_admin = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN
        ).first()
        
        if not super_admin:
            click.echo("❌ No super administrator found in system")
            sys.exit(1)
        
        # Revoke role
        permission_service = PermissionService(db)
        try:
            updated_user = permission_service.revoke_role(
                user_id=str(user.id),
                granted_by=super_admin,
                reason=reason
            )
            click.echo(f"✅ Role revoked for {email}. Now has role: {updated_user.role.value}")
        except Exception as e:
            click.echo(f"❌ Error revoking role: {str(e)}")
            sys.exit(1)


@admin.command()
@click.argument('email')
def show_role(email: str):
    """Show current role and permissions for user."""
    
    with get_db_session() as db:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User not found: {email}")
            sys.exit(1)
        
        click.echo(f"\n📋 User Details:")
        click.echo(f"  Email: {email}")
        click.echo(f"  Name: {user.name}")
        click.echo(f"  Role: {user.role.value}")
        click.echo(f"\n🔐 Permissions:")
        click.echo(f"  Is Admin: {'✅' if user.is_admin() else '❌'}")
        click.echo(f"  Is Staff: {'✅' if user.is_staff() else '❌'}")
        click.echo(f"  Is Super Admin: {'✅' if user.is_super_admin() else '❌'}")
        
        if user.admin_access_expires:
            click.echo(f"\n⏰ Admin Session:")
            click.echo(f"  Expires: {user.admin_access_expires}")
        
        if user.allowed_ip_addresses:
            click.echo(f"\n🌐 IP Allowlist:")
            for ip in user.allowed_ip_addresses:
                click.echo(f"  - {ip}")


@admin.command()
def list_admins():
    """List all users with admin or staff roles."""
    
    with get_db_session() as db:
        permission_service = PermissionService(db)
        stats = permission_service.get_admin_stats()
        
        click.echo(f"\n📊 User Statistics:")
        click.echo(f"  Total Users: {stats['total_users']}")
        click.echo(f"  Super Admins: {stats['super_admins']}")
        click.echo(f"  Admins: {stats['admins']}")
        click.echo(f"  Staff: {stats['staff']}")
        click.echo(f"  Regular Users: {stats['regular_users']}")
        
        # List super admins
        super_admins = permission_service.get_users_by_role(UserRole.SUPER_ADMIN)
        if super_admins:
            click.echo(f"\n👑 Super Administrators:")
            for user in super_admins:
                click.echo(f"  - {user.email} ({user.name})")
        
        # List admins
        admins = permission_service.get_users_by_role(UserRole.ADMIN)
        if admins:
            click.echo(f"\n🔑 Administrators:")
            for user in admins:
                click.echo(f"  - {user.email} ({user.name})")
        
        # List staff
        staff = permission_service.get_users_by_role(UserRole.STAFF)
        if staff:
            click.echo(f"\n📋 Staff Members:")
            for user in staff:
                click.echo(f"  - {user.email} ({user.name})")


@admin.command()
@click.argument('user_email')
@click.option('--limit', '-l', default=10, help='Number of audit logs to show')
def audit_log(user_email: str, limit: int):
    """Show role change audit log for a user."""
    
    with get_db_session() as db:
        user = db.query(User).filter(User.email == user_email).first()
        if not user:
            click.echo(f"❌ User not found: {user_email}")
            sys.exit(1)
        
        permission_service = PermissionService(db)
        logs = permission_service.get_role_audit_log(user_id=str(user.id), limit=limit)
        
        if not logs:
            click.echo(f"No role changes found for {user_email}")
            return
        
        click.echo(f"\n📜 Role Change History for {user_email}:")
        click.echo("-" * 60)
        
        for log in logs:
            changed_by = db.query(User).filter(User.id == log.changed_by_id).first()
            click.echo(f"\n🕐 {log.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            click.echo(f"  Changed by: {changed_by.email if changed_by else 'Unknown'}")
            click.echo(f"  Old Role: {log.old_role or 'None'}")
            click.echo(f"  New Role: {log.new_role}")
            click.echo(f"  Reason: {log.reason or 'No reason provided'}")
            if log.ip_address:
                click.echo(f"  IP Address: {log.ip_address}")


@admin.command()
@click.argument('email')
def create_super_admin(email: str):
    """Create the first super admin (use only for initial setup)."""
    
    click.echo("⚠️  WARNING: This command should only be used for initial setup!")
    click.confirm(f'Create super admin account for {email}?', abort=True)
    
    with get_db_session() as db:
        # Check if any super admin exists
        existing_super = db.query(User).filter(
            User.role == UserRole.SUPER_ADMIN
        ).first()
        
        if existing_super:
            click.echo(f"❌ Super admin already exists: {existing_super.email}")
            click.echo("Use 'grant-role' command to manage roles.")
            sys.exit(1)
        
        # Find user by email
        user = db.query(User).filter(User.email == email).first()
        if not user:
            click.echo(f"❌ User not found: {email}")
            click.echo("User must exist before granting super admin role.")
            sys.exit(1)
        
        # Grant super admin role
        user.role = UserRole.SUPER_ADMIN
        db.commit()
        
        click.echo(f"✅ Super admin role granted to {email}")
        click.echo("This user can now manage all other user roles.")


if __name__ == "__main__":
    admin()