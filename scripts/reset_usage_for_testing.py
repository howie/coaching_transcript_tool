#!/usr/bin/env python3
"""
Reset Usage for Testing Script

This script resets a user's usage to allow continued testing without hitting plan limits.
It's designed for development/testing purposes only.

Usage:
    python scripts/reset_usage_for_testing.py --user-id USER_ID [--month YYYY-MM]

Features:
- Resets session durations to remove them from usage calculations
- Resets user usage tracking fields
- Preserves all session data and metadata
- Safe for development testing
"""

import argparse
import os
import sys
from datetime import datetime
from uuid import UUID

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from coaching_assistant.core.database import get_db
from coaching_assistant.core.config import settings
from sqlalchemy import text

def reset_user_usage_for_testing(user_id: str, target_month: str = None):
    """Reset user usage for testing purposes.

    Args:
        user_id: UUID string of the user
        target_month: YYYY-MM format (defaults to current month)
    """
    if target_month is None:
        now = datetime.utcnow()
        target_month = now.strftime('%Y-%m')

    year, month = target_month.split('-')
    month_start = f"{year}-{month:0>2}-01"

    print(f"🔄 Resetting usage for user {user_id} for month {target_month}")
    print("=" * 60)

    db_session = next(get_db())

    try:
        # 1. Check current sessions
        print("📋 STEP 1: Checking current sessions...")
        sessions_query = text("""
            SELECT COUNT(*) as session_count,
                   COALESCE(SUM(duration_seconds), 0) as total_seconds
            FROM session
            WHERE user_id = :user_id
                AND created_at >= :month_start
                AND duration_seconds IS NOT NULL
                AND duration_seconds > 0
        """)
        result = db_session.execute(sessions_query, {
            "user_id": user_id,
            "month_start": month_start
        }).fetchone()

        session_count = result[0] if result else 0
        total_seconds = result[1] if result else 0
        total_minutes = total_seconds / 60

        print(f"   📊 Found {session_count} sessions with {total_minutes:.1f} minutes of usage")

        if session_count == 0:
            print("   ✅ No sessions with duration found - already reset")
        else:
            # 2. Reset session durations
            print("\n🔄 STEP 2: Resetting session durations...")
            reset_query = text("""
                UPDATE session
                SET duration_seconds = NULL
                WHERE user_id = :user_id
                    AND created_at >= :month_start
                    AND duration_seconds IS NOT NULL
                    AND duration_seconds > 0
            """)
            reset_result = db_session.execute(reset_query, {
                "user_id": user_id,
                "month_start": month_start
            })
            print(f"   ✅ Reset {reset_result.rowcount} session durations")

        # 3. Reset user tracking fields
        print("\n🔄 STEP 3: Resetting user tracking fields...")
        user_reset_query = text("""
            UPDATE "user"
            SET usage_minutes = 0,
                session_count = 0,
                transcription_count = 0,
                current_month_start = :month_start
            WHERE id = :user_id
        """)
        user_result = db_session.execute(user_reset_query, {
            "user_id": user_id,
            "month_start": month_start
        })
        print(f"   ✅ Reset user tracking fields")

        # 4. Commit changes
        db_session.commit()

        # 5. Verify reset
        print("\n✅ STEP 4: Verifying reset...")
        verify_query = text("""
            SELECT COALESCE(SUM(duration_seconds), 0) as remaining_seconds
            FROM session
            WHERE user_id = :user_id
                AND created_at >= :month_start
                AND duration_seconds IS NOT NULL
        """)
        verify_result = db_session.execute(verify_query, {
            "user_id": user_id,
            "month_start": month_start
        }).fetchone()

        remaining_seconds = verify_result[0] if verify_result else 0
        remaining_minutes = remaining_seconds / 60

        print(f"   📊 Current usage: {remaining_minutes:.1f} minutes")

        if remaining_minutes == 0:
            print("   🎉 SUCCESS: Usage reset complete!")
            print("   ✨ You can now test MP4 uploads without hitting limits")
        else:
            print(f"   ⚠️  WARNING: Still showing {remaining_minutes:.1f} minutes usage")

        print("\n" + "=" * 60)
        print("✅ Reset operation completed successfully")

    except Exception as e:
        db_session.rollback()
        print(f"❌ Error during reset: {e}")
        raise
    finally:
        db_session.close()

def main():
    """Main function to handle command line arguments."""
    parser = argparse.ArgumentParser(
        description="Reset user usage for testing purposes"
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="UUID of the user to reset usage for"
    )
    parser.add_argument(
        "--month",
        help="Target month in YYYY-MM format (defaults to current month)"
    )

    args = parser.parse_args()

    # Validate user ID format
    try:
        UUID(args.user_id)
    except ValueError:
        print(f"❌ Invalid user ID format: {args.user_id}")
        sys.exit(1)

    # Validate month format if provided
    if args.month:
        try:
            datetime.strptime(args.month, '%Y-%m')
        except ValueError:
            print(f"❌ Invalid month format: {args.month}. Use YYYY-MM format.")
            sys.exit(1)

    reset_user_usage_for_testing(args.user_id, args.month)

if __name__ == "__main__":
    main()