"""Admin daily report service for production analytics."""

import logging
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from decimal import Decimal
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc, DECIMAL

from ...models.user import User, UserRole
from ...models.session import Session as TranscriptSession, SessionStatus
from ...models.ecpay_subscription import SaasSubscription
from ..config import Settings

logger = logging.getLogger(__name__)


@dataclass
class DailyReportData:
    """Daily report data structure."""

    # Date range
    report_date: str
    report_period_start: datetime
    report_period_end: datetime

    # User metrics
    total_users: int
    new_users: List[Dict[str, Any]]
    new_users_count: int
    active_users_count: int
    users_by_plan: Dict[str, int]

    # Session & Usage metrics
    total_sessions: int
    completed_sessions: int
    failed_sessions: int
    sessions_by_provider: Dict[str, int]
    total_minutes_processed: Decimal
    total_cost_usd: Decimal

    # Admin & Staff activity
    admin_users: List[Dict[str, Any]]
    staff_logins_today: int

    # Revenue & Billing
    active_subscriptions: Dict[str, int]
    subscription_changes: List[Dict[str, Any]]

    # System health
    error_rate: float
    avg_processing_time_minutes: float

    # Top users by activity
    top_users: List[Dict[str, Any]]


class AdminDailyReportService:
    """Service for generating admin daily reports."""

    def __init__(self, db_session: Session, settings: Settings):
        self.db = db_session
        self.settings = settings
        self.logger = logging.getLogger(
            f"{__name__}.{self.__class__.__name__}"
        )

    def generate_daily_report(
        self, target_date: Optional[datetime] = None
    ) -> DailyReportData:
        """
        Generate comprehensive daily report for admin dashboard.

        Args:
            target_date: Target date for report (defaults to yesterday)

        Returns:
            DailyReportData: Complete daily report data
        """
        if target_date is None:
            target_date = datetime.now(timezone.utc) - timedelta(days=1)

        # Define report period (24 hours ending at midnight of target_date)
        report_start = target_date.replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        report_end = report_start + timedelta(days=1)

        self.logger.info(
            f"📊 Generating daily report for {report_start.date()}"
        )

        try:
            # Gather all metrics - handle database errors gracefully
            user_metrics = self._get_user_metrics(report_start, report_end)
            session_metrics = self._get_session_metrics(
                report_start, report_end
            )
            admin_metrics = self._get_admin_metrics(report_start, report_end)

            # Handle billing metrics which may fail if table doesn't exist
            try:
                billing_metrics = self._get_billing_metrics(
                    report_start, report_end
                )
            except Exception as e:
                self.logger.warning(f"Failed to get billing metrics: {e}")
                # Rollback and try again with a new transaction
                self.db.rollback()
                billing_metrics = {
                    "active_subscriptions": {},
                    "subscription_changes": [],
                }

            system_metrics = self._get_system_health_metrics(
                report_start, report_end
            )
            activity_metrics = self._get_activity_metrics(
                report_start, report_end
            )

            report_data = DailyReportData(
                report_date=report_start.strftime("%Y-%m-%d"),
                report_period_start=report_start,
                report_period_end=report_end,
                **user_metrics,
                **session_metrics,
                **admin_metrics,
                **billing_metrics,
                **system_metrics,
                **activity_metrics,
            )

            self.logger.info(
                f"✅ Daily report generated successfully for {report_start.date()}"
            )
            return report_data

        except Exception as e:
            self.logger.error(f"❌ Failed to generate daily report: {str(e)}")
            raise

    def _get_user_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get user-related metrics."""
        self.logger.debug("📋 Collecting user metrics...")

        # Total users
        total_users = self.db.query(User).count()

        # New users in period
        new_users_query = (
            self.db.query(User)
            .filter(and_(User.created_at >= start, User.created_at < end))
            .order_by(desc(User.created_at))
        )

        new_users = [
            {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "plan": user.plan.value,
                "auth_provider": user.auth_provider,
                "created_at": user.created_at.isoformat(),
                "google_connected": user.google_connected,
            }
            for user in new_users_query.all()
        ]

        # Active users (users who created sessions in period)
        active_users_count = (
            self.db.query(func.count(func.distinct(TranscriptSession.user_id)))
            .filter(
                and_(
                    TranscriptSession.created_at >= start,
                    TranscriptSession.created_at < end,
                )
            )
            .scalar()
            or 0
        )

        # Users by plan
        plan_counts = (
            self.db.query(User.plan, func.count(User.id))
            .group_by(User.plan)
            .all()
        )

        users_by_plan = {plan.value: count for plan, count in plan_counts}

        return {
            "total_users": total_users,
            "new_users": new_users,
            "new_users_count": len(new_users),
            "active_users_count": active_users_count,
            "users_by_plan": users_by_plan,
        }

    def _get_session_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get session and usage metrics."""
        self.logger.debug("📋 Collecting session metrics...")

        # Session counts by status
        sessions_in_period = self.db.query(TranscriptSession).filter(
            and_(
                TranscriptSession.created_at >= start,
                TranscriptSession.created_at < end,
            )
        )

        total_sessions = sessions_in_period.count()
        completed_sessions = sessions_in_period.filter(
            TranscriptSession.status == SessionStatus.COMPLETED
        ).count()
        failed_sessions = sessions_in_period.filter(
            TranscriptSession.status == SessionStatus.FAILED
        ).count()

        # Sessions by STT provider
        provider_counts = (
            self.db.query(
                TranscriptSession.stt_provider,
                func.count(TranscriptSession.id),
            )
            .filter(
                and_(
                    TranscriptSession.created_at >= start,
                    TranscriptSession.created_at < end,
                )
            )
            .group_by(TranscriptSession.stt_provider)
            .all()
        )

        sessions_by_provider = {
            provider or "unknown": count for provider, count in provider_counts
        }

        # Total processing metrics
        usage_stats = (
            self.db.query(
                func.sum(TranscriptSession.duration_seconds),
                func.sum(
                    func.cast(TranscriptSession.stt_cost_usd, DECIMAL(12, 4))
                ),
            )
            .filter(
                and_(
                    TranscriptSession.created_at >= start,
                    TranscriptSession.created_at < end,
                    TranscriptSession.status == SessionStatus.COMPLETED,
                )
            )
            .first()
        )

        total_seconds = (
            usage_stats[0] if usage_stats and usage_stats[0] is not None else 0
        )
        total_minutes_processed = (
            Decimal(str(total_seconds)) / 60 if total_seconds else Decimal("0")
        )
        total_cost_raw = (
            usage_stats[1]
            if usage_stats and usage_stats[1] is not None
            else None
        )
        total_cost_usd = (
            Decimal(str(total_cost_raw))
            if total_cost_raw is not None
            else Decimal("0")
        )

        return {
            "total_sessions": total_sessions,
            "completed_sessions": completed_sessions,
            "failed_sessions": failed_sessions,
            "sessions_by_provider": sessions_by_provider,
            "total_minutes_processed": total_minutes_processed,
            "total_cost_usd": total_cost_usd,
        }

    def _get_admin_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get admin and staff activity metrics."""
        self.logger.debug("📋 Collecting admin metrics...")

        # All admin users
        admin_users_query = (
            self.db.query(User)
            .filter(
                User.role.in_(
                    [UserRole.ADMIN, UserRole.STAFF, UserRole.SUPER_ADMIN]
                )
            )
            .order_by(User.role, User.email)
        )

        admin_users = [
            {
                "id": str(user.id),
                "email": user.email,
                "name": user.name,
                "role": user.role.value,
                "last_admin_login": (
                    user.last_admin_login.isoformat()
                    if user.last_admin_login
                    else None
                ),
                "admin_access_expires": (
                    user.admin_access_expires.isoformat()
                    if user.admin_access_expires
                    else None
                ),
                "created_at": user.created_at.isoformat(),
            }
            for user in admin_users_query.all()
        ]

        # Staff logins today
        staff_logins_today = (
            self.db.query(User)
            .filter(
                and_(
                    User.role.in_(
                        [UserRole.ADMIN, UserRole.STAFF, UserRole.SUPER_ADMIN]
                    ),
                    User.last_admin_login >= start,
                    User.last_admin_login < end,
                )
            )
            .count()
        )

        return {
            "admin_users": admin_users,
            "staff_logins_today": staff_logins_today,
        }

    def _get_billing_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get billing and subscription metrics."""
        self.logger.debug("📋 Collecting billing metrics...")

        # Active subscriptions by plan - handle missing table gracefully
        try:
            subscription_counts = (
                self.db.query(
                    SaasSubscription.plan_name, func.count(SaasSubscription.id)
                )
                .filter(SaasSubscription.status == "active")
                .group_by(SaasSubscription.plan_name)
                .all()
            )

            active_subscriptions = {
                plan or "unknown": count for plan, count in subscription_counts
            }
        except Exception as e:
            self.logger.warning(
                f"Failed to query subscription counts (table may not exist): {e}"
            )
            active_subscriptions = {}

        # Subscription changes in period (new, cancelled, upgraded)
        try:
            subscription_changes = (
                self.db.query(SaasSubscription)
                .filter(
                    or_(
                        and_(
                            SaasSubscription.created_at >= start,
                            SaasSubscription.created_at < end,
                        ),
                        and_(
                            SaasSubscription.updated_at >= start,
                            SaasSubscription.updated_at < end,
                        ),
                    )
                )
                .all()
            )

            changes_summary = [
                {
                    "id": str(sub.id),
                    "user_email": sub.user.email if sub.user else "unknown",
                    "plan_name": sub.plan_name,
                    "status": sub.status,
                    "created_at": sub.created_at.isoformat(),
                    "updated_at": (
                        sub.updated_at.isoformat() if sub.updated_at else None
                    ),
                    "amount": (
                        float(sub.amount_twd) / 100 if sub.amount_twd else 0.0
                    ),  # Convert from cents
                    "billing_cycle": sub.billing_cycle,
                }
                for sub in subscription_changes[:20]  # Limit to recent changes
            ]
        except Exception as e:
            self.logger.warning(
                f"Failed to query subscription changes (table may not exist): {e}"
            )
            changes_summary = []

        return {
            "active_subscriptions": active_subscriptions,
            "subscription_changes": changes_summary,
        }

    def _get_system_health_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get system health and performance metrics."""
        self.logger.debug("📋 Collecting system health metrics...")

        # Calculate error rate
        total_sessions = (
            self.db.query(TranscriptSession)
            .filter(
                and_(
                    TranscriptSession.created_at >= start,
                    TranscriptSession.created_at < end,
                )
            )
            .count()
        )

        failed_sessions = (
            self.db.query(TranscriptSession)
            .filter(
                and_(
                    TranscriptSession.created_at >= start,
                    TranscriptSession.created_at < end,
                    TranscriptSession.status == SessionStatus.FAILED,
                )
            )
            .count()
        )

        error_rate = (
            (failed_sessions / total_sessions * 100)
            if total_sessions > 0
            else 0.0
        )

        # Average processing time (approximation based on completed sessions)
        completed_durations = (
            self.db.query(func.avg(TranscriptSession.duration_seconds))
            .filter(
                and_(
                    TranscriptSession.created_at >= start,
                    TranscriptSession.created_at < end,
                    TranscriptSession.status == SessionStatus.COMPLETED,
                    TranscriptSession.duration_seconds.isnot(None),
                )
            )
            .scalar()
        )

        avg_processing_time_minutes = float(completed_durations or 0) / 60.0

        return {
            "error_rate": error_rate,
            "avg_processing_time_minutes": avg_processing_time_minutes,
        }

    def _get_activity_metrics(
        self, start: datetime, end: datetime
    ) -> Dict[str, Any]:
        """Get top user activity metrics."""
        self.logger.debug("📋 Collecting activity metrics...")

        # Top 10 most active users by sessions created
        top_users_query = (
            self.db.query(
                User,
                func.count(TranscriptSession.id).label("session_count"),
                func.sum(TranscriptSession.duration_seconds).label(
                    "total_seconds"
                ),
                func.count(
                    case(
                        [
                            (
                                TranscriptSession.status
                                == SessionStatus.COMPLETED,
                                1,
                            )
                        ]
                    )
                ).label("completed_sessions"),
            )
            .join(TranscriptSession, User.id == TranscriptSession.user_id)
            .filter(
                and_(
                    TranscriptSession.created_at >= start,
                    TranscriptSession.created_at < end,
                )
            )
            .group_by(User.id)
            .order_by(desc("session_count"))
            .limit(10)
        )

        top_users = [
            {
                "user_id": str(user.id),
                "email": user.email,
                "name": user.name,
                "plan": user.plan.value,
                "sessions_count": session_count,
                "completed_sessions": completed_sessions,
                "total_minutes": float(total_seconds or 0) / 60.0,
                "success_rate": (
                    (completed_sessions / session_count * 100)
                    if session_count > 0
                    else 0.0
                ),
            }
            for user, session_count, total_seconds, completed_sessions in top_users_query.all()
        ]

        return {"top_users": top_users}

    def format_report_for_email(self, report: DailyReportData) -> str:
        """Format report data as HTML email."""

        # Calculate key metrics
        success_rate = (
            (report.completed_sessions / report.total_sessions * 100)
            if report.total_sessions > 0
            else 0
        )

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Daily Admin Report - {report.report_date}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #2563eb; color: white; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 20px 0; padding: 15px; border: 1px solid #e5e5e5; border-radius: 5px; }}
                .metric {{ display: inline-block; margin: 10px 20px 10px 0; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #2563eb; }}
                .metric-label {{ color: #666; font-size: 14px; }}
                .table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                .table th, .table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                .table th {{ background-color: #f5f5f5; }}
                .success {{ color: #16a34a; }}
                .warning {{ color: #ca8a04; }}
                .error {{ color: #dc2626; }}
                .users-list {{ max-height: 200px; overflow-y: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🎯 Daily Admin Report</h1>
                <h2>{report.report_date}</h2>
                <p>Report generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </div>

            <!-- Key Metrics -->
            <div class="section">
                <h3>📊 Key Metrics</h3>
                <div class="metric">
                    <div class="metric-value">{report.total_users}</div>
                    <div class="metric-label">Total Users</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'success' if report.new_users_count > 0 else ''}">{report.new_users_count}</div>
                    <div class="metric-label">New Users</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{report.active_users_count}</div>
                    <div class="metric-label">Active Users</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{report.total_sessions}</div>
                    <div class="metric-label">Total Sessions</div>
                </div>
                <div class="metric">
                    <div class="metric-value {'success' if success_rate > 95 else 'warning' if success_rate > 85 else 'error'}">{success_rate:.1f}%</div>
                    <div class="metric-label">Success Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{float(report.total_minutes_processed):.1f}</div>
                    <div class="metric-label">Minutes Processed</div>
                </div>
                <div class="metric">
                    <div class="metric-value">${float(report.total_cost_usd):.4f}</div>
                    <div class="metric-label">Total Cost</div>
                </div>
            </div>

            <!-- New Users -->
            <div class="section">
                <h3>👥 New Users ({report.new_users_count})</h3>
                {self._format_new_users_table(report.new_users) if report.new_users else '<p>No new users today.</p>'}
            </div>

            <!-- Plan Distribution -->
            <div class="section">
                <h3>💼 Users by Plan</h3>
                <table class="table">
                    <tr><th>Plan</th><th>Count</th><th>Percentage</th></tr>
                    {self._format_plan_distribution(report.users_by_plan, report.total_users)}
                </table>
            </div>

            <!-- Session Metrics -->
            <div class="section">
                <h3>🔄 Session Activity</h3>
                <p><strong>Completed:</strong> {report.completed_sessions} | <strong>Failed:</strong> {report.failed_sessions} | <strong>Other:</strong> {report.total_sessions - report.completed_sessions - report.failed_sessions}</p>
                <p><strong>STT Provider Distribution:</strong></p>
                <ul>
                    {self._format_provider_list(report.sessions_by_provider)}
                </ul>
            </div>

            <!-- Top Users -->
            <div class="section">
                <h3>🏆 Top Active Users</h3>
                {self._format_top_users_table(report.top_users) if report.top_users else '<p>No active users today.</p>'}
            </div>

            <!-- Admin Activity -->
            <div class="section">
                <h3>👨‍💼 Admin & Staff</h3>
                <p><strong>Staff logins today:</strong> {report.staff_logins_today}</p>
                <p><strong>Total admin users:</strong> {len(report.admin_users)}</p>
                <div class="users-list">
                    {self._format_admin_users_list(report.admin_users)}
                </div>
            </div>

            <!-- System Health -->
            <div class="section">
                <h3>🏥 System Health</h3>
                <div class="metric">
                    <div class="metric-value {'success' if report.error_rate < 5 else 'warning' if report.error_rate < 10 else 'error'}">{report.error_rate:.2f}%</div>
                    <div class="metric-label">Error Rate</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{report.avg_processing_time_minutes:.1f}</div>
                    <div class="metric-label">Avg Processing Time (min)</div>
                </div>
            </div>

            <!-- Billing Summary -->
            <div class="section">
                <h3>💰 Billing & Subscriptions</h3>
                <p><strong>Active Subscriptions:</strong></p>
                <ul>
                    {self._format_subscription_list(report.active_subscriptions)}
                </ul>
                <p><strong>Recent Changes:</strong> {len(report.subscription_changes)} subscription events</p>
            </div>

            <div class="section">
                <p><small>Generated by Admin Daily Report Agent | {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}</small></p>
            </div>
        </body>
        </html>
        """

        return html_content

    def _format_new_users_table(self, new_users: List[Dict]) -> str:
        """Format new users as HTML table."""
        if not new_users:
            return "<p>No new users.</p>"

        rows = []
        for user in new_users[:10]:  # Show top 10
            rows.append(
                f"<tr>"
                f"<td>{user['email']}</td>"
                f"<td>{user['name']}</td>"
                f"<td>{user['plan'].upper()}</td>"
                f"<td>{user['auth_provider']}</td>"
                f"<td>{datetime.fromisoformat(user['created_at'].replace('Z', '+00:00')).strftime('%H:%M')}</td>"
                f"</tr>"
            )

        return f"""
        <table class="table">
            <tr><th>Email</th><th>Name</th><th>Plan</th><th>Auth</th><th>Time</th></tr>
            {''.join(rows)}
        </table>
        """

    def _format_plan_distribution(
        self, users_by_plan: Dict[str, int], total_users: int
    ) -> str:
        """Format plan distribution as HTML table rows."""
        rows = []
        for plan, count in users_by_plan.items():
            percentage = (count / total_users * 100) if total_users > 0 else 0
            rows.append(
                f"<tr><td>{plan.upper()}</td><td>{count}</td><td>{percentage:.1f}%</td></tr>"
            )
        return "".join(rows)

    def _format_provider_list(
        self, sessions_by_provider: Dict[str, int]
    ) -> str:
        """Format provider distribution as HTML list items."""
        items = []
        for provider, count in sessions_by_provider.items():
            items.append(
                f"<li><strong>{provider.title()}:</strong> {count} sessions</li>"
            )
        return "".join(items)

    def _format_top_users_table(self, top_users: List[Dict]) -> str:
        """Format top users as HTML table."""
        if not top_users:
            return "<p>No active users.</p>"

        rows = []
        for user in top_users[:5]:  # Show top 5
            rows.append(
                f"<tr>"
                f"<td>{user['email']}</td>"
                f"<td>{user['plan'].upper()}</td>"
                f"<td>{user['sessions_count']}</td>"
                f"<td>{user['completed_sessions']}</td>"
                f"<td>{user['total_minutes']:.1f}</td>"
                f"<td>{user['success_rate']:.1f}%</td>"
                f"</tr>"
            )

        return f"""
        <table class="table">
            <tr><th>Email</th><th>Plan</th><th>Sessions</th><th>Completed</th><th>Minutes</th><th>Success Rate</th></tr>
            {''.join(rows)}
        </table>
        """

    def _format_admin_users_list(self, admin_users: List[Dict]) -> str:
        """Format admin users as HTML list."""
        items = []
        for user in admin_users:
            last_login = (
                "Never"
                if not user["last_admin_login"]
                else datetime.fromisoformat(
                    user["last_admin_login"].replace("Z", "+00:00")
                ).strftime("%Y-%m-%d")
            )
            items.append(
                f"<p><strong>{user['role'].upper()}:</strong> {user['email']} (Last login: {last_login})</p>"
            )
        return "".join(items)

    def _format_subscription_list(
        self, active_subscriptions: Dict[str, int]
    ) -> str:
        """Format subscription distribution as HTML list items."""
        items = []
        for plan, count in active_subscriptions.items():
            items.append(
                f"<li><strong>{plan.upper()}:</strong> {count} active subscriptions</li>"
            )
        return "".join(items)

    def export_report_json(
        self, report: DailyReportData, output_path: str
    ) -> None:
        """Export report data as JSON file."""

        # Convert to serializable format
        report_dict = {
            "report_date": report.report_date,
            "report_period_start": report.report_period_start.isoformat(),
            "report_period_end": report.report_period_end.isoformat(),
            "total_users": report.total_users,
            "new_users": report.new_users,
            "new_users_count": report.new_users_count,
            "active_users_count": report.active_users_count,
            "users_by_plan": report.users_by_plan,
            "total_sessions": report.total_sessions,
            "completed_sessions": report.completed_sessions,
            "failed_sessions": report.failed_sessions,
            "sessions_by_provider": report.sessions_by_provider,
            "total_minutes_processed": float(report.total_minutes_processed),
            "total_cost_usd": float(report.total_cost_usd),
            "admin_users": report.admin_users,
            "staff_logins_today": report.staff_logins_today,
            "active_subscriptions": report.active_subscriptions,
            "subscription_changes": report.subscription_changes,
            "error_rate": report.error_rate,
            "avg_processing_time_minutes": report.avg_processing_time_minutes,
            "top_users": report.top_users,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)

        self.logger.info(f"📄 Report exported to JSON: {output_path}")


# Fix import issue by importing case from sqlalchemy
from sqlalchemy import case, or_
