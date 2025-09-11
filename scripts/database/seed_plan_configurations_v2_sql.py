#!/usr/bin/env python3
"""
Phase 2 seed script for plan configurations using raw SQL.
This bypasses SQLAlchemy enum conversion issues.

Usage:
    python scripts/database/seed_plan_configurations_v2_sql.py
"""

import sys
import os
import logging
import json
import uuid
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from coaching_assistant.core.database import SessionLocal
from sqlalchemy import text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_phase2_plan_configurations():
    """Get Phase 2 plan configurations with updated requirements."""
    return [
        {
            # FREE PLAN - 免費試用方案
            "plan_type": "free",  # Use lowercase string directly
            "plan_name": "free",
            "display_name": "免費試用方案",
            "description": "開始您的教練旅程，體驗基本功能",
            "tagline": "免費開始使用",
            "limits": {
                # Phase 2: Only minutes-based limits
                "max_sessions": -1,           # Unlimited sessions
                "max_total_minutes": 200,     # 200 minutes per month
                "max_transcription_count": -1, # Unlimited transcriptions
                "max_file_size_mb": 60,       # 60MB per file
                "export_formats": ["json", "txt"],
                "concurrent_processing": 1,
                "retention_days": 30
            },
            "features": {
                "priority_support": False,
                "team_collaboration": False,
                "api_access": False,
                "sso": False,
                "custom_branding": False,
                "advanced_analytics": False
            },
            "monthly_price_cents": 0,         # Free
            "annual_price_cents": 0,          # Free
            "monthly_price_twd_cents": 0,     # Free
            "annual_price_twd_cents": 0,      # Free
            "currency": "TWD",
            "is_popular": False,
            "is_enterprise": False,
            "color_scheme": "gray",
            "sort_order": 1,
            "is_active": True,
            "is_visible": True,
            "extra_data": {
                "stripe_product_id": None,
                "trial_days": 0,
                "max_team_members": 1,
                "onboarding_video_url": "/onboarding/free-plan"
            }
        },
        {
            # STUDENT PLAN - 學習方案 (NEW)
            "plan_type": "student",  # Use lowercase string directly
            "plan_name": "student",
            "display_name": "學習方案",
            "description": "專為學生設計的優惠方案，支援學習需求",
            "tagline": "學習者的最佳選擇",
            "limits": {
                # Phase 2: Only minutes-based limits
                "max_sessions": -1,           # Unlimited sessions
                "max_total_minutes": 500,     # 500 minutes per month
                "max_transcription_count": -1, # Unlimited transcriptions
                "max_file_size_mb": 100,      # 100MB per file
                "export_formats": ["json", "txt", "vtt", "srt"],
                "concurrent_processing": 2,
                "retention_days": 180         # 6 months
            },
            "features": {
                "priority_support": False,
                "team_collaboration": False,
                "api_access": False,
                "sso": False,
                "custom_branding": False,
                "advanced_analytics": False
            },
            "monthly_price_cents": 999,       # ~$10 USD equivalent
            "annual_price_cents": 9990,       # ~$100 USD equivalent (10 months)
            "monthly_price_twd_cents": 29900, # 299 TWD/month
            "annual_price_twd_cents": 299000, # 2990 TWD/year (10 months price)
            "currency": "TWD",
            "is_popular": False,
            "is_enterprise": False,
            "color_scheme": "green",
            "sort_order": 2,
            "is_active": True,
            "is_visible": True,
            "extra_data": {
                "stripe_product_id": "prod_student_placeholder",
                "stripe_price_id_monthly": "price_student_monthly_placeholder",
                "stripe_price_id_annual": "price_student_annual_placeholder",
                "trial_days": 7,
                "max_team_members": 1,
                "student_verification_required": True,
                "educational_discount": 0.3  # 30% discount from regular pricing
            }
        },
        {
            # PRO PLAN - 專業方案
            "plan_type": "pro",  # Use lowercase string directly
            "plan_name": "pro",
            "display_name": "專業方案",
            "description": "專業教練的完整解決方案，功能齊全",
            "tagline": "最受歡迎的選擇",
            "limits": {
                # Phase 2: Only minutes-based limits
                "max_sessions": -1,           # Unlimited sessions
                "max_total_minutes": 3000,    # 3000 minutes per month (50 hours)
                "max_transcription_count": -1, # Unlimited transcriptions
                "max_file_size_mb": 200,      # 200MB per file
                "export_formats": ["json", "txt", "vtt", "srt", "docx"],
                "concurrent_processing": 3,
                "retention_days": 365         # 1 year
            },
            "features": {
                "priority_support": True,
                "team_collaboration": False,
                "api_access": False,
                "sso": False,
                "custom_branding": False,
                "advanced_analytics": True
            },
            "monthly_price_cents": 2999,      # ~$30 USD equivalent
            "annual_price_cents": 25492,      # ~$255 USD (8.5 months)
            "monthly_price_twd_cents": 89900, # 899 TWD/month
            "annual_price_twd_cents": 764150, # 7641.5 TWD/year (8.5 months price)
            "currency": "TWD",
            "is_popular": True,
            "is_enterprise": False,
            "color_scheme": "blue",
            "sort_order": 3,
            "is_active": True,
            "is_visible": True,
            "extra_data": {
                "stripe_product_id": "prod_pro_placeholder",
                "stripe_price_id_monthly": "price_pro_monthly_placeholder",
                "stripe_price_id_annual": "price_pro_annual_placeholder",
                "trial_days": 14,
                "max_team_members": 1,
                "promotional_discount": 0.15,  # 15% off first 3 months
                "priority_support_response_hours": 24
            }
        },
        {
            # COACHING_SCHOOL PLAN - 認證學校方案 (Updated from ENTERPRISE)
            "plan_type": "coaching_school",  # Use lowercase string directly
            "plan_name": "coaching_school",
            "display_name": "認證學校方案",
            "description": "專為 ICF 認證教練學校設計的企業級解決方案",
            "tagline": "學校專屬，無限可能",
            "limits": {
                # Phase 2: Unlimited everything for schools
                "max_sessions": -1,           # Unlimited
                "max_total_minutes": -1,      # Unlimited
                "max_transcription_count": -1, # Unlimited
                "max_file_size_mb": 500,      # 500MB per file
                "export_formats": ["json", "txt", "vtt", "srt", "docx", "xlsx", "pdf"],
                "concurrent_processing": 10,
                "retention_days": -1          # Permanent retention
            },
            "features": {
                "priority_support": True,
                "team_collaboration": True,
                "api_access": True,
                "sso": True,
                "custom_branding": True,
                "advanced_analytics": True
            },
            "monthly_price_cents": 16900,     # ~$169 USD base price
            "annual_price_cents": 143650,     # ~$1436 USD (8.5 months)
            "monthly_price_twd_cents": 500000, # 5000 TWD base (10 students included)
            "annual_price_twd_cents": 4250000, # 42500 TWD/year (8.5 months)
            "currency": "TWD",
            "is_popular": False,
            "is_enterprise": True,
            "color_scheme": "purple",
            "sort_order": 4,
            "is_active": True,
            "is_visible": True,
            "extra_data": {
                "stripe_product_id": "prod_coaching_school_placeholder",
                "stripe_price_id_monthly": "price_school_monthly_placeholder",
                "stripe_price_id_annual": "price_school_annual_placeholder",
                "trial_days": 30,
                "max_team_members": -1,       # Unlimited team members
                "base_students_included": 10,
                "additional_student_price_twd_cents": 20000,  # 200 TWD per extra student/month
                "sla_response_hours": 4,
                "dedicated_account_manager": True,
                "custom_contract_available": True,
                "onboarding_support_hours": 8,
                "custom_integration_support": True,
                "white_label_available": True,
                "bulk_user_management": True,
                "advanced_reporting": True,
                "data_export_api": True
            }
        }
    ]


def seed_plan_configurations_v2_sql(db):
    """Seed Phase 2 plan configurations using raw SQL."""
    
    logger.info("🌱 Starting Phase 2 plan configuration seeding (SQL method)...")
    
    # Check existing plans
    result = db.execute(text("SELECT COUNT(*) FROM plan_configurations"))
    existing_count = result.scalar()
    logger.info(f"📊 Found {existing_count} existing plan configurations")
    
    # Get Phase 2 configurations
    phase2_configs = get_phase2_plan_configurations()
    logger.info(f"📋 Prepared {len(phase2_configs)} Phase 2 configurations")
    
    # Clear existing configurations
    if existing_count > 0:
        logger.info("🗑️  Clearing existing configurations for clean Phase 2 setup")
        db.execute(text("DELETE FROM plan_configurations"))
        db.flush()
    
    # Insert Phase 2 configurations using raw SQL
    inserted_count = 0
    now = datetime.utcnow()
    
    for config in phase2_configs:
        try:
            plan_id = str(uuid.uuid4())
            
            # Convert JSON fields to strings
            limits_json = json.dumps(config["limits"])
            features_json = json.dumps(config["features"])
            extra_data_json = json.dumps(config["extra_data"])
            
            # Insert using parameterized raw SQL
            insert_sql = text("""
                INSERT INTO plan_configurations 
                (id, plan_type, plan_name, display_name, description, tagline, 
                 limits, features, monthly_price_cents, annual_price_cents, currency,
                 monthly_price_twd_cents, annual_price_twd_cents, is_popular, is_enterprise,
                 color_scheme, sort_order, is_active, is_visible, extra_data,
                 created_at, updated_at)
                VALUES 
                (:id, :plan_type, :plan_name, :display_name, :description, :tagline,
                 (:limits)::JSON, (:features)::JSON, :monthly_price_cents, :annual_price_cents, :currency,
                 :monthly_price_twd_cents, :annual_price_twd_cents, :is_popular, :is_enterprise,
                 :color_scheme, :sort_order, :is_active, :is_visible, (:extra_data)::JSON,
                 :created_at, :updated_at)
            """)
            
            db.execute(insert_sql, {
                "id": plan_id,
                "plan_type": config["plan_type"],  # Direct string - should work with lowercase
                "plan_name": config["plan_name"],
                "display_name": config["display_name"],
                "description": config["description"],
                "tagline": config["tagline"],
                "limits": limits_json,
                "features": features_json,
                "monthly_price_cents": config["monthly_price_cents"],
                "annual_price_cents": config["annual_price_cents"],
                "currency": config["currency"],
                "monthly_price_twd_cents": config["monthly_price_twd_cents"],
                "annual_price_twd_cents": config["annual_price_twd_cents"],
                "is_popular": config["is_popular"],
                "is_enterprise": config["is_enterprise"],
                "color_scheme": config["color_scheme"],
                "sort_order": config["sort_order"],
                "is_active": config["is_active"],
                "is_visible": config["is_visible"],
                "extra_data": extra_data_json,
                "created_at": now,
                "updated_at": now
            })
            
            inserted_count += 1
            logger.info(f"  ➕ Added {config['display_name']} ({config['plan_name']})")
            
        except Exception as e:
            logger.error(f"❌ Failed to add {config['display_name']}: {e}")
            raise
    
    # Commit transaction
    try:
        db.commit()
        logger.info(f"✅ Successfully seeded {inserted_count} Phase 2 plan configurations")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Failed to commit plan configurations: {e}")
        raise


def verify_phase2_seed(db):
    """Verify Phase 2 seed data integrity."""
    logger.info("\n📊 Verifying Phase 2 seed data...")
    
    result = db.execute(text("SELECT * FROM plan_configurations ORDER BY sort_order"))
    plans = result.fetchall()
    
    if len(plans) != 4:
        logger.error(f"❌ Expected 4 plans, found {len(plans)}")
        return False
    
    expected_plans = ["free", "student", "pro", "coaching_school"]
    actual_plans = [plan.plan_name for plan in plans]
    
    if actual_plans != expected_plans:
        logger.error(f"❌ Plan name mismatch. Expected: {expected_plans}, Got: {actual_plans}")
        return False
    
    logger.info(f"✅ Verification passed: {len(plans)} plans configured correctly")
    
    # Detailed verification
    logger.info("\n📋 Plan Details:")
    for plan in plans:
        # Handle limits - could be string or dict
        if isinstance(plan.limits, str):
            limits = json.loads(plan.limits)
        else:
            limits = plan.limits
        pricing_twd = plan.monthly_price_twd_cents / 100 if plan.monthly_price_twd_cents else 0
        
        # Verify Phase 2 requirements
        sessions_limit = limits.get('max_sessions', 0)
        transcriptions_limit = limits.get('max_transcription_count', 0)
        minutes_limit = limits.get('max_total_minutes', 0)
        
        phase2_compliant = (sessions_limit == -1 and transcriptions_limit == -1)
        compliance_status = "✅ Phase 2 Compliant" if phase2_compliant else "❌ Not Phase 2 Compliant"
        
        logger.info(f"\n  🏷️  {plan.display_name} ({plan.plan_name}):")
        logger.info(f"    💰 Price: NT${pricing_twd:.0f}/月")
        logger.info(f"    🎯 Sessions: {'無限制' if sessions_limit == -1 else sessions_limit}")
        logger.info(f"    ⏱️  Minutes: {'無限制' if minutes_limit == -1 else f'{minutes_limit} 分鐘/月'}")
        logger.info(f"    📝 Transcriptions: {'無限制' if transcriptions_limit == -1 else transcriptions_limit}")
        logger.info(f"    📊 File Size: {limits.get('max_file_size_mb', 0)} MB")
        logger.info(f"    🌟 Popular: {'是' if plan.is_popular else '否'}")
        logger.info(f"    🏢 Enterprise: {'是' if plan.is_enterprise else '否'}")
        logger.info(f"    ✅ Status: {compliance_status}")
        
        # Special validation for coaching school plan
        if plan.plan_name == "coaching_school":
            # Handle extra_data - could be string or dict
            if isinstance(plan.extra_data, str):
                extra_data = json.loads(plan.extra_data) if plan.extra_data else {}
            else:
                extra_data = plan.extra_data or {}
            base_students = extra_data.get('base_students_included', 0)
            extra_student_price = extra_data.get('additional_student_price_twd_cents', 0) / 100
            logger.info(f"    🎓 Base Students: {base_students}")
            logger.info(f"    📚 Extra Student Price: NT${extra_student_price:.0f}/月")
    
    return True


def main():
    """Main execution function."""
    logger.info("🚀 Starting Phase 2 Plan Configuration Seeding (SQL Method)")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Seed Phase 2 configurations
        seed_plan_configurations_v2_sql(db)
        
        # Verify the seed
        if verify_phase2_seed(db):
            logger.info("\n🎉 Phase 2 Plan Configuration Seeding Completed Successfully!")
            logger.info("\n📋 Summary:")
            logger.info("  ✅ 免費試用方案 (Free Trial) - 200 分鐘/月")
            logger.info("  ✅ 學習方案 (Learning Plan) - 500 分鐘/月, NT$299/月")  
            logger.info("  ✅ 專業方案 (Professional Plan) - 3000 分鐘/月, NT$899/月")
            logger.info("  ✅ 認證學校方案 (Coaching School Plan) - 無限制, NT$5000/月起")
            logger.info("\n🔥 Phase 2 Features:")
            logger.info("  ✨ 無限制會談數 (Unlimited Sessions)")
            logger.info("  ✨ 無限制轉錄數 (Unlimited Transcriptions)")
            logger.info("  ✨ 僅限制音檔分鐘數 (Minutes-Only Limits)")
            
        else:
            logger.error("❌ Phase 2 seed verification failed!")
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Phase 2 seeding failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()