"""Celery tasks for admin daily reports."""

import logging
import os
import smtplib
from datetime import datetime, timezone, timedelta

try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    from email.mime.base import MimeBase
    from email import encoders
except ImportError:
    # Fallback for Python 3.13+ compatibility
    import email.mime.text as mime_text
    import email.mime.multipart as mime_multipart
    import email.mime.base as mime_base
    import email.encoders as encoders

    MimeText = mime_text.MIMEText
    MimeMultipart = mime_multipart.MIMEMultipart
    MimeBase = mime_base.MIMEBase
from typing import List, Optional

from celery import shared_task

from ..core.services.admin_daily_report import (
    AdminDailyReportService,
    DailyReportData,
)
from ..core.database import get_db_session
from ..core.config import Settings

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def generate_and_send_daily_report(
    self,
    target_date_str: Optional[str] = None,
    recipient_emails: Optional[List[str]] = None,
):
    """
    Celery task to generate and send daily admin report.

    Args:
        target_date_str: Target date in ISO format (YYYY-MM-DD), defaults to yesterday
        recipient_emails: List of email addresses to send report to
    """
    try:
        logger.info("🚀 Starting daily admin report generation task")

        # Parse target date
        if target_date_str:
            target_date = datetime.fromisoformat(target_date_str).replace(
                tzinfo=timezone.utc
            )
        else:
            target_date = datetime.now(timezone.utc) - timedelta(days=1)

        # Initialize services
        settings = Settings()

        # Get database session
        with get_db_session() as db_session:
            report_service = AdminDailyReportService(db_session, settings)

            # Generate report
            logger.info(f"📊 Generating report for date: {target_date.date()}")
            report_data = report_service.generate_daily_report(target_date)

            # Export to JSON for backup
            json_filename = f"daily_report_{report_data.report_date}.json"
            json_path = os.path.join("/tmp", json_filename)
            report_service.export_report_json(report_data, json_path)

            # Generate HTML email content
            html_content = report_service.format_report_for_email(report_data)

            # Send email report
            if not recipient_emails:
                recipient_emails = _get_default_admin_emails(settings)

            if recipient_emails:
                _send_email_report(
                    report_data=report_data,
                    html_content=html_content,
                    json_attachment_path=json_path,
                    recipients=recipient_emails,
                    settings=settings,
                )
                logger.info(
                    f"✅ Daily report sent to {len(recipient_emails)} recipients"
                )
            else:
                logger.warning(
                    "⚠️ No recipient emails configured, report generated but not sent"
                )

            # Clean up temp file
            if os.path.exists(json_path):
                os.remove(json_path)

            logger.info("✅ Daily admin report task completed successfully")

            return {
                "status": "success",
                "report_date": report_data.report_date,
                "recipients_count": (
                    len(recipient_emails) if recipient_emails else 0
                ),
                "key_metrics": {
                    "total_users": report_data.total_users,
                    "new_users": report_data.new_users_count,
                    "active_users": report_data.active_users_count,
                    "total_sessions": report_data.total_sessions,
                    "completed_sessions": report_data.completed_sessions,
                    "error_rate": report_data.error_rate,
                    "total_minutes": float(
                        report_data.total_minutes_processed
                    ),
                },
            }

    except Exception as exc:
        logger.error(f"❌ Daily report task failed: {str(exc)}")

        # Retry with exponential backoff
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceeded:
            logger.error("❌ Daily report task failed after all retries")

            # Send alert email about failure
            if recipient_emails:
                _send_failure_alert(
                    error_message=str(exc),
                    target_date=target_date_str or "yesterday",
                    recipients=recipient_emails,
                    settings=Settings(),
                )

            return {
                "status": "failed",
                "error": str(exc),
                "target_date": target_date_str,
            }


@shared_task(bind=True)
def schedule_weekly_summary_report(
    self, week_start_date_str: Optional[str] = None
):
    """
    Generate weekly summary report (aggregation of daily reports).

    Args:
        week_start_date_str: Start date of week in ISO format (YYYY-MM-DD)
    """
    try:
        logger.info("📅 Starting weekly summary report generation")

        # Parse week start date (defaults to last Monday)
        if week_start_date_str:
            week_start = datetime.fromisoformat(week_start_date_str).replace(
                tzinfo=timezone.utc
            )
        else:
            today = datetime.now(timezone.utc).date()
            days_since_monday = today.weekday()
            last_monday = today - timedelta(days=days_since_monday + 7)
            week_start = datetime.combine(
                last_monday, datetime.min.time()
            ).replace(tzinfo=timezone.utc)

        week_end = week_start + timedelta(days=7)

        logger.info(
            f"📊 Generating weekly report for {week_start.date()} to {week_end.date()}"
        )

        settings = Settings()

        with get_db_session() as db_session:
            report_service = AdminDailyReportService(db_session, settings)

            # Generate daily reports for each day of the week
            weekly_data = []
            for i in range(7):
                day = week_start + timedelta(days=i)
                daily_report = report_service.generate_daily_report(day)
                weekly_data.append(daily_report)

            # Aggregate weekly metrics
            weekly_summary = _aggregate_weekly_data(weekly_data)

            # Generate weekly report email
            html_content = _format_weekly_report_email(
                weekly_summary, week_start, week_end
            )

            # Send to admin emails
            recipient_emails = _get_default_admin_emails(settings)
            if recipient_emails:
                _send_weekly_report_email(
                    html_content=html_content,
                    week_start=week_start,
                    week_end=week_end,
                    recipients=recipient_emails,
                    settings=settings,
                )

            logger.info("✅ Weekly summary report completed")

            return {
                "status": "success",
                "week_start": week_start.date().isoformat(),
                "week_end": week_end.date().isoformat(),
                "total_days": len(weekly_data),
            }

    except Exception as exc:
        logger.error(f"❌ Weekly report task failed: {str(exc)}")
        return {"status": "failed", "error": str(exc)}


def _get_default_admin_emails(settings: Settings) -> List[str]:
    """Get default admin email addresses from settings."""
    # Check environment variables for admin emails
    admin_emails_env = os.getenv("ADMIN_REPORT_EMAILS", "")

    if admin_emails_env:
        return [
            email.strip()
            for email in admin_emails_env.split(",")
            if email.strip()
        ]

    # Fallback to default admin emails (you should configure these)
    default_emails = [
        "admin@yourdomain.com",  # Replace with actual admin emails
        "reports@yourdomain.com",  # Replace with actual admin emails
    ]

    return default_emails


def _send_email_report(
    report_data: DailyReportData,
    html_content: str,
    json_attachment_path: str,
    recipients: List[str],
    settings: Settings,
) -> None:
    """Send daily report via email."""

    # Email configuration from environment
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    sender_email = os.getenv("SENDER_EMAIL", smtp_user)

    if not all([smtp_user, smtp_password]):
        logger.warning("⚠️ SMTP credentials not configured, email not sent")
        return

    try:
        # Create message
        msg = MimeMultipart("alternative")
        msg["Subject"] = f"Daily Admin Report - {report_data.report_date} 📊"
        msg["From"] = sender_email
        msg["To"] = ", ".join(recipients)

        # Add HTML content
        html_part = MimeText(html_content, "html", "utf-8")
        msg.attach(html_part)

        # Add JSON attachment
        if os.path.exists(json_attachment_path):
            with open(json_attachment_path, "rb") as attachment:
                part = MimeBase("application", "octet-stream")
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= daily_report_{report_data.report_date}.json",
                )
                msg.attach(part)

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(sender_email, recipients, msg.as_string())

        logger.info(
            f"📧 Daily report email sent successfully to {len(recipients)} recipients"
        )

    except Exception as e:
        logger.error(f"❌ Failed to send email report: {str(e)}")
        raise


def _send_failure_alert(
    error_message: str,
    target_date: str,
    recipients: List[str],
    settings: Settings,
) -> None:
    """Send failure alert email."""

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_user, smtp_password]):
        return

    try:
        html_content = f"""
        <html>
        <body>
            <h2 style="color: #dc2626;">⚠️ Daily Report Generation Failed</h2>
            <p><strong>Target Date:</strong> {target_date}</p>
            <p><strong>Error:</strong> {error_message}</p>
            <p><strong>Time:</strong> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p>Please check the system logs for more details.</p>
        </body>
        </html>
        """

        msg = MimeMultipart()
        msg["Subject"] = f"❌ Daily Report Failed - {target_date}"
        msg["From"] = smtp_user
        msg["To"] = ", ".join(recipients)

        msg.attach(MimeText(html_content, "html"))

        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())

        logger.info("📧 Failure alert email sent")

    except Exception as e:
        logger.error(f"❌ Failed to send failure alert: {str(e)}")


def _aggregate_weekly_data(daily_reports: List[DailyReportData]) -> dict:
    """Aggregate daily report data into weekly summary."""

    weekly_summary = {
        "total_users_end": 0,
        "new_users_week": 0,
        "active_users_week": set(),
        "total_sessions_week": 0,
        "completed_sessions_week": 0,
        "failed_sessions_week": 0,
        "total_minutes_week": 0,
        "total_cost_week": 0,
        "error_rates": [],
        "daily_breakdown": [],
    }

    for daily in daily_reports:
        weekly_summary["total_users_end"] = max(
            weekly_summary["total_users_end"], daily.total_users
        )
        weekly_summary["new_users_week"] += daily.new_users_count
        weekly_summary["total_sessions_week"] += daily.total_sessions
        weekly_summary["completed_sessions_week"] += daily.completed_sessions
        weekly_summary["failed_sessions_week"] += daily.failed_sessions
        weekly_summary["total_minutes_week"] += float(
            daily.total_minutes_processed
        )
        weekly_summary["total_cost_week"] += float(daily.total_cost_usd)

        if daily.total_sessions > 0:
            weekly_summary["error_rates"].append(daily.error_rate)

        weekly_summary["daily_breakdown"].append(
            {
                "date": daily.report_date,
                "new_users": daily.new_users_count,
                "sessions": daily.total_sessions,
                "completed": daily.completed_sessions,
                "minutes": float(daily.total_minutes_processed),
            }
        )

    # Calculate averages
    weekly_summary["avg_error_rate"] = (
        sum(weekly_summary["error_rates"]) / len(weekly_summary["error_rates"])
        if weekly_summary["error_rates"]
        else 0
    )

    return weekly_summary


def _format_weekly_report_email(
    weekly_data: dict, week_start: datetime, week_end: datetime
) -> str:
    """Format weekly summary report as HTML email."""

    success_rate = (
        (
            (
                weekly_data["completed_sessions_week"]
                / weekly_data["total_sessions_week"]
            )
            * 100
        )
        if weekly_data["total_sessions_week"] > 0
        else 0
    )

    daily_rows = []
    for day in weekly_data["daily_breakdown"]:
        daily_rows.append(
            f"<tr>"
            f"<td>{day['date']}</td>"
            f"<td>{day['new_users']}</td>"
            f"<td>{day['sessions']}</td>"
            f"<td>{day['completed']}</td>"
            f"<td>{day['minutes']:.1f}</td>"
            f"</tr>"
        )

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Weekly Admin Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background-color: #7c3aed; color: white; padding: 20px; border-radius: 5px; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #e5e5e5; border-radius: 5px; }}
            .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
            .metric-value {{ font-size: 24px; font-weight: bold; color: #7c3aed; }}
            .metric-label {{ color: #666; font-size: 14px; }}
            .table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
            .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .table th {{ background-color: #f5f5f5; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📅 Weekly Admin Report</h1>
            <h2>{week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')}</h2>
        </div>

        <div class="section">
            <h3>📊 Weekly Summary</h3>
            <div class="metric">
                <div class="metric-value">{weekly_data['new_users_week']}</div>
                <div class="metric-label">New Users</div>
            </div>
            <div class="metric">
                <div class="metric-value">{weekly_data['total_sessions_week']}</div>
                <div class="metric-label">Total Sessions</div>
            </div>
            <div class="metric">
                <div class="metric-value">{success_rate:.1f}%</div>
                <div class="metric-label">Success Rate</div>
            </div>
            <div class="metric">
                <div class="metric-value">{weekly_data['total_minutes_week']:.0f}</div>
                <div class="metric-label">Minutes Processed</div>
            </div>
            <div class="metric">
                <div class="metric-value">${weekly_data['total_cost_week']:.4f}</div>
                <div class="metric-label">Total Cost</div>
            </div>
        </div>

        <div class="section">
            <h3>📈 Daily Breakdown</h3>
            <table class="table">
                <tr><th>Date</th><th>New Users</th><th>Sessions</th><th>Completed</th><th>Minutes</th></tr>
                {''.join(daily_rows)}
            </table>
        </div>
    </body>
    </html>
    """

    return html_content


def _send_weekly_report_email(
    html_content: str,
    week_start: datetime,
    week_end: datetime,
    recipients: List[str],
    settings: Settings,
) -> None:
    """Send weekly report via email."""

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_user, smtp_password]):
        logger.warning(
            "⚠️ SMTP credentials not configured, weekly email not sent"
        )
        return

    try:
        msg = MimeMultipart()
        msg["Subject"] = (
            f"Weekly Admin Report - {week_start.strftime('%Y-%m-%d')} to {week_end.strftime('%Y-%m-%d')} 📅"
        )
        msg["From"] = smtp_user
        msg["To"] = ", ".join(recipients)

        msg.attach(MimeText(html_content, "html", "utf-8"))

        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, recipients, msg.as_string())

        logger.info(
            f"📧 Weekly report email sent to {len(recipients)} recipients"
        )

    except Exception as e:
        logger.error(f"❌ Failed to send weekly report: {str(e)}")


# Import MaxRetriesExceeded at the top
try:
    from celery.exceptions import MaxRetriesExceeded
except ImportError:
    # Fallback for newer Celery versions
    from celery.exceptions import Retry as MaxRetriesExceeded
