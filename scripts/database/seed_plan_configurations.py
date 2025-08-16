#!/usr/bin/env python3
"""
Seed script to populate PlanConfiguration table with initial billing plans.
Run this after applying the database migration.

Usage:
    python scripts/seed_plan_configurations.py
"""

import sys
import os
import logging
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from coaching_assistant.core.database import engine, SessionLocal
from coaching_assistant.models.plan_configuration import PlanConfiguration
from coaching_assistant.models.user import UserPlan

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def seed_plan_configurations(db: Session):
    """Seed the database with initial plan configurations."""
    
    # Check if plans already exist
    existing_plans = db.query(PlanConfiguration).count()
    if existing_plans > 0:
        logger.info(f"Found {existing_plans} existing plan configurations. Skipping seed.")
        return
    
    logger.info("🌱 Seeding plan configurations...")
    
    # Free Plan
    free_plan = PlanConfiguration(
        plan_type=UserPlan.FREE,
        plan_name="free",
        display_name="免費試用",
        description="適合剛開始使用平台的教練",
        tagline="免費開始使用",
        limits={
            "max_sessions": 10,
            "max_total_minutes": 120,
            "max_transcription_count": 20,
            "max_file_size_mb": 50,
            "export_formats": ["json", "txt"],
            "concurrent_processing": 1,
            "retention_days": 30
        },
        features={
            "priority_support": False,
            "team_collaboration": False,
            "api_access": False,
            "sso": False,
            "custom_branding": False,
            "advanced_analytics": False
        },
        monthly_price_cents=0,
        annual_price_cents=0,
        monthly_price_twd_cents=0,
        annual_price_twd_cents=0,
        currency="USD",
        is_popular=False,
        is_enterprise=False,
        color_scheme="gray",
        sort_order=1,
        is_active=True,
        is_visible=True,
        extra_data={
            "stripe_product_id": None,
            "trial_days": 0,
            "max_team_members": 1
        }
    )
    
    # Pro Plan
    pro_plan = PlanConfiguration(
        plan_type=UserPlan.PRO,
        plan_name="pro",
        display_name="專業版",
        description="適合專業教練的完整功能",
        tagline="最受歡迎的選擇",
        limits={
            "max_sessions": 100,
            "max_total_minutes": 1200,
            "max_transcription_count": 200,
            "max_file_size_mb": 200,
            "export_formats": ["json", "txt", "vtt", "srt", "docx"],
            "concurrent_processing": 3,
            "retention_days": 365
        },
        features={
            "priority_support": True,
            "team_collaboration": False,
            "api_access": False,
            "sso": False,
            "custom_branding": False,
            "advanced_analytics": True
        },
        monthly_price_cents=2999,  # $29.99
        annual_price_cents=2499,   # $24.99/month when paid annually
        monthly_price_twd_cents=79000,  # NT$790
        annual_price_twd_cents=63200,   # NT$632/month when paid annually
        currency="USD",
        is_popular=True,
        is_enterprise=False,
        color_scheme="blue",
        sort_order=2,
        is_active=True,
        is_visible=True,
        extra_data={
            "stripe_product_id": "prod_pro_placeholder",
            "stripe_price_id_monthly": "price_pro_monthly_placeholder",
            "stripe_price_id_annual": "price_pro_annual_placeholder",
            "trial_days": 14,
            "max_team_members": 1,
            "promotional_discount": 0.2  # 20% off first month
        }
    )
    
    # Business/Enterprise Plan
    business_plan = PlanConfiguration(
        plan_type=UserPlan.ENTERPRISE,
        plan_name="business",
        display_name="企業版",
        description="適合教練團隊和組織",
        tagline="擴展您的團隊",
        limits={
            "max_sessions": -1,  # Unlimited
            "max_total_minutes": -1,  # Unlimited
            "max_transcription_count": -1,  # Unlimited
            "max_file_size_mb": 500,
            "export_formats": ["json", "txt", "vtt", "srt", "docx", "xlsx", "pdf"],
            "concurrent_processing": 10,
            "retention_days": -1  # Permanent
        },
        features={
            "priority_support": True,
            "team_collaboration": True,
            "api_access": True,
            "sso": True,
            "custom_branding": True,
            "advanced_analytics": True
        },
        monthly_price_cents=9999,  # $99.99
        annual_price_cents=8333,   # $83.33/month when paid annually
        monthly_price_twd_cents=189000,  # NT$1,890
        annual_price_twd_cents=157500,   # NT$1,575/month when paid annually
        currency="USD",
        is_popular=False,
        is_enterprise=True,
        color_scheme="purple",
        sort_order=3,
        is_active=True,
        is_visible=True,
        extra_data={
            "stripe_product_id": "prod_business_placeholder",
            "stripe_price_id_monthly": "price_business_monthly_placeholder",
            "stripe_price_id_annual": "price_business_annual_placeholder",
            "trial_days": 30,
            "max_team_members": -1,  # Unlimited
            "sla_response_hours": 4,
            "dedicated_account_manager": True,
            "custom_contract_available": True
        }
    )
    
    # Add all plans to the database
    db.add(free_plan)
    db.add(pro_plan)
    db.add(business_plan)
    
    try:
        db.commit()
        logger.info("✅ Successfully seeded 3 plan configurations:")
        logger.info("  - Free Trial (免費試用)")
        logger.info("  - Pro Plan (專業版)")
        logger.info("  - Business Plan (企業版)")
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error seeding plan configurations: {e}")
        raise


def verify_seed(db: Session):
    """Verify that the seed data was inserted correctly."""
    plans = db.query(PlanConfiguration).all()
    
    logger.info("\n📊 Verification Report:")
    logger.info(f"Total plans in database: {len(plans)}")
    
    for plan in plans:
        logger.info(f"\n  {plan.display_name} ({plan.plan_name}):")
        logger.info(f"    - Type: {plan.plan_type.value}")
        logger.info(f"    - Monthly Price: ${plan.monthly_price_cents/100:.2f} USD / NT${plan.monthly_price_twd_cents/100:.0f} TWD")
        logger.info(f"    - Annual Price: ${plan.annual_price_cents/100:.2f} USD / NT${plan.annual_price_twd_cents/100:.0f} TWD")
        logger.info(f"    - Max Sessions: {plan.limits['max_sessions'] if plan.limits['max_sessions'] != -1 else 'Unlimited'}")
        logger.info(f"    - Max Minutes: {plan.limits['max_total_minutes'] if plan.limits['max_total_minutes'] != -1 else 'Unlimited'}")
        logger.info(f"    - Popular: {'Yes' if plan.is_popular else 'No'}")
        logger.info(f"    - Active: {'Yes' if plan.is_active else 'No'}")


def main():
    """Main function to run the seed script."""
    logger.info("🚀 Starting Plan Configuration Seed Script")
    logger.info(f"Database URL: {os.getenv('DATABASE_URL', 'Not configured')}")
    
    # Create database session
    db = SessionLocal()
    
    try:
        # Seed the data
        seed_plan_configurations(db)
        
        # Verify the seed
        verify_seed(db)
        
        logger.info("\n✅ Seed script completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Seed script failed: {e}")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()