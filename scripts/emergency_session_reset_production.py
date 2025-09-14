#!/usr/bin/env python3
"""
Emergency script to reset stuck production transcription sessions

This script specifically connects to the production database and resets
sessions that have been stuck in 'processing' status.

Usage:
    python scripts/emergency_session_reset_production.py --dry-run
    python scripts/emergency_session_reset_production.py --execute
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Production database URL
PRODUCTION_DB_URL = "postgresql://coachly_user:***REMOVED***@dpg-d27igr7diees73cla8og-a.singapore-postgres.render.com/coachly"

def get_production_db():
    """Create connection to production database"""
    engine = create_engine(PRODUCTION_DB_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()

def reset_stuck_sessions_sql(timeout_minutes=30, dry_run=True):
    """
    Reset sessions stuck in processing state using direct SQL
    
    Args:
        timeout_minutes (int): Sessions older than this will be reset
        dry_run (bool): If True, only report what would be done
        
    Returns:
        int: Number of sessions that were (or would be) reset
    """
    logger.info(f"🔗 Connecting to production database...")
    logger.info(f"📊 Checking for sessions stuck longer than {timeout_minutes} minutes")
    
    try:
        db = get_production_db()
    except Exception as e:
        logger.error(f"❌ Failed to connect to production database: {e}")
        return 0
    
    try:
        cutoff_time = datetime.now() - timedelta(minutes=timeout_minutes)
        logger.info(f"⏰ Cutoff time: {cutoff_time}")
        
        # Query stuck sessions using raw SQL
        query = text("""
            SELECT 
                id,
                user_id,
                title,
                status,
                created_at,
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_stuck
            FROM sessions 
            WHERE status = 'processing' 
              AND created_at < :cutoff_time
            ORDER BY created_at
        """)
        
        result = db.execute(query, {"cutoff_time": cutoff_time})
        stuck_sessions = result.fetchall()
        
        logger.info(f"🔍 Found {len(stuck_sessions)} stuck sessions")
        
        if not stuck_sessions:
            logger.info("✅ No stuck sessions found - system is healthy!")
            return 0
        
        # Display details of stuck sessions
        for i, session in enumerate(stuck_sessions, 1):
            hours_stuck = session.minutes_stuck / 60
            days_stuck = hours_stuck / 24
            
            logger.info(f"")
            logger.info(f"🚨 Session {i}/{len(stuck_sessions)}: {session.id}")
            logger.info(f"   👤 User ID: {session.user_id}")
            logger.info(f"   📝 Title: {session.title or 'No title'}")
            logger.info(f"   ⏱️  Created: {session.created_at}")
            logger.info(f"   🕐 Updated: {session.updated_at}")
            logger.info(f"   ⏳ Stuck for: {session.minutes_stuck:.0f} minutes ({hours_stuck:.1f} hours / {days_stuck:.1f} days)")
        
        if not dry_run:
            # Update sessions using raw SQL
            logger.info(f"")
            logger.info(f"🔧 Resetting {len(stuck_sessions)} stuck sessions...")
            
            update_query = text("""
                UPDATE sessions 
                SET 
                    status = 'failed',
                    error_message = :error_message,
                    updated_at = NOW()
                WHERE status = 'processing' 
                  AND created_at < :cutoff_time
            """)
            
            error_message = f'Session timeout after processing for more than {timeout_minutes} minutes - automatically reset by emergency script on {datetime.now().isoformat()}'
            
            result = db.execute(update_query, {
                "error_message": error_message,
                "cutoff_time": cutoff_time
            })
            
            rows_affected = result.rowcount
            db.commit()
            
            logger.info(f"✅ Successfully reset {rows_affected} sessions")
            
            if rows_affected != len(stuck_sessions):
                logger.warning(f"⚠️  Warning: Expected to reset {len(stuck_sessions)} sessions but actually reset {rows_affected}")
        else:
            logger.info(f"")
            logger.info(f"🔍 DRY RUN: Would reset {len(stuck_sessions)} sessions")
            logger.info(f"💡 Use --execute to actually reset these sessions")
        
        return len(stuck_sessions)
        
    except Exception as e:
        logger.error(f"❌ Error during session reset: {e}")
        if not dry_run:
            db.rollback()
            logger.info("🔄 Database changes rolled back due to error")
        return 0
        
    finally:
        db.close()
        logger.info("🔌 Database connection closed")

def verify_reset_results():
    """Verify that sessions were reset successfully"""
    logger.info("🔍 Verifying reset results...")
    
    try:
        db = get_production_db()
        
        # Count sessions by status
        status_query = text("""
            SELECT 
                status,
                COUNT(*) as count
            FROM sessions 
            GROUP BY status
            ORDER BY status
        """)
        
        result = db.execute(status_query)
        status_counts = result.fetchall()
        
        logger.info("📊 Session Status Summary:")
        total_sessions = 0
        processing_count = 0
        
        for status_row in status_counts:
            count = status_row.count
            total_sessions += count
            if status_row.status == 'processing':
                processing_count = count
            logger.info(f"   📋 {status_row.status}: {count}")
        
        logger.info(f"   📊 Total: {total_sessions}")
        
        # Check for any remaining stuck sessions
        stuck_query = text("""
            SELECT 
                id,
                EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_stuck
            FROM sessions 
            WHERE status = 'processing' 
              AND created_at < NOW() - INTERVAL '30 minutes'
        """)
        
        result = db.execute(stuck_query)
        remaining_stuck = result.fetchall()
        
        if remaining_stuck:
            logger.warning(f"⚠️  Warning: {len(remaining_stuck)} sessions still stuck!")
            for session in remaining_stuck:
                logger.warning(f"   🚨 Session {session.id}: {session.minutes_stuck:.0f} minutes")
        else:
            logger.info("✅ Verification successful: No sessions stuck > 30 minutes")
        
        db.close()
        return len(remaining_stuck) == 0
        
    except Exception as e:
        logger.error(f"❌ Error during verification: {e}")
        return False

def list_all_processing_sessions():
    """List all current processing sessions"""
    logger.info("📋 Listing all processing sessions...")
    
    try:
        db = get_production_db()
        
        query = text("""
            SELECT 
                id,
                user_id,
                title,
                status,
                created_at,
                updated_at,
                EXTRACT(EPOCH FROM (NOW() - created_at))/60 as minutes_processing
            FROM sessions 
            WHERE status = 'processing'
            ORDER BY created_at
        """)
        
        result = db.execute(query)
        processing_sessions = result.fetchall()
        
        if not processing_sessions:
            logger.info("✅ No sessions currently in processing status")
            return
        
        logger.info(f"🔍 Found {len(processing_sessions)} sessions in processing status:")
        
        for i, session in enumerate(processing_sessions, 1):
            hours = session.minutes_processing / 60
            days = hours / 24
            
            status_emoji = "🚨" if session.minutes_processing > 30 else "⏳"
            
            logger.info(f"")
            logger.info(f"{status_emoji} Session {i}: {session.id}")
            logger.info(f"   👤 User: {session.user_id}")
            logger.info(f"   📝 Title: {session.title or 'No title'}")
            logger.info(f"   ⏱️  Created: {session.created_at}")
            logger.info(f"   🕐 Updated: {session.updated_at}")
            logger.info(f"   ⏳ Processing: {session.minutes_processing:.0f} min ({hours:.1f}h / {days:.1f}d)")
        
        db.close()
        
    except Exception as e:
        logger.error(f"❌ Error listing sessions: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Reset stuck production transcription sessions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
🚨 PRODUCTION DATABASE WARNING 🚨
This script connects directly to the production database!

Examples:
  # List all processing sessions
  python scripts/emergency_session_reset_production.py --list
  
  # Check what would be reset (safe)
  python scripts/emergency_session_reset_production.py --dry-run
  
  # Actually reset stuck sessions
  python scripts/emergency_session_reset_production.py --execute
  
  # Verify after reset
  python scripts/emergency_session_reset_production.py --verify
        """
    )
    
    parser.add_argument(
        '--timeout', 
        type=int, 
        default=30, 
        help='Timeout in minutes (default: 30)'
    )
    
    parser.add_argument(
        '--execute', 
        action='store_true', 
        help='Actually execute changes (PRODUCTION)'
    )
    
    parser.add_argument(
        '--dry-run', 
        action='store_true', 
        help='Only show what would be done (default)'
    )
    
    parser.add_argument(
        '--verify', 
        action='store_true', 
        help='Verify no sessions are stuck'
    )
    
    parser.add_argument(
        '--list', 
        action='store_true', 
        help='List all current processing sessions'
    )
    
    args = parser.parse_args()
    
    print("🚨" + "="*60 + "🚨")
    print("🚨  PRODUCTION DATABASE EMERGENCY SCRIPT  🚨")
    print("🚨" + "="*60 + "🚨")
    print(f"Database: dpg-d27igr7diees73cla8og-a.singapore-postgres.render.com")
    print(f"Database: coachly")
    print("")
    
    if args.list:
        list_all_processing_sessions()
        return
    
    if args.verify:
        success = verify_reset_results()
        sys.exit(0 if success else 1)
    
    # Handle conflicting flags
    if args.execute and args.dry_run:
        logger.error("❌ Cannot specify both --execute and --dry-run")
        sys.exit(1)
    
    # Determine if this is a dry run
    dry_run = not args.execute
    
    # Show extra warning for execute mode
    if not dry_run:
        print("⚠️ " + "="*50 + " ⚠️")
        print("⚠️   PRODUCTION DATABASE MODIFICATION WARNING   ⚠️")
        print("⚠️ " + "="*50 + " ⚠️")
        print(f"This will MODIFY the production database!")
        print(f"Sessions older than {args.timeout} minutes will be reset to 'failed'.")
        print(f"")
        print("Type 'RESET PRODUCTION' to confirm:")
        
        confirmation = input().strip()
        if confirmation != 'RESET PRODUCTION':
            print("❌ Operation cancelled.")
            sys.exit(0)
        print()
    
    # Run the reset
    count = reset_stuck_sessions_sql(args.timeout, dry_run)
    
    print("")
    print("📋 " + "="*50)
    if dry_run:
        print(f"📋 DRY RUN SUMMARY: Found {count} sessions that would be reset")
        if count > 0:
            print(f"💡 Use --execute to actually reset these sessions")
            print(f"⚠️  Make sure to backup the database first!")
    else:
        print(f"✅ EXECUTION SUMMARY: Successfully reset {count} sessions")
        if count > 0:
            print("🔍 Running verification...")
            verify_reset_results()
    print("📋 " + "="*50)
    
    sys.exit(0)

if __name__ == "__main__":
    main()