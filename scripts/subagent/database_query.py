#!/usr/bin/env python3
"""
Claude Code Subagent - 資料庫查詢助手

這是一個簡單的 subagent，讓 Claude Code 可以直接幫您查詢資料庫分析數據。
當您說 "查詢最新狀況" 時，我會使用這個工具來分析系統數據。
"""

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from coaching_assistant.core.database import get_db_session
from coaching_assistant.models.session import (
    Session as TranscriptSession,
)
from coaching_assistant.models.session import (
    SessionStatus,
)
from coaching_assistant.models.user import User, UserPlan


class DatabaseQueryAgent:
    """簡單的資料庫查詢代理，供 Claude Code 使用."""

    def __init__(self):
        self.name = "Database Query Agent"
        self.description = "幫助 Claude Code 查詢和分析系統資料庫"

    def get_system_overview(self) -> Dict[str, Any]:
        """獲取系統總覽數據."""
        try:
            with get_db_session() as db:
                now = datetime.now(timezone.utc)
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

                # 用戶統計
                total_users = db.query(User).count()
                new_users_today = (
                    db.query(User).filter(User.created_at >= today_start).count()
                )

                # 用戶分佈
                free_users = db.query(User).filter(User.plan == UserPlan.FREE).count()
                pro_users = db.query(User).filter(User.plan == UserPlan.PRO).count()
                enterprise_users = (
                    db.query(User).filter(User.plan == UserPlan.ENTERPRISE).count()
                )

                # 會話統計
                total_sessions_today = (
                    db.query(TranscriptSession)
                    .filter(TranscriptSession.created_at >= today_start)
                    .count()
                )

                completed_sessions = (
                    db.query(TranscriptSession)
                    .filter(
                        TranscriptSession.created_at >= today_start,
                        TranscriptSession.status == SessionStatus.COMPLETED,
                    )
                    .count()
                )

                failed_sessions = (
                    db.query(TranscriptSession)
                    .filter(
                        TranscriptSession.created_at >= today_start,
                        TranscriptSession.status == SessionStatus.FAILED,
                    )
                    .count()
                )

                processing_sessions = (
                    db.query(TranscriptSession)
                    .filter(TranscriptSession.status == SessionStatus.PROCESSING)
                    .count()
                )

                # 計算成功率
                success_rate = (
                    (completed_sessions / total_sessions_today * 100)
                    if total_sessions_today > 0
                    else 100
                )

                return {
                    "timestamp": now.isoformat(),
                    "users": {
                        "total": total_users,
                        "new_today": new_users_today,
                        "by_plan": {
                            "free": free_users,
                            "pro": pro_users,
                            "enterprise": enterprise_users,
                        },
                    },
                    "sessions": {
                        "today_total": total_sessions_today,
                        "completed": completed_sessions,
                        "failed": failed_sessions,
                        "processing": processing_sessions,
                        "success_rate": round(success_rate, 1),
                    },
                }
        except Exception as e:
            return {"error": f"資料庫查詢失敗: {str(e)}"}

    def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取最近註冊的用戶."""
        try:
            with get_db_session() as db:
                recent_users = (
                    db.query(User).order_by(User.created_at.desc()).limit(limit).all()
                )

                return [
                    {
                        "id": str(user.id),
                        "email": user.email[:25] + "..."
                        if len(user.email) > 25
                        else user.email,
                        "plan": user.plan.value,
                        "created_at": user.created_at.strftime("%Y-%m-%d %H:%M"),
                        "auth_provider": user.auth_provider
                        if hasattr(user, "auth_provider")
                        else "email",
                    }
                    for user in recent_users
                ]
        except Exception as e:
            return [{"error": f"查詢用戶失敗: {str(e)}"}]

    def get_recent_sessions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取最近的會話."""
        try:
            with get_db_session() as db:
                recent_sessions = (
                    db.query(TranscriptSession)
                    .order_by(TranscriptSession.created_at.desc())
                    .limit(limit)
                    .all()
                )

                return [
                    {
                        "id": str(session.id)[:8] + "...",
                        "title": session.title[:30] + "..."
                        if len(session.title) > 30
                        else session.title,
                        "status": session.status.value,
                        "created_at": session.created_at.strftime("%Y-%m-%d %H:%M"),
                        "duration_minutes": round(session.duration_minutes, 1)
                        if session.duration_seconds
                        else 0,
                        "stt_provider": session.stt_provider or "unknown",
                    }
                    for session in recent_sessions
                ]
        except Exception as e:
            return [{"error": f"查詢會話失敗: {str(e)}"}]

    def get_user_growth_trend(self, days: int = 7) -> Dict[str, Any]:
        """獲取用戶增長趨勢."""
        try:
            with get_db_session() as db:
                now = datetime.now(timezone.utc)
                start_date = now - timedelta(days=days)

                total_users = db.query(User).count()
                new_users_period = (
                    db.query(User).filter(User.created_at >= start_date).count()
                )

                growth_rate = (
                    (new_users_period / (total_users - new_users_period) * 100)
                    if (total_users - new_users_period) > 0
                    else 0
                )

                return {
                    "period_days": days,
                    "total_users": total_users,
                    "new_users": new_users_period,
                    "growth_rate": round(growth_rate, 2),
                    "avg_per_day": round(new_users_period / days, 1),
                }
        except Exception as e:
            return {"error": f"查詢增長趨勢失敗: {str(e)}"}

    def check_system_issues(self) -> Dict[str, Any]:
        """檢查潛在的系統問題."""
        try:
            with get_db_session() as db:
                now = datetime.now(timezone.utc)
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

                issues = []
                warnings = []

                # 檢查處理時間過長的會話
                long_processing = (
                    db.query(TranscriptSession)
                    .filter(
                        TranscriptSession.status == SessionStatus.PROCESSING,
                        TranscriptSession.created_at < now - timedelta(minutes=30),
                    )
                    .count()
                )

                if long_processing > 0:
                    issues.append(f"{long_processing} 個會話處理時間超過30分鐘")

                # 檢查今日失敗率
                total_today = (
                    db.query(TranscriptSession)
                    .filter(TranscriptSession.created_at >= today_start)
                    .count()
                )

                failed_today = (
                    db.query(TranscriptSession)
                    .filter(
                        TranscriptSession.created_at >= today_start,
                        TranscriptSession.status == SessionStatus.FAILED,
                    )
                    .count()
                )

                if total_today > 0:
                    error_rate = failed_today / total_today * 100
                    if error_rate > 15:
                        issues.append(f"今日錯誤率過高: {error_rate:.1f}%")
                    elif error_rate > 5:
                        warnings.append(f"錯誤率略高: {error_rate:.1f}%")

                return {
                    "timestamp": now.isoformat(),
                    "status": "healthy"
                    if not issues
                    else "warning"
                    if not issues and warnings
                    else "issue",
                    "issues": issues,
                    "warnings": warnings,
                    "long_processing_sessions": long_processing,
                    "error_rate": round(error_rate if total_today > 0 else 0, 1),
                }
        except Exception as e:
            return {"error": f"檢查系統問題失敗: {str(e)}"}

    def format_overview_report(self, data: Dict[str, Any]) -> str:
        """格式化系統總覽報告."""
        if "error" in data:
            return f"❌ {data['error']}"

        users = data.get("users", {})
        sessions = data.get("sessions", {})

        report = f"""📊 **系統狀況總覽** ({data.get("timestamp", "N/A")[:19]})

👥 **用戶情況**
• 總用戶數: {users.get("total", 0)}
• 今日新增: {users.get("new_today", 0)}
• 方案分佈: FREE {users.get("by_plan", {}).get("free", 0)} | PRO {users.get("by_plan", {}).get("pro", 0)} | ENTERPRISE {users.get("by_plan", {}).get("enterprise", 0)}

🔄 **會話狀況**
• 今日總數: {sessions.get("today_total", 0)}
• 已完成: {sessions.get("completed", 0)}
• 失敗: {sessions.get("failed", 0)}
• 處理中: {sessions.get("processing", 0)}
• 成功率: {sessions.get("success_rate", 0)}%

💡 **快速分析**
"""

        # 添加簡單的分析
        if sessions.get("success_rate", 0) > 90:
            report += "• ✅ 系統處理性能優秀\n"
        elif sessions.get("success_rate", 0) > 80:
            report += "• 🟡 系統處理性能良好\n"
        else:
            report += "• ⚠️ 系統處理性能需要關注\n"

        if users.get("new_today", 0) > 0:
            report += f"• 📈 今日有 {users.get('new_today', 0)} 位新用戶加入\n"
        else:
            report += "• 📊 今日暫無新用戶註冊\n"

        if sessions.get("processing", 0) > 5:
            report += (
                f"• 🔄 當前有 {sessions.get('processing', 0)} 個會話在處理，系統較忙\n"
            )
        elif sessions.get("processing", 0) > 0:
            report += (
                f"• 🔄 當前有 {sessions.get('processing', 0)} 個會話在處理，正常\n"
            )
        else:
            report += "• 😴 目前沒有會話在處理\n"

        return report


# 創建全域實例供 Claude Code 使用
db_agent = DatabaseQueryAgent()


def query_system_status() -> str:
    """
    Claude Code 專用函數：查詢系統狀況

    這個函數會被 Claude Code 調用來獲取最新的系統狀況。
    """
    print("🔍 Claude Code 正在查詢系統狀況...")

    # 獲取系統總覽
    overview_data = db_agent.get_system_overview()
    overview_report = db_agent.format_overview_report(overview_data)

    return overview_report


def query_recent_activity() -> str:
    """
    Claude Code 專用函數：查詢最近活動
    """
    print("🕐 Claude Code 正在查詢最近活動...")

    recent_users = db_agent.get_recent_users(5)
    recent_sessions = db_agent.get_recent_sessions(5)

    report = "📝 **最近活動**\n\n"

    report += "👥 **最近註冊用戶**\n"
    for user in recent_users[:3]:
        if "error" not in user:
            report += f"• {user['email']} ({user['plan']}, {user['created_at']})\n"

    report += "\n🔄 **最近會話**\n"
    for session in recent_sessions[:3]:
        if "error" not in session:
            report += (
                f"• {session['title']} ({session['status']}, {session['created_at']})\n"
            )

    return report


def query_user_growth() -> str:
    """
    Claude Code 專用函數：查詢用戶增長
    """
    print("📈 Claude Code 正在分析用戶增長...")

    growth_data = db_agent.get_user_growth_trend(7)

    if "error" in growth_data:
        return f"❌ {growth_data['error']}"

    report = f"""📈 **用戶增長分析** (過去7天)

• 總用戶數: {growth_data["total_users"]}
• 新增用戶: {growth_data["new_users"]}
• 增長率: {growth_data["growth_rate"]}%
• 平均每日: {growth_data["avg_per_day"]} 位新用戶

💡 **增長趨勢**: {"📈 快速增長" if growth_data["growth_rate"] > 10 else "📊 穩定增長" if growth_data["growth_rate"] > 0 else "📉 需要關注"}
"""

    return report


def check_system_health() -> str:
    """
    Claude Code 專用函數：檢查系統健康狀況
    """
    print("🏥 Claude Code 正在檢查系統健康狀況...")

    health_data = db_agent.check_system_issues()

    if "error" in health_data:
        return f"❌ {health_data['error']}"

    status_emoji = {"healthy": "🟢", "warning": "🟡", "issue": "🔴"}.get(
        health_data["status"], "⚪"
    )

    report = f"""🏥 **系統健康檢查**

{status_emoji} **總體狀況**: {health_data["status"].upper()}

"""

    if health_data["issues"]:
        report += "🚨 **需要立即處理**\n"
        for issue in health_data["issues"]:
            report += f"• {issue}\n"
        report += "\n"

    if health_data["warnings"]:
        report += "⚠️ **需要關注**\n"
        for warning in health_data["warnings"]:
            report += f"• {warning}\n"
        report += "\n"

    if not health_data["issues"] and not health_data["warnings"]:
        report += "✅ **一切正常，沒有發現問題**\n"

    report += "📊 **關鍵指標**\n"
    report += f"• 處理中會話: {health_data['long_processing_sessions']}\n"
    report += f"• 錯誤率: {health_data['error_rate']}%\n"

    return report


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Claude Code Database Query Agent")
    parser.add_argument(
        "command",
        choices=[
            "query_system_status",
            "query_recent_activity",
            "query_user_growth",
            "check_system_health",
        ],
        help="要執行的查詢命令",
    )
    parser.add_argument("--period", type=int, default=7, help="分析期間（天數）")

    args = parser.parse_args()

    if args.command == "query_system_status":
        print(query_system_status())
    elif args.command == "query_recent_activity":
        print(query_recent_activity())
    elif args.command == "query_user_growth":
        if args.period != 7:
            # Support custom period for user growth
            growth_data = db_agent.get_user_growth_trend(args.period)
            if "error" in growth_data:
                print(f"❌ {growth_data['error']}")
            else:
                report = f"""📈 **用戶增長分析** (過去{args.period}天)

• 總用戶數: {growth_data["total_users"]}
• 新增用戶: {growth_data["new_users"]}
• 增長率: {growth_data["growth_rate"]}%
• 平均每日: {growth_data["avg_per_day"]} 位新用戶

💡 **增長趨勢**: {"📈 快速增長" if growth_data["growth_rate"] > 10 else "📊 穩定增長" if growth_data["growth_rate"] > 0 else "📉 需要關注"}
"""
                print(report)
        else:
            print(query_user_growth())
    elif args.command == "check_system_health":
        print(check_system_health())
