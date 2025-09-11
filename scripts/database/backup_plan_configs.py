#!/usr/bin/env python3
"""
Production-ready backup script for plan configurations.
Creates a complete backup of plan_configurations table before migration.

Usage:
    python scripts/database/backup_plan_configs.py
"""

import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coaching_assistant.core.config import Settings
from coaching_assistant.core.database import create_database_engine
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def backup_plan_configurations():
    """Create a complete backup of plan configurations."""
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    backup_dir = Path(__file__).parent / "backups"
    backup_dir.mkdir(exist_ok=True)
    
    backup_file = backup_dir / f"plan_configs_backup_{timestamp}.json"
    
    logger.info("🔄 Starting plan configuration backup...")
    logger.info(f"📁 Backup file: {backup_file}")
    
    settings = Settings()
    engine = create_database_engine(settings.DATABASE_URL)
    
    backup_data = {
        "timestamp": timestamp,
        "database_url": settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else "***",
        "backup_metadata": {
            "script_version": "1.0",
            "purpose": "pre_migration_backup_phase2",
            "migration_target": "minutes_only_limits_with_school_plan"
        },
        "plan_configurations": [],
        "related_data": {}
    }
    
    with engine.connect() as conn:
        # 1. Backup plan_configurations table
        logger.info("📋 Backing up plan_configurations table...")
        
        result = conn.execute(text("""
            SELECT 
                id, plan_type, plan_name, display_name, description, tagline,
                limits, features, monthly_price_cents, annual_price_cents,
                currency, monthly_price_twd_cents, annual_price_twd_cents,
                is_popular, is_enterprise, color_scheme, sort_order,
                is_active, is_visible, extra_data, created_at, updated_at
            FROM plan_configurations 
            ORDER BY sort_order, plan_type
        """))
        
        plan_configs = []
        for row in result:
            config = {
                "id": str(row.id),
                "plan_type": row.plan_type,
                "plan_name": row.plan_name,
                "display_name": row.display_name,
                "description": row.description,
                "tagline": row.tagline,
                "limits": row.limits,
                "features": row.features,
                "pricing": {
                    "monthly_usd": row.monthly_price_cents,
                    "annual_usd": row.annual_price_cents,
                    "monthly_twd": row.monthly_price_twd_cents,
                    "annual_twd": row.annual_price_twd_cents,
                    "currency": row.currency
                },
                "display_config": {
                    "is_popular": row.is_popular,
                    "is_enterprise": row.is_enterprise,
                    "color_scheme": row.color_scheme,
                    "sort_order": row.sort_order
                },
                "status": {
                    "is_active": row.is_active,
                    "is_visible": row.is_visible
                },
                "extra_data": row.extra_data,
                "timestamps": {
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None
                }
            }
            plan_configs.append(config)
        
        backup_data["plan_configurations"] = plan_configs
        logger.info(f"✅ Backed up {len(plan_configs)} plan configurations")
        
        # 2. Backup related user plan distribution
        logger.info("👥 Backing up user plan distribution...")
        
        user_plans_result = conn.execute(text("""
            SELECT plan, COUNT(*) as user_count
            FROM "user"
            GROUP BY plan
            ORDER BY plan
        """))
        
        user_distribution = {}
        total_users = 0
        for row in user_plans_result:
            user_distribution[row.plan] = row.user_count
            total_users += row.user_count
        
        backup_data["related_data"]["user_plan_distribution"] = user_distribution
        backup_data["related_data"]["total_users"] = total_users
        logger.info(f"👥 User distribution: {user_distribution}")
        
        # 3. Backup UserPlan enum values
        logger.info("🔢 Backing up UserPlan enum values...")
        
        enum_result = conn.execute(text("""
            SELECT enumlabel 
            FROM pg_enum e
            JOIN pg_type t ON e.enumtypid = t.oid
            WHERE t.typname = 'userplan'
            ORDER BY e.enumsortorder
        """))
        
        enum_values = [row.enumlabel for row in enum_result]
        backup_data["related_data"]["userplan_enum_values"] = enum_values
        logger.info(f"🔢 UserPlan enum values: {enum_values}")
        
        # 4. Check for any active subscriptions
        logger.info("💳 Backing up active subscriptions summary...")
        
        try:
            subscription_result = conn.execute(text("""
                SELECT plan_id, status, COUNT(*) as count
                FROM saas_subscriptions
                WHERE status IN ('active', 'past_due', 'trialing')
                GROUP BY plan_id, status
                ORDER BY plan_id, status
            """))
            
            active_subscriptions = {}
            for row in subscription_result:
                plan_id = row.plan_id or "unknown"
                if plan_id not in active_subscriptions:
                    active_subscriptions[plan_id] = {}
                active_subscriptions[plan_id][row.status] = row.count
            
            backup_data["related_data"]["active_subscriptions"] = active_subscriptions
            logger.info(f"💳 Active subscriptions: {active_subscriptions}")
            
        except Exception as e:
            logger.warning(f"⚠️  Could not backup subscription data: {e}")
            backup_data["related_data"]["active_subscriptions"] = None
    
    # Write backup to file
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(backup_data, f, indent=2, ensure_ascii=False, default=str)
    
    # Create a summary
    summary = {
        "backup_file": str(backup_file),
        "timestamp": timestamp,
        "plan_count": len(backup_data["plan_configurations"]),
        "total_users": backup_data["related_data"]["total_users"],
        "enum_values": backup_data["related_data"]["userplan_enum_values"],
        "file_size_mb": round(backup_file.stat().st_size / 1024 / 1024, 2)
    }
    
    logger.info("\n" + "="*60)
    logger.info("✅ BACKUP COMPLETED SUCCESSFULLY")
    logger.info("="*60)
    logger.info(f"📁 File: {backup_file}")
    logger.info(f"📊 Plans backed up: {summary['plan_count']}")
    logger.info(f"👥 Total users: {summary['total_users']}")
    logger.info(f"📏 File size: {summary['file_size_mb']} MB")
    logger.info(f"🔢 UserPlan enum: {summary['enum_values']}")
    
    # Save summary for scripts
    summary_file = backup_dir / f"backup_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return backup_file, summary


def verify_backup(backup_file: Path):
    """Verify backup integrity."""
    logger.info(f"🔍 Verifying backup: {backup_file}")
    
    try:
        with open(backup_file, 'r') as f:
            data = json.load(f)
        
        # Basic structure checks
        required_keys = ["timestamp", "plan_configurations", "related_data"]
        for key in required_keys:
            if key not in data:
                raise ValueError(f"Missing required key: {key}")
        
        # Plan data checks
        plans = data["plan_configurations"]
        if not plans:
            raise ValueError("No plan configurations found in backup")
        
        for plan in plans:
            if not plan.get("plan_name") or not plan.get("display_name"):
                raise ValueError(f"Invalid plan data: {plan}")
        
        logger.info(f"✅ Backup verification passed: {len(plans)} plans")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backup verification failed: {e}")
        return False


if __name__ == "__main__":
    try:
        backup_file, summary = backup_plan_configurations()
        
        # Verify backup
        if verify_backup(backup_file):
            logger.info("🎉 Backup and verification completed successfully!")
            print(f"\nBackup file: {backup_file}")
            sys.exit(0)
        else:
            logger.error("❌ Backup verification failed!")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Backup failed: {e}")
        sys.exit(1)