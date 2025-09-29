#!/usr/bin/env python3
"""
Beta monitoring script to track usage and costs during beta launch.
Run this periodically to ensure no cost escalation.
"""

from datetime import datetime, timedelta

from sqlalchemy import text

from coaching_assistant.core.config import Settings
from coaching_assistant.core.database import create_database_engine


def check_daily_usage():
    """Check daily usage statistics for beta safety."""
    print(f"🔍 Beta Monitoring Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    settings = Settings()
    engine = create_database_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # 1. User plan distribution
        result = conn.execute(
            text('SELECT plan, COUNT(*) as count FROM "user" GROUP BY plan')
        )
        plan_counts = list(result)
        print("📊 User Plan Distribution:")
        total_users = sum(count for _, count in plan_counts)
        for plan, count in plan_counts:
            percentage = (count / total_users * 100) if total_users > 0 else 0
            print(f"  - {plan}: {count} users ({percentage:.1f}%)")

        # 2. Today's activity
        today = datetime.now().date()
        result = conn.execute(
            text("""
            SELECT 
                COUNT(*) as sessions_created,
                COUNT(CASE WHEN status = 'COMPLETED' THEN 1 END) as transcriptions_completed
            FROM session 
            WHERE DATE(created_at) = :today
        """),
            {"today": today},
        )

        daily_stats = result.fetchone()
        print(f"\n📈 Today's Activity ({today}):")
        print(f"  - Sessions created: {daily_stats[0]}")
        print(f"  - Transcriptions completed: {daily_stats[1]}")

        # 3. User usage statistics
        result = conn.execute(
            text("""
            SELECT 
                plan,
                AVG(session_count) as avg_sessions,
                AVG(transcription_count) as avg_transcriptions,
                AVG(usage_minutes) as avg_minutes,
                MAX(session_count) as max_sessions,
                MAX(transcription_count) as max_transcriptions,
                MAX(usage_minutes) as max_minutes
            FROM "user" 
            GROUP BY plan
        """)
        )

        usage_stats = list(result)
        print("\n📋 Usage Statistics by Plan:")
        for stat in usage_stats:
            plan, avg_s, avg_t, avg_m, max_s, max_t, max_m = stat
            print(f"  - {plan}:")
            print(
                f"    • Avg: {avg_s:.1f} sessions, {avg_t:.1f} transcriptions, {avg_m:.1f} min"
            )
            print(
                f"    • Max: {max_s} sessions, {max_t} transcriptions, {max_m:.1f} min"
            )

        # 4. Users approaching limits
        result = conn.execute(
            text("""
            SELECT email, plan, session_count, transcription_count, usage_minutes
            FROM "user"
            WHERE 
                (plan = 'FREE' AND (session_count >= 2 OR transcription_count >= 4 OR usage_minutes >= 50)) OR
                (plan = 'PRO' AND (session_count >= 20 OR transcription_count >= 40 OR usage_minutes >= 250))
            ORDER BY session_count DESC, transcription_count DESC
        """)
        )

        approaching_limits = list(result)
        print(f"\n⚠️  Users Approaching Limits ({len(approaching_limits)}):")
        if approaching_limits:
            for email, plan, sessions, transcriptions, minutes in approaching_limits:
                print(
                    f"  - {email} ({plan}): {sessions}s, {transcriptions}t, {minutes:.0f}m"
                )
        else:
            print("  - No users approaching limits ✅")

        # 5. Users at or over limits (CRITICAL)
        result = conn.execute(
            text("""
            SELECT email, plan, session_count, transcription_count, usage_minutes
            FROM "user"
            WHERE 
                (plan = 'FREE' AND (session_count >= 3 OR transcription_count >= 5 OR usage_minutes >= 60)) OR
                (plan = 'PRO' AND (session_count >= 25 OR transcription_count >= 50 OR usage_minutes >= 300))
            ORDER BY session_count DESC, transcription_count DESC
        """)
        )

        over_limits = list(result)
        print(f"\n🚨 CRITICAL: Users At/Over Limits ({len(over_limits)}):")
        if over_limits:
            for email, plan, sessions, transcriptions, minutes in over_limits:
                print(
                    f"  - {email} ({plan}): {sessions}s, {transcriptions}t, {minutes:.0f}m"
                )
            print("  ⚠️  THESE USERS SHOULD BE BLOCKED FROM FURTHER USAGE!")
        else:
            print("  - No users over limits ✅")

        # 6. Recent sessions with large files
        result = conn.execute(
            text("""
            SELECT s.title, u.email, s.audio_filename, s.created_at
            FROM session s
            JOIN "user" u ON s.user_id = u.id
            WHERE s.created_at >= :since
            AND s.audio_filename IS NOT NULL
            ORDER BY s.created_at DESC
            LIMIT 10
        """),
            {"since": datetime.now() - timedelta(hours=24)},
        )

        recent_sessions = list(result)
        print(f"\n📁 Recent Sessions (Last 24h): {len(recent_sessions)}")
        for title, email, filename, created in recent_sessions[:5]:
            print(f"  - {created.strftime('%H:%M')} | {email} | {title} | {filename}")

        # 7. Cost estimation (rough)
        total_transcriptions_today = daily_stats[1] or 0
        estimated_cost_today = (
            total_transcriptions_today * 0.10
        )  # Rough $0.10 per transcription
        print(f"\n💰 Estimated Cost Today: ${estimated_cost_today:.2f}")

        if estimated_cost_today > 50:
            print("  🚨 CRITICAL: Daily cost exceeding $50 limit!")
        elif estimated_cost_today > 25:
            print("  ⚠️  WARNING: Daily cost approaching $25")
        else:
            print("  ✅ Daily cost within safe limits")


def check_system_health():
    """Check overall system health indicators."""
    print("\n🔧 System Health Check:")

    settings = Settings()
    engine = create_database_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        # Check for failed sessions
        result = conn.execute(
            text("""
            SELECT COUNT(*) 
            FROM session 
            WHERE status = 'FAILED' 
            AND created_at >= :since
        """),
            {"since": datetime.now() - timedelta(hours=24)},
        )

        failed_sessions = result.scalar()
        print(f"  - Failed sessions (24h): {failed_sessions}")

        # Check for stuck processing sessions
        result = conn.execute(
            text("""
            SELECT COUNT(*) 
            FROM session 
            WHERE status = 'PROCESSING' 
            AND created_at < :stuck_threshold
        """),
            {"stuck_threshold": datetime.now() - timedelta(hours=2)},
        )

        stuck_sessions = result.scalar()
        print(f"  - Stuck processing sessions: {stuck_sessions}")

        if stuck_sessions > 0:
            print("    ⚠️  Some sessions may be stuck in processing")

        # Check database performance
        start_time = datetime.now()
        conn.execute(text("SELECT 1"))
        db_response_time = (datetime.now() - start_time).total_seconds() * 1000
        print(f"  - Database response time: {db_response_time:.1f}ms")

        if db_response_time > 100:
            print("    ⚠️  Database response time high")


def main():
    """Run complete beta monitoring check."""
    try:
        check_daily_usage()
        check_system_health()

        print("\n" + "=" * 60)
        print("✅ Beta monitoring check completed")
        print("Next check recommended in 4 hours")

    except Exception as e:
        print(f"\n❌ Monitoring check failed: {e}")
        print("🚨 CRITICAL: Manual investigation required")


if __name__ == "__main__":
    main()
