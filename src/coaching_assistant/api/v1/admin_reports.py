"""Admin reports API endpoints."""

import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ...core.config import settings
from ...core.database import get_db
from ...core.models.user import User, UserRole
from ...core.services.admin_daily_report import AdminDailyReportService
from ...tasks.admin_report_tasks import (
    generate_and_send_daily_report,
    schedule_weekly_summary_report,
)
from .dependencies import require_admin

router = APIRouter(prefix="/admin/reports", tags=["Admin Reports"])
logger = logging.getLogger(__name__)


class ReportRequest(BaseModel):
    """Request model for generating reports."""

    target_date: Optional[str] = Field(
        None,
        description="Target date in YYYY-MM-DD format (defaults to yesterday)",
        example="2024-01-15",
    )
    recipient_emails: Optional[List[str]] = Field(
        None,
        description=(
            "List of email addresses to send report to "
            "(defaults to configured admin emails)"
        ),
        example=["admin@company.com", "manager@company.com"],
    )
    send_email: bool = Field(
        True, description="Whether to send email report or just generate data"
    )


class ReportResponse(BaseModel):
    """Response model for report operations."""

    status: str
    message: str
    report_date: Optional[str] = None
    task_id: Optional[str] = None
    data: Optional[dict] = None


@router.get("/daily", response_model=ReportResponse)
async def get_daily_report(
    target_date: Optional[str] = Query(
        None,
        description=("Target date in YYYY-MM-DD format (defaults to yesterday)"),
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Get daily report data (read-only, no email sending).

    Requires STAFF role or higher.
    """
    # Check if user has staff privileges
    if not current_user.is_staff():
        raise HTTPException(
            status_code=403, detail="Access denied. Staff privileges required."
        )

    try:
        logger.info(f"🔍 User {current_user.email} requesting daily report")

        # Parse target date
        if target_date:
            try:
                parsed_date = datetime.fromisoformat(target_date).replace(
                    tzinfo=timezone.utc
                )
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )
        else:
            parsed_date = datetime.now(timezone.utc) - timedelta(days=1)

        # Generate report
        report_service = AdminDailyReportService(db, settings)
        report_data = report_service.generate_daily_report(parsed_date)

        # Convert to dict for response
        response_data = {
            "report_date": report_data.report_date,
            "metrics": {
                "total_users": report_data.total_users,
                "new_users_count": report_data.new_users_count,
                "active_users_count": report_data.active_users_count,
                "total_sessions": report_data.total_sessions,
                "completed_sessions": report_data.completed_sessions,
                "failed_sessions": report_data.failed_sessions,
                "error_rate": report_data.error_rate,
                "total_minutes_processed": float(report_data.total_minutes_processed),
                "total_cost_usd": float(report_data.total_cost_usd),
            },
            "users_by_plan": report_data.users_by_plan,
            "sessions_by_provider": report_data.sessions_by_provider,
            # Limit for API response
            "new_users": report_data.new_users[:10],
            # Limit for API response
            "top_users": report_data.top_users[:5],
            "admin_summary": {
                "total_admin_users": len(report_data.admin_users),
                "staff_logins_today": report_data.staff_logins_today,
            },
            "system_health": {
                "error_rate": report_data.error_rate,
                "avg_processing_time_minutes": (
                    report_data.avg_processing_time_minutes
                ),
            },
        }

        return ReportResponse(
            status="success",
            message=f"Daily report generated for {report_data.report_date}",
            report_date=report_data.report_date,
            data=response_data,
        )

    except Exception as e:
        logger.error(f"❌ Failed to generate daily report: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate report: {str(e)}"
        )


@router.post("/daily/send", response_model=ReportResponse)
async def send_daily_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_admin),
):
    """
    Generate and send daily report via email (async task).

    Requires ADMIN role.
    """
    # Check admin privileges
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403, detail="Access denied. Admin privileges required."
        )

    try:
        logger.info(f"📧 User {current_user.email} triggering daily report email")

        # Validate date format if provided
        if request.target_date:
            try:
                datetime.fromisoformat(request.target_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )

        # Queue the background task
        task = generate_and_send_daily_report.delay(
            target_date_str=request.target_date,
            recipient_emails=request.recipient_emails,
        )

        logger.info(f"📤 Daily report task queued: {task.id}")

        return ReportResponse(
            status="queued",
            message="Daily report generation and email sending queued successfully",  # noqa: E501
            task_id=task.id,
            report_date=request.target_date or "yesterday",
        )

    except Exception as e:
        logger.error(f"❌ Failed to queue daily report task: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to queue report task: {str(e)}"
        )


@router.post("/weekly/send", response_model=ReportResponse)
async def send_weekly_report(
    week_start_date: Optional[str] = Query(
        None,
        description=("Week start date in YYYY-MM-DD format (defaults to last Monday)"),
    ),
    current_user: User = Depends(require_admin),
):
    """
    Generate and send weekly summary report.

    Requires ADMIN role.
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403, detail="Access denied. Admin privileges required."
        )

    try:
        logger.info(f"📅 User {current_user.email} triggering weekly report")

        # Validate date format if provided
        if week_start_date:
            try:
                datetime.fromisoformat(week_start_date)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid date format. Use YYYY-MM-DD.",
                )

        # Queue the background task
        task = schedule_weekly_summary_report.delay(week_start_date_str=week_start_date)

        logger.info(f"📤 Weekly report task queued: {task.id}")

        return ReportResponse(
            status="queued",
            message="Weekly report generation queued successfully",
            task_id=task.id,
        )

    except Exception as e:
        logger.error(f"❌ Failed to queue weekly report task: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to queue weekly report task: {str(e)}",  # noqa: E501
        )


@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str, current_user: User = Depends(require_admin)):
    """
    Check the status of a report generation task.

    Requires STAFF role or higher.
    """
    if not current_user.is_staff():
        raise HTTPException(
            status_code=403, detail="Access denied. Staff privileges required."
        )

    try:
        # Get task result from Celery
        from celery.result import AsyncResult

        result = AsyncResult(task_id)

        response = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
        }

        if result.ready():
            if result.successful():
                response["result"] = result.result
            else:
                response["error"] = str(result.result)

        return response

    except Exception as e:
        logger.error(f"❌ Failed to get task status: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.get("/users/admin-list")
async def get_admin_users(
    current_user: User = Depends(require_admin), db: Session = Depends(get_db)
):
    """
    Get list of all admin and staff users.

    Requires ADMIN role.
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403, detail="Access denied. Admin privileges required."
        )

    try:
        # Query admin users
        admin_users = (
            db.query(User)
            .filter(
                User.role.in_([UserRole.ADMIN, UserRole.STAFF, UserRole.SUPER_ADMIN])
            )
            .order_by(User.role, User.email)
            .all()
        )

        admin_list = [
            {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "last_admin_login": (
                    user.last_admin_login.isoformat() if user.last_admin_login else None
                ),
                "created_at": user.created_at.isoformat(),
            }
            for user in admin_users
        ]

        return {
            "admin_users": admin_list,
            "total_count": len(admin_list),
            "by_role": {
                "super_admin": sum(1 for u in admin_list if u["role"] == "super_admin"),
                "admin": sum(1 for u in admin_list if u["role"] == "admin"),
                "staff": sum(1 for u in admin_list if u["role"] == "staff"),
            },
        }

    except Exception as e:
        logger.error(f"❌ Failed to get admin users: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get admin users: {str(e)}"
        )


@router.get("/config/email-settings")
async def get_email_settings(current_user: User = Depends(require_admin)):
    """
    Get email configuration status for reports.

    Requires ADMIN role.
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=403, detail="Access denied. Admin privileges required."
        )

    import os

    # Check email configuration without exposing sensitive data
    config_status = {
        "smtp_configured": bool(os.getenv("SMTP_USER") and os.getenv("SMTP_PASSWORD")),
        "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "sender_email": os.getenv(
            "SENDER_EMAIL", os.getenv("SMTP_USER", "not-configured")
        ),
        "admin_emails_configured": bool(os.getenv("ADMIN_REPORT_EMAILS")),
        "admin_emails_count": (
            len(os.getenv("ADMIN_REPORT_EMAILS", "").split(","))
            if os.getenv("ADMIN_REPORT_EMAILS")
            else 0
        ),
    }

    return config_status


@router.post("/test-email")
async def send_test_email(
    recipient_email: str = Query(..., description="Email address to send test to"),
    current_user: User = Depends(require_admin),
):
    """
    Send a test email to verify email configuration.

    Requires SUPER_ADMIN role.
    """
    if not current_user.is_super_admin():
        raise HTTPException(
            status_code=403,
            detail="Access denied. Super admin privileges required.",
        )

    import os
    import smtplib
    from email.mime.text import MimeText

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not all([smtp_user, smtp_password]):
        raise HTTPException(status_code=400, detail="SMTP credentials not configured")

    try:
        # Create test message
        msg = MimeText(
            "This is a test email from the Admin Reports system. ✅",
            "plain",
            "utf-8",
        )
        msg["Subject"] = "Admin Reports Test Email 📧"
        msg["From"] = os.getenv("SENDER_EMAIL", smtp_user)
        msg["To"] = recipient_email

        # Send test email
        smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))

        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, [recipient_email], msg.as_string())

        logger.info(f"📧 Test email sent to {recipient_email} by {current_user.email}")

        return {
            "status": "success",
            "message": f"Test email sent successfully to {recipient_email}",
        }

    except Exception as e:
        logger.error(f"❌ Failed to send test email: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to send test email: {str(e)}"
        )
