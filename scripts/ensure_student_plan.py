#!/usr/bin/env python3
"""
Script to ensure STUDENT plan configuration exists in database.
Fixes Bug: STUDENT plan not appearing in billing page.
"""

import os
import sys
import logging
from uuid import uuid4

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, 'src'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from coaching_assistant.infrastructure.db.models.plan_configuration_model import PlanConfigurationModel
from coaching_assistant.models.user import UserPlan

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_student_plan_config():
    """Create STUDENT plan configuration if it doesn't exist."""

    # Get database URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False

    # Create database connection
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    with SessionLocal() as db:
        try:
            # Check if STUDENT plan already exists
            existing_plan = db.query(PlanConfigurationModel).filter(
                PlanConfigurationModel.plan_type == 'student'
            ).first()

            if existing_plan:
                logger.info("✅ STUDENT plan configuration already exists")
                logger.info(f"   Display name: {existing_plan.display_name}")
                return True

            # Create STUDENT plan configuration
            student_plan = PlanConfigurationModel(
                id=uuid4(),
                plan_type='student',  # Database expects lowercase string
                display_name='學習方案',  # Chinese display name
                description='學生專用轉錄方案，適合學習和練習使用',
                is_active=True,
                limits={
                    "max_sessions": 20,
                    "max_total_minutes": 600,  # 10 hours
                    "max_transcription_count": 20,
                    "max_file_size_mb": 100,
                    "export_formats": ["json", "txt", "vtt"],
                    "concurrent_processing": 1,
                    "retention_days": 30
                },
                features={
                    "priority_support": False,
                    "team_collaboration": False,
                    "api_access": False,
                    "sso": False,
                    "custom_branding": False
                },
                pricing={
                    "monthly_price_cents": 29900,  # $299 USD
                    "annual_price_cents": 299000,  # $2990 USD (10 months price)
                    "monthly_price_twd_cents": 95900,  # NT$959
                    "annual_price_twd_cents": 959000,  # NT$9590
                    "currency": "USD"
                }
            )

            db.add(student_plan)
            db.commit()

            logger.info("✅ STUDENT plan configuration created successfully")
            logger.info(f"   ID: {student_plan.id}")
            logger.info(f"   Display name: {student_plan.display_name}")
            logger.info(f"   Max sessions: {student_plan.limits['max_sessions']}")

            return True

        except Exception as e:
            logger.error(f"❌ Failed to create STUDENT plan configuration: {e}")
            db.rollback()
            return False

def verify_all_plans():
    """Verify all expected plan configurations exist."""

    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return False

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    expected_plans = ['free', 'student', 'pro', 'enterprise', 'coaching_school']

    with SessionLocal() as db:
        try:
            logger.info("📋 Checking all plan configurations...")

            existing_plans = db.query(PlanConfigurationModel).all()
            existing_types = [plan.plan_type for plan in existing_plans]

            for plan_type in expected_plans:
                if plan_type in existing_types:
                    plan = next(p for p in existing_plans if p.plan_type == plan_type)
                    logger.info(f"   ✅ {plan_type.upper()}: {plan.display_name}")
                else:
                    logger.warning(f"   ❌ {plan_type.upper()}: Missing")

            logger.info(f"📊 Total plans found: {len(existing_plans)}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to verify plans: {e}")
            return False

if __name__ == "__main__":
    logger.info("🚀 Starting STUDENT plan configuration check...")

    # Create STUDENT plan if needed
    success = create_student_plan_config()

    if success:
        # Verify all plans
        verify_all_plans()
        logger.info("🎯 STUDENT plan configuration check completed successfully")
    else:
        logger.error("💥 STUDENT plan configuration check failed")
        sys.exit(1)