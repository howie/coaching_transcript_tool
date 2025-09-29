#!/usr/bin/env python3
"""
Emergency script to reset stuck transcription sessions

This script identifies and resets transcription sessions that have been
stuck in 'processing' status for longer than the specified timeout period.

Usage:
    python scripts/emergency_session_reset.py --timeout 30 --dry-run
    python scripts/emergency_session_reset.py --timeout 30 --execute
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

try:
    from src.coaching_assistant.core.database import get_db
    from src.coaching_assistant.models.session import Session, SessionStatus
except ImportError as e:
    print(f"Error importing modules: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)

import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def reset_stuck_sessions(timeout_minutes=30, dry_run=True):
    """
    Reset sessions stuck in processing state

    Args:
        timeout_minutes (int): Sessions older than this will be reset
        dry_run (bool): If True, only report what would be done

    Returns:
        int: Number of sessions that were (or would be) reset
    """
    logger.info(
        f"Starting session reset check (timeout: {timeout_minutes} minutes, dry_run: {dry_run})"
    )

    try:
        db = next(get_db())
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return 0

    try:
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        logger.info(f"Looking for sessions created before: {cutoff_time}")

        # Find stuck sessions
        stuck_sessions = (
            db.query(Session)
            .filter(
                Session.status == SessionStatus.PROCESSING,
                Session.created_at < cutoff_time,
            )
            .all()
        )

        logger.info(f"Found {len(stuck_sessions)} stuck sessions")

        if not stuck_sessions:
            logger.info("No stuck sessions found - system is healthy!")
            return 0

        # Process each stuck session
        for i, session in enumerate(stuck_sessions, 1):
            processing_time = datetime.now() - session.created_at
            processing_hours = processing_time.total_seconds() / 3600

            logger.info(f"Session {i}/{len(stuck_sessions)}: {session.id}")
            logger.info(f"  - User ID: {session.user_id}")
            logger.info(f"  - Created: {session.created_at}")
            logger.info(f"  - Processing time: {processing_hours:.1f} hours")
            logger.info(f"  - Current status: {session.status}")

            if hasattr(session, "audio_file_name") and session.audio_file_name:
                logger.info(f"  - File: {session.audio_file_name}")

            if not dry_run:
                # Update session status
                old_status = session.status
                session.status = SessionStatus.FAILED
                session.error_message = f"Session timeout after {processing_time} - automatically reset by emergency script"
                session.updated_at = datetime.now()

                logger.info(f"  ✅ Reset session {session.id}: {old_status} -> failed")
            else:
                logger.info(f"  🔍 Would reset session {session.id} (dry run)")

        if not dry_run:
            # Commit all changes
            db.commit()
            logger.info(
                f"✅ Successfully committed changes - reset {len(stuck_sessions)} sessions"
            )
        else:
            logger.info(
                f"🔍 DRY RUN complete - found {len(stuck_sessions)} sessions that would be reset"
            )

        return len(stuck_sessions)

    except Exception as e:
        logger.error(f"Error during session reset: {e}")
        if not dry_run:
            db.rollback()
            logger.info("Database changes rolled back due to error")
        return 0

    finally:
        db.close()
        logger.info("Database connection closed")


def verify_reset_results():
    """Verify that no sessions are still stuck in processing"""
    logger.info("Verifying reset results...")

    try:
        db = next(get_db())

        # Count remaining processing sessions
        processing_count = (
            db.query(Session).filter(Session.status == SessionStatus.PROCESSING).count()
        )

        if processing_count == 0:
            logger.info("✅ Verification successful: No sessions in processing status")
        else:
            logger.warning(
                f"⚠️  Warning: {processing_count} sessions still in processing status"
            )

            # Show details of remaining processing sessions
            remaining_sessions = (
                db.query(Session)
                .filter(Session.status == SessionStatus.PROCESSING)
                .all()
            )

            for session in remaining_sessions:
                age = datetime.now() - session.created_at
                logger.warning(f"  - Session {session.id}: {age} old")

        # Show summary statistics
        total_sessions = db.query(Session).count()
        failed_sessions = (
            db.query(Session).filter(Session.status == SessionStatus.FAILED).count()
        )
        completed_sessions = (
            db.query(Session).filter(Session.status == SessionStatus.COMPLETED).count()
        )

        logger.info("Session Status Summary:")
        logger.info(f"  - Total: {total_sessions}")
        logger.info(f"  - Completed: {completed_sessions}")
        logger.info(f"  - Failed: {failed_sessions}")
        logger.info(f"  - Processing: {processing_count}")

        db.close()
        return processing_count == 0

    except Exception as e:
        logger.error(f"Error during verification: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Reset stuck transcription sessions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check what would be reset (safe)
  python scripts/emergency_session_reset.py --timeout 30 --dry-run
  
  # Actually reset stuck sessions
  python scripts/emergency_session_reset.py --timeout 30 --execute
  
  # Check for very old sessions (6 hours)
  python scripts/emergency_session_reset.py --timeout 360 --dry-run
        """,
    )

    parser.add_argument(
        "--timeout", type=int, default=30, help="Timeout in minutes (default: 30)"
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually execute changes (default: dry run)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Only show what would be done (default behavior)",
    )

    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify that no sessions are stuck (use after reset)",
    )

    args = parser.parse_args()

    # Handle conflicting flags
    if args.execute and args.dry_run:
        logger.error("Cannot specify both --execute and --dry-run")
        sys.exit(1)

    # Determine if this is a dry run
    dry_run = not args.execute

    if args.verify:
        # Just run verification
        success = verify_reset_results()
        sys.exit(0 if success else 1)

    # Show warning for execute mode
    if not dry_run:
        print("\n" + "=" * 50)
        print("⚠️  PRODUCTION DATABASE MODIFICATION WARNING ⚠️")
        print("=" * 50)
        print("This will MODIFY the production database!")
        print(
            f"Sessions older than {args.timeout} minutes will be reset to 'failed' status."
        )
        print("\nAre you sure you want to continue? (yes/no)")

        confirmation = input().strip().lower()
        if confirmation not in ["yes", "y"]:
            print("Operation cancelled.")
            sys.exit(0)
        print()

    # Run the reset
    count = reset_stuck_sessions(args.timeout, dry_run)

    if dry_run:
        print(f"\n📋 Summary: Found {count} sessions that would be reset")
        print("Use --execute to actually reset these sessions")
        if count > 0:
            print(f"Command: python {' '.join(sys.argv)} --execute")
    else:
        print(f"\n✅ Summary: Successfully reset {count} sessions")
        if count > 0:
            print("Running verification...")
            verify_reset_results()

    sys.exit(0)


if __name__ == "__main__":
    main()
