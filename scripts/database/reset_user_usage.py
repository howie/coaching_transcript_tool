#!/usr/bin/env python3
"""
Reset user usage counts for testing purposes.

This script resets session_count and transcription_count to 0 for a specified user,
allowing them to test the upload functionality without being blocked by plan limits.
"""

import argparse
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from coaching_assistant.core.database import get_db_session
from coaching_assistant.models.user import User


def reset_user_usage(
    email: str = None,
    user_id: str = None,
    reset_sessions: bool = True,
    reset_transcriptions: bool = True,
):
    """Reset usage counts for a user."""

    if not email and not user_id:
        print("❌ Error: Must provide either --email or --user-id")
        return False

    with get_db_session() as session:
        try:
            # Find the user
            if email:
                user = session.query(User).filter(User.email == email).first()
                if not user:
                    print(f"❌ Error: User with email '{email}' not found")
                    return False
            else:
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    print(f"❌ Error: User with ID '{user_id}' not found")
                    return False

            print(f"👤 Found user: {user.email} (ID: {user.id})")
            print(
                f"📊 Current usage - Sessions: {user.session_count}, Transcriptions: {user.transcription_count}"
            )
            print(f"📋 Plan: {user.plan.value if user.plan else 'None'}")

            # Reset counts
            changes_made = []

            if reset_sessions and user.session_count > 0:
                user.session_count = 0
                changes_made.append("sessions")

            if reset_transcriptions and user.transcription_count > 0:
                user.transcription_count = 0
                changes_made.append("transcriptions")

            if changes_made:
                print(f"✅ Successfully reset {', '.join(changes_made)} count(s) to 0")
                print(
                    f"📊 New usage - Sessions: {user.session_count}, Transcriptions: {user.transcription_count}"
                )
            else:
                print("ℹ️  No changes needed - usage counts are already 0")

            return True

        except Exception as e:
            print(f"❌ Error resetting usage: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Reset user usage counts for testing purposes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Reset all usage for user by email
  python reset_user_usage.py --email user@example.com
  
  # Reset only session count
  python reset_user_usage.py --email user@example.com --sessions-only
  
  # Reset only transcription count  
  python reset_user_usage.py --email user@example.com --transcriptions-only
  
  # Reset by user ID
  python reset_user_usage.py --user-id 12345678-1234-1234-1234-123456789012
        """,
    )

    # User identification
    user_group = parser.add_mutually_exclusive_group(required=True)
    user_group.add_argument("--email", help="User email address")
    user_group.add_argument("--user-id", help="User ID (UUID)")

    # What to reset
    reset_group = parser.add_mutually_exclusive_group()
    reset_group.add_argument(
        "--sessions-only", action="store_true", help="Reset only session count"
    )
    reset_group.add_argument(
        "--transcriptions-only",
        action="store_true",
        help="Reset only transcription count",
    )

    args = parser.parse_args()

    # Determine what to reset
    reset_sessions = not args.transcriptions_only
    reset_transcriptions = not args.sessions_only

    print("🔄 Resetting user usage counts...")
    success = reset_user_usage(
        email=args.email,
        user_id=args.user_id,
        reset_sessions=reset_sessions,
        reset_transcriptions=reset_transcriptions,
    )

    if success:
        print("🎉 Usage reset completed successfully!")
        print("💡 The user can now create new sessions and transcriptions.")
    else:
        print("💥 Failed to reset usage counts.")
        sys.exit(1)


if __name__ == "__main__":
    main()
