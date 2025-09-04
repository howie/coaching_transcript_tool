#!/usr/bin/env python3
"""
Setup script for Admin Daily Report Agent.

This script helps configure and test the admin report system.
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coaching_assistant.core.services.admin_daily_report import AdminDailyReportService
from coaching_assistant.tasks.admin_report_tasks import generate_and_send_daily_report
from coaching_assistant.core.database import get_db_session
from coaching_assistant.core.config import Settings

logger = logging.getLogger(__name__)


def setup_logging():
    """Setup logging for the setup script."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


def check_environment():
    """Check if all required environment variables are configured."""
    
    required_vars = [
        'DATABASE_URL',
        'REDIS_URL',
        'SMTP_USER',
        'SMTP_PASSWORD'
    ]
    
    optional_vars = [
        'SMTP_SERVER',
        'SMTP_PORT',
        'SENDER_EMAIL', 
        'ADMIN_REPORT_EMAILS'
    ]
    
    print("🔍 Checking environment configuration...")
    print()
    
    missing_required = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if 'PASSWORD' in var or 'KEY' in var:
                display_value = f"{'*' * (len(value) - 4)}{value[-4:]}" if len(value) > 4 else "****"
            else:
                display_value = value[:50] + "..." if len(value) > 50 else value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
            missing_required.append(var)
    
    print()
    print("Optional configuration:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            if var == 'ADMIN_REPORT_EMAILS':
                emails = [email.strip() for email in value.split(',')]
                print(f"✅ {var}: {len(emails)} email(s) configured")
            else:
                print(f"✅ {var}: {value}")
        else:
            print(f"⚠️  {var}: Using default")
    
    if missing_required:
        print()
        print("❌ Missing required environment variables:")
        for var in missing_required:
            print(f"   - {var}")
        print()
        print("Please configure these variables before running the admin report system.")
        return False
    
    print()
    print("✅ Environment configuration looks good!")
    return True


def test_database_connection():
    """Test database connection and query basic metrics."""
    
    print("🔗 Testing database connection...")
    
    try:
        with get_db_session() as db:
            from coaching_assistant.models.user import User
            from coaching_assistant.models.session import Session as TranscriptSession
            
            user_count = db.query(User).count()
            session_count = db.query(TranscriptSession).count()
            
            print(f"✅ Database connected successfully")
            print(f"   - Total users: {user_count}")
            print(f"   - Total sessions: {session_count}")
            return True
            
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def generate_test_report(target_date: str = None):
    """Generate a test report without sending email."""
    
    print("📊 Generating test report...")
    
    try:
        if target_date:
            test_date = datetime.fromisoformat(target_date).replace(tzinfo=timezone.utc)
        else:
            test_date = datetime.now(timezone.utc) - timedelta(days=1)
        
        settings = Settings()
        
        with get_db_session() as db:
            report_service = AdminDailyReportService(db, settings)
            report_data = report_service.generate_daily_report(test_date)
            
            print(f"✅ Test report generated for {report_data.report_date}")
            print()
            print("📈 Key metrics:")
            print(f"   - Total users: {report_data.total_users}")
            print(f"   - New users: {report_data.new_users_count}")
            print(f"   - Active users: {report_data.active_users_count}")
            print(f"   - Total sessions: {report_data.total_sessions}")
            print(f"   - Completed sessions: {report_data.completed_sessions}")
            print(f"   - Failed sessions: {report_data.failed_sessions}")
            print(f"   - Error rate: {report_data.error_rate:.2f}%")
            print(f"   - Minutes processed: {float(report_data.total_minutes_processed):.1f}")
            print(f"   - Total cost: ${float(report_data.total_cost_usd):.4f}")
            
            # Export JSON for inspection
            json_path = f"/tmp/test_admin_report_{report_data.report_date}.json"
            report_service.export_report_json(report_data, json_path)
            print(f"📄 Full report saved to: {json_path}")
            
            return True
            
    except Exception as e:
        print(f"❌ Test report generation failed: {str(e)}")
        return False


def test_email_configuration():
    """Test email configuration by sending a test email."""
    
    print("📧 Testing email configuration...")
    
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    if not all([smtp_user, smtp_password]):
        print("❌ SMTP credentials not configured")
        return False
    
    try:
        import smtplib
        from email.mime.text import MimeText
        
        # Create test message
        test_email = smtp_user  # Send to self
        msg = MimeText("This is a test email from Admin Report Setup. ✅", 'plain', 'utf-8')
        msg['Subject'] = "Admin Reports Setup Test 🧪"
        msg['From'] = os.getenv("SENDER_EMAIL", smtp_user)
        msg['To'] = test_email
        
        # Send test email
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [test_email], msg.as_string())
        
        print(f"✅ Test email sent successfully to {test_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email test failed: {str(e)}")
        return False


def show_usage_instructions():
    """Show usage instructions for the admin report system."""
    
    print()
    print("🎯 Admin Daily Report System - Usage Instructions")
    print("=" * 60)
    print()
    print("1. 📋 ENVIRONMENT CONFIGURATION")
    print("   Set these environment variables:")
    print("   ")
    print("   Required:")
    print("   - DATABASE_URL=postgresql://...")
    print("   - REDIS_URL=redis://...")
    print("   - SMTP_USER=your-email@gmail.com")
    print("   - SMTP_PASSWORD=your-app-password")
    print()
    print("   Optional:")
    print("   - SMTP_SERVER=smtp.gmail.com")
    print("   - SMTP_PORT=587")
    print("   - SENDER_EMAIL=reports@yourcompany.com")
    print("   - ADMIN_REPORT_EMAILS=admin1@company.com,admin2@company.com")
    print()
    
    print("2. 🚀 CELERY WORKER & BEAT SETUP")
    print("   Start Celery worker for admin reports:")
    print("   ")
    print("   celery -A coaching_assistant.config.celery worker \\")
    print("     --queues=admin_reports \\")
    print("     --concurrency=2 \\")
    print("     --loglevel=info")
    print()
    print("   Start Celery beat scheduler:")
    print("   ")
    print("   celery -A coaching_assistant.config.celery beat \\")
    print("     --scheduler=celery.beat:PersistentScheduler \\")
    print("     --loglevel=info")
    print()
    
    print("3. 📅 AUTOMATIC SCHEDULE")
    print("   Reports are automatically generated:")
    print("   - Daily report: Every day at 8:00 AM UTC")
    print("   - Weekly report: Every Monday at 9:00 AM UTC")
    print()
    
    print("4. 🔧 MANUAL TRIGGERING")
    print("   Via API endpoints:")
    print("   ")
    print("   # Get daily report data (read-only)")
    print("   GET /admin/reports/daily?target_date=2024-01-15")
    print()
    print("   # Send daily report email")
    print("   POST /admin/reports/daily/send")
    print("   {")
    print('     "target_date": "2024-01-15",')
    print('     "recipient_emails": ["admin@company.com"]')
    print("   }")
    print()
    print("   # Send weekly report")
    print("   POST /admin/reports/weekly/send?week_start_date=2024-01-15")
    print()
    
    print("5. 🔍 MONITORING")
    print("   Check task status:")
    print("   GET /admin/reports/task-status/{task_id}")
    print()
    print("   View admin users:")
    print("   GET /admin/reports/users/admin-list")
    print()
    print("   Check email configuration:")
    print("   GET /admin/reports/config/email-settings")
    print()
    
    print("6. 🧪 TESTING")
    print("   Run this setup script with different options:")
    print("   ")
    print("   python scripts/admin_report_setup.py --check-env")
    print("   python scripts/admin_report_setup.py --test-db")
    print("   python scripts/admin_report_setup.py --test-email")
    print("   python scripts/admin_report_setup.py --generate-test-report")
    print("   python scripts/admin_report_setup.py --all")
    print()
    
    print("7. 📊 REPORT CONTENTS")
    print("   Each daily report includes:")
    print("   - User metrics (total, new, active)")
    print("   - Session metrics (completed, failed, error rate)")
    print("   - Usage statistics (minutes, costs)")
    print("   - Top active users")
    print("   - Admin/staff activity")
    print("   - System health metrics")
    print("   - Billing and subscription data")
    print()
    
    print("🎉 Your admin report system is ready to use!")


def main():
    """Main setup function."""
    
    setup_logging()
    
    parser = argparse.ArgumentParser(
        description="Admin Daily Report Setup and Testing Tool"
    )
    parser.add_argument(
        "--check-env",
        action="store_true", 
        help="Check environment configuration"
    )
    parser.add_argument(
        "--test-db",
        action="store_true",
        help="Test database connection"
    )
    parser.add_argument(
        "--test-email",
        action="store_true",
        help="Test email configuration"
    )
    parser.add_argument(
        "--generate-test-report",
        action="store_true",
        help="Generate a test report (no email)"
    )
    parser.add_argument(
        "--target-date",
        type=str,
        help="Target date for test report (YYYY-MM-DD)"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--usage",
        action="store_true",
        help="Show usage instructions"
    )
    
    args = parser.parse_args()
    
    if args.usage:
        show_usage_instructions()
        return
    
    if not any([args.check_env, args.test_db, args.test_email, args.generate_test_report, args.all]):
        show_usage_instructions()
        return
    
    print("🎯 Admin Daily Report Setup Tool")
    print("=" * 40)
    print()
    
    success = True
    
    if args.check_env or args.all:
        if not check_environment():
            success = False
        print()
    
    if args.test_db or args.all:
        if not test_database_connection():
            success = False
        print()
    
    if args.test_email or args.all:
        if not test_email_configuration():
            success = False
        print()
    
    if args.generate_test_report or args.all:
        if not generate_test_report(args.target_date):
            success = False
        print()
    
    if success:
        print("✅ All tests passed! Admin report system is ready.")
        if not args.usage:
            print()
            print("💡 Run with --usage to see detailed usage instructions.")
    else:
        print("❌ Some tests failed. Please fix the issues before using the admin report system.")
        sys.exit(1)


if __name__ == "__main__":
    main()