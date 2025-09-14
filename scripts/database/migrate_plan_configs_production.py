#!/usr/bin/env python3
"""
Production migration script for Phase 2 plan configuration updates.
Safely migrates plan configurations to new structure with transaction support.

Features:
- Transaction-based migration with rollback support
- Dry-run mode for testing
- Detailed logging and progress tracking
- Data validation before and after migration
- Support for COACHING_SCHOOL plan addition

Usage:
    python scripts/database/migrate_plan_configs_production.py --dry-run
    python scripts/database/migrate_plan_configs_production.py --execute
"""

import argparse
import json
import sys
from datetime import datetime, UTC
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coaching_assistant.core.config import Settings
from coaching_assistant.core.database import create_database_engine
from sqlalchemy import text, inspect
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlanConfigurationMigrator:
    """Production-ready plan configuration migrator."""
    
    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.settings = Settings()
        self.engine = create_database_engine(self.settings.DATABASE_URL)
        self.migration_log = []
        
    def log_step(self, message: str, level: str = "INFO"):
        """Log migration step with timestamp."""
        timestamp = datetime.now(UTC).isoformat()
        log_entry = {"timestamp": timestamp, "level": level, "message": message}
        self.migration_log.append(log_entry)
        getattr(logger, level.lower())(f"[{timestamp}] {message}")
    
    def validate_pre_migration(self) -> bool:
        """Validate database state before migration."""
        self.log_step("🔍 Pre-migration validation started")
        
        with self.engine.connect() as conn:
            try:
                # Check if plan_configurations table exists
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                
                if 'plan_configurations' not in tables:
                    self.log_step("❌ plan_configurations table not found", "ERROR")
                    return False
                
                # Check existing plans
                result = conn.execute(text("""
                    SELECT plan_type, plan_name, display_name, limits 
                    FROM plan_configurations 
                    ORDER BY sort_order
                """))
                
                existing_plans = list(result)
                self.log_step(f"📋 Found {len(existing_plans)} existing plans")
                
                for plan in existing_plans:
                    self.log_step(f"  - {plan.plan_type}: {plan.display_name}")
                
                # Check user distribution
                user_result = conn.execute(text("""
                    SELECT plan, COUNT(*) as count 
                    FROM "user" 
                    GROUP BY plan
                """))
                
                user_counts = {row.plan: row.count for row in user_result}
                self.log_step(f"👥 User distribution: {user_counts}")
                
                # Validate UserPlan enum
                enum_result = conn.execute(text("""
                    SELECT enumlabel 
                    FROM pg_enum e
                    JOIN pg_type t ON e.enumtypid = t.oid
                    WHERE t.typname = 'userplan'
                    ORDER BY e.enumsortorder
                """))
                
                enum_values = [row.enumlabel for row in enum_result]
                self.log_step(f"🔢 UserPlan enum values: {enum_values}")
                
                # Check if STUDENT already exists
                if 'student' not in [v.lower() for v in enum_values]:
                    self.log_step("⚠️  STUDENT plan not found in enum - need to add it", "WARNING")
                
                self.log_step("✅ Pre-migration validation passed")
                return True
                
            except Exception as e:
                self.log_step(f"❌ Pre-migration validation failed: {e}", "ERROR")
                return False
    
    def get_new_plan_configurations(self) -> List[Dict[str, Any]]:
        """Get the new plan configurations for Phase 2."""
        return [
            {
                "plan_type": "free",
                "plan_name": "free",
                "display_name": "免費試用方案",
                "description": "開始您的教練旅程",
                "tagline": "免費開始使用",
                "limits": {
                    "maxSessions": -1,        # Unlimited sessions
                    "maxMinutes": 200,        # 200 minutes per month
                    "maxTranscriptions": -1,  # Unlimited transcriptions
                    "maxFileSize": 60,        # 60MB per file
                    "retentionDays": 30,
                    "concurrentJobs": 1,
                    "exportFormats": ["json", "txt"]
                },
                "features": {
                    "priority_support": False,
                    "team_collaboration": False,
                    "api_access": False,
                    "advanced_analytics": False
                },
                "monthly_price_twd_cents": 0,
                "annual_price_twd_cents": 0,
                "monthly_price_cents": 0,
                "annual_price_cents": 0,
                "currency": "TWD",
                "is_popular": False,
                "is_enterprise": False,
                "color_scheme": "gray",
                "sort_order": 1,
                "is_active": True,
                "is_visible": True
            },
            {
                "plan_type": "student",
                "plan_name": "student",
                "display_name": "學習方案",
                "description": "學生專屬優惠方案",
                "tagline": "學習者的最佳選擇",
                "limits": {
                    "maxSessions": -1,        # Unlimited sessions
                    "maxMinutes": 500,        # 500 minutes per month
                    "maxTranscriptions": -1,  # Unlimited transcriptions
                    "maxFileSize": 100,       # 100MB per file
                    "retentionDays": 180,     # 6 months
                    "concurrentJobs": 2,
                    "exportFormats": ["json", "txt", "vtt", "srt"]
                },
                "features": {
                    "priority_support": False,
                    "team_collaboration": False,
                    "api_access": False,
                    "advanced_analytics": False
                },
                "monthly_price_twd_cents": 29900,  # 299 TWD
                "annual_price_twd_cents": 299000,  # 2990 TWD (10 months)
                "monthly_price_cents": 999,         # ~$10 USD
                "annual_price_cents": 9990,        # ~$100 USD
                "currency": "TWD",
                "is_popular": False,
                "is_enterprise": False,
                "color_scheme": "green",
                "sort_order": 2,
                "is_active": True,
                "is_visible": True
            },
            {
                "plan_type": "pro",
                "plan_name": "pro",
                "display_name": "專業方案",
                "description": "專業教練的最佳選擇",
                "tagline": "最受歡迎的選擇",
                "limits": {
                    "maxSessions": -1,        # Unlimited sessions
                    "maxMinutes": 3000,       # 3000 minutes per month (50 hours)
                    "maxTranscriptions": -1,  # Unlimited transcriptions
                    "maxFileSize": 200,       # 200MB per file
                    "retentionDays": 365,     # 1 year
                    "concurrentJobs": 3,
                    "exportFormats": ["json", "txt", "vtt", "srt", "docx"]
                },
                "features": {
                    "priority_support": True,
                    "team_collaboration": False,
                    "api_access": False,
                    "advanced_analytics": True
                },
                "monthly_price_twd_cents": 89900,  # 899 TWD
                "annual_price_twd_cents": 899000,  # 8990 TWD (10 months)
                "monthly_price_cents": 2999,       # ~$30 USD
                "annual_price_cents": 29990,       # ~$300 USD
                "currency": "TWD",
                "is_popular": True,
                "is_enterprise": False,
                "color_scheme": "blue",
                "sort_order": 3,
                "is_active": True,
                "is_visible": True
            },
            {
                "plan_type": "coaching_school",  # Updated from enterprise
                "plan_name": "coaching_school",
                "display_name": "認證學校方案",
                "description": "專為 ICF 認證教練學校設計",
                "tagline": "學校專屬解決方案",
                "limits": {
                    "maxSessions": -1,        # Unlimited
                    "maxMinutes": -1,         # Unlimited
                    "maxTranscriptions": -1,  # Unlimited
                    "maxFileSize": 500,       # 500MB per file
                    "retentionDays": -1,      # Permanent
                    "concurrentJobs": 10,
                    "exportFormats": ["json", "txt", "vtt", "srt", "docx", "xlsx", "pdf"]
                },
                "features": {
                    "priority_support": True,
                    "team_collaboration": True,
                    "api_access": True,
                    "advanced_analytics": True,
                    "custom_branding": True,
                    "sso": True
                },
                "monthly_price_twd_cents": 500000,  # 5000 TWD base price
                "annual_price_twd_cents": 4250000,  # 42500 TWD (8.5 months)
                "monthly_price_cents": 16900,       # ~$169 USD
                "annual_price_cents": 143650,       # ~$1436 USD
                "currency": "TWD",
                "is_popular": False,
                "is_enterprise": True,
                "color_scheme": "purple",
                "sort_order": 4,
                "is_active": True,
                "is_visible": True,
                "extra_data": {
                    "base_students": 10,
                    "additional_student_price_twd": 20000,  # 200 TWD per additional student
                    "custom_pricing_available": True,
                    "dedicated_support": True,
                    "onboarding_included": True
                }
            }
        ]
    
    def execute_migration(self) -> bool:
        """Execute the migration with transaction support."""
        if self.dry_run:
            self.log_step("🧪 DRY RUN MODE - No changes will be made")
        
        self.log_step("🚀 Starting plan configuration migration")
        
        new_configs = self.get_new_plan_configurations()
        self.log_step(f"📋 Prepared {len(new_configs)} new plan configurations")
        
        with self.engine.begin() as trans:  # Transaction starts here
            try:
                conn = trans.connection
                
                # Step 1: Backup existing data (in transaction)
                self.log_step("💾 Creating in-transaction backup")
                existing_result = conn.execute(text("SELECT * FROM plan_configurations"))
                existing_configs = [dict(row._mapping) for row in existing_result]
                self.log_step(f"💾 Backed up {len(existing_configs)} existing configurations")
                
                if not self.dry_run:
                    # Step 2: Clear existing configurations
                    self.log_step("🗑️  Clearing existing plan configurations")
                    delete_result = conn.execute(text("DELETE FROM plan_configurations"))
                    self.log_step(f"🗑️  Deleted {delete_result.rowcount} existing configurations")
                    
                    # Step 3: Insert new configurations
                    self.log_step("➕ Inserting new plan configurations")
                    
                    for config in new_configs:
                        insert_sql = text("""
                            INSERT INTO plan_configurations (
                                id, plan_type, plan_name, display_name, description, tagline,
                                limits, features, monthly_price_cents, annual_price_cents,
                                currency, monthly_price_twd_cents, annual_price_twd_cents,
                                is_popular, is_enterprise, color_scheme, sort_order,
                                is_active, is_visible, extra_data, created_at, updated_at
                            ) VALUES (
                                gen_random_uuid(), :plan_type, :plan_name, :display_name, :description, :tagline,
                                :limits, :features, :monthly_price_cents, :annual_price_cents,
                                :currency, :monthly_price_twd_cents, :annual_price_twd_cents,
                                :is_popular, :is_enterprise, :color_scheme, :sort_order,
                                :is_active, :is_visible, :extra_data, NOW(), NOW()
                            )
                        """)
                        
                        conn.execute(insert_sql, {
                            'plan_type': config['plan_type'],
                            'plan_name': config['plan_name'],
                            'display_name': config['display_name'],
                            'description': config['description'],
                            'tagline': config['tagline'],
                            'limits': json.dumps(config['limits']),
                            'features': json.dumps(config['features']),
                            'monthly_price_cents': config['monthly_price_cents'],
                            'annual_price_cents': config['annual_price_cents'],
                            'currency': config['currency'],
                            'monthly_price_twd_cents': config['monthly_price_twd_cents'],
                            'annual_price_twd_cents': config['annual_price_twd_cents'],
                            'is_popular': config['is_popular'],
                            'is_enterprise': config['is_enterprise'],
                            'color_scheme': config['color_scheme'],
                            'sort_order': config['sort_order'],
                            'is_active': config['is_active'],
                            'is_visible': config['is_visible'],
                            'extra_data': json.dumps(config.get('extra_data', {}))
                        })
                        
                        self.log_step(f"  ✅ Inserted {config['display_name']} ({config['plan_type']})")
                
                else:
                    self.log_step("🧪 DRY RUN: Would insert new configurations")
                    for config in new_configs:
                        self.log_step(f"  🧪 Would insert: {config['display_name']} ({config['plan_type']})")
                
                # Step 4: Validate migration results
                if not self.dry_run:
                    validation_result = conn.execute(text("""
                        SELECT plan_type, display_name, 
                               limits->>'maxMinutes' as max_minutes,
                               limits->>'maxSessions' as max_sessions
                        FROM plan_configurations 
                        ORDER BY sort_order
                    """))
                    
                    self.log_step("🔍 Migration validation:")
                    for row in validation_result:
                        self.log_step(f"  ✅ {row.plan_type}: {row.display_name} - {row.max_minutes} min, {row.max_sessions} sessions")
                
                # If dry run, rollback transaction
                if self.dry_run:
                    self.log_step("🧪 DRY RUN: Rolling back transaction")
                    trans.rollback()
                    return True
                
                # Transaction will auto-commit if we reach here
                self.log_step("✅ Migration completed successfully - committing transaction")
                return True
                
            except Exception as e:
                self.log_step(f"❌ Migration failed: {e}", "ERROR")
                self.log_step("🔄 Rolling back transaction", "WARNING")
                trans.rollback()
                return False
    
    def validate_post_migration(self) -> bool:
        """Validate database state after migration."""
        if self.dry_run:
            return True
            
        self.log_step("🔍 Post-migration validation started")
        
        with self.engine.connect() as conn:
            try:
                # Check plan configurations
                result = conn.execute(text("""
                    SELECT plan_type, display_name, 
                           limits->>'maxMinutes' as max_minutes,
                           limits->>'maxSessions' as max_sessions,
                           limits->>'maxTranscriptions' as max_transcriptions
                    FROM plan_configurations 
                    ORDER BY sort_order
                """))
                
                plans = list(result)
                expected_plans = ["free", "student", "pro", "coaching_school"]
                actual_plans = [p.plan_type for p in plans]
                
                if set(actual_plans) != set(expected_plans):
                    self.log_step(f"❌ Plan mismatch. Expected: {expected_plans}, Got: {actual_plans}", "ERROR")
                    return False
                
                # Validate Phase 2 requirements (minutes-only limits)
                for plan in plans:
                    if plan.max_sessions != "-1":
                        self.log_step(f"❌ {plan.plan_type} should have unlimited sessions, got {plan.max_sessions}", "ERROR")
                        return False
                    
                    if plan.max_transcriptions != "-1":
                        self.log_step(f"❌ {plan.plan_type} should have unlimited transcriptions, got {plan.max_transcriptions}", "ERROR")
                        return False
                    
                    if plan.plan_type != "coaching_school" and plan.max_minutes == "-1":
                        self.log_step(f"⚠️  {plan.plan_type} has unlimited minutes - verify this is correct", "WARNING")
                
                self.log_step(f"✅ Post-migration validation passed for {len(plans)} plans")
                return True
                
            except Exception as e:
                self.log_step(f"❌ Post-migration validation failed: {e}", "ERROR")
                return False
    
    def save_migration_log(self):
        """Save migration log to file."""
        timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
        log_dir = Path(__file__).parent / "migration_logs"
        log_dir.mkdir(exist_ok=True)
        
        log_file = log_dir / f"migration_log_{timestamp}.json"
        
        migration_summary = {
            "timestamp": timestamp,
            "dry_run": self.dry_run,
            "success": len([l for l in self.migration_log if "failed" not in l["message"].lower()]) > 0,
            "total_steps": len(self.migration_log),
            "log_entries": self.migration_log
        }
        
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(migration_summary, f, indent=2, ensure_ascii=False)
        
        self.log_step(f"📄 Migration log saved: {log_file}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Migrate plan configurations for Phase 2")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode (no changes)")
    parser.add_argument("--execute", action="store_true", help="Execute the migration")
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print("Error: Must specify either --dry-run or --execute")
        sys.exit(1)
    
    if args.dry_run and args.execute:
        print("Error: Cannot specify both --dry-run and --execute")
        sys.exit(1)
    
    # Create migrator
    migrator = PlanConfigurationMigrator(dry_run=args.dry_run)
    
    try:
        # Pre-migration validation
        if not migrator.validate_pre_migration():
            logger.error("❌ Pre-migration validation failed")
            sys.exit(1)
        
        # Execute migration
        if migrator.execute_migration():
            # Post-migration validation
            if migrator.validate_post_migration():
                migrator.save_migration_log()
                mode = "DRY RUN" if args.dry_run else "PRODUCTION"
                logger.info(f"🎉 Migration completed successfully! ({mode})")
                sys.exit(0)
            else:
                migrator.save_migration_log()
                logger.error("❌ Post-migration validation failed")
                sys.exit(1)
        else:
            migrator.save_migration_log()
            logger.error("❌ Migration execution failed")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Migration script failed: {e}")
        migrator.save_migration_log()
        sys.exit(1)


if __name__ == "__main__":
    main()