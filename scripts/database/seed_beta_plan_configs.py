#!/usr/bin/env python3
"""
Seed beta plan configurations with conservative limits for safe launch.
"""

import uuid
import json
from datetime import datetime, UTC
from coaching_assistant.core.config import Settings
from sqlalchemy import create_engine, text

def seed_beta_plan_configs():
    """Seed conservative plan configurations for beta launch."""
    settings = Settings()
    engine = create_engine(settings.DATABASE_URL)
    
    # Conservative beta limits (more restrictive than final)
    plan_configs = [
        {
            'id': str(uuid.uuid4()),
            'plan_type': 'FREE',
            'plan_name': 'free',
            'display_name': 'Free Trial',
            'description': 'Perfect for trying out our coaching transcription service',
            'tagline': 'Start your coaching journey',
            'limits': {
                'maxSessions': 10,       # Updated: 10 sessions per month
                'maxMinutes': 200,       # Updated: 200 min of transcription per month
                'maxTranscriptions': 5,  # Updated: 5 transcriptions per month
                'maxFileSize': 60,       # Updated: up to 40 min per recording (60MB ~= 40min)
                'maxExports': 10,        # Conservative limit
                'retentionDays': 30,
                'concurrentJobs': 1
            },
            'features': [
                'Basic transcription',
                'Speaker diarization', 
                'Text and JSON export',
                '30-day data retention',
                'Email support'
            ],
            'monthly_price_cents': 0,
            'annual_price_cents': 0,
            'currency': 'USD',
            'monthly_price_twd_cents': 0,
            'annual_price_twd_cents': 0,
            'is_popular': False,
            'is_enterprise': False,
            'color_scheme': 'blue',
            'sort_order': 1,
            'is_active': True,
            'is_visible': True,
            'extra_data': {
                'beta_limits': True,
                'cost_control': 'strict'
            }
        },
        {
            'id': str(uuid.uuid4()),
            'plan_type': 'PRO',
            'plan_name': 'pro',
            'display_name': 'Professional',
            'description': 'For professional coaches who need more capacity',
            'tagline': 'Scale your coaching practice',
            'limits': {
                'maxSessions': 25,       # Reduced from 100 for beta safety
                'maxMinutes': 300,       # Reduced from 1200 for beta safety (5 hours vs 20)
                'maxTranscriptions': 50, # Reduced from 200 for beta safety
                'maxFileSize': 100,      # Reduced from 200MB for beta safety
                'maxExports': 100,       # Conservative limit
                'retentionDays': 365,
                'concurrentJobs': 2
            },
            'features': [
                'Everything in Free',
                'Priority processing',
                'Advanced export formats (VTT, SRT)',
                '1-year data retention',
                'Priority support',
                'Bulk operations'
            ],
            'monthly_price_cents': 2900,  # $29/month
            'annual_price_cents': 29000,  # $290/year (2 months free)
            'currency': 'USD', 
            'monthly_price_twd_cents': 89000,   # ~$29 USD in TWD
            'annual_price_twd_cents': 890000,   # ~$290 USD in TWD
            'is_popular': True,
            'is_enterprise': False,
            'color_scheme': 'purple',
            'sort_order': 2,
            'is_active': True,
            'is_visible': True,
            'extra_data': {
                'beta_limits': True,
                'cost_control': 'moderate'
            }
        },
        {
            'id': str(uuid.uuid4()),
            'plan_type': 'ENTERPRISE',
            'plan_name': 'enterprise',
            'display_name': 'Enterprise',
            'description': 'For coaching organizations and teams',
            'tagline': 'Unlimited coaching transcription',
            'limits': {
                'maxSessions': 500,      # Conservative limit for beta (not unlimited)
                'maxMinutes': 1500,      # Conservative limit for beta (25 hours)
                'maxTranscriptions': 1000, # Conservative limit for beta
                'maxFileSize': 500,      # Conservative limit for beta
                'maxExports': 500,       # Conservative limit for beta
                'retentionDays': -1,     # Unlimited retention
                'concurrentJobs': 5
            },
            'features': [
                'Everything in Pro',
                'Unlimited usage*',
                'Custom integrations',
                'Dedicated support',
                'SLA guarantees',
                'Custom retention policies',
                'API access'
            ],
            'monthly_price_cents': 9900,  # $99/month
            'annual_price_cents': 99000,  # $990/year
            'currency': 'USD',
            'monthly_price_twd_cents': 304000,  # ~$99 USD in TWD
            'annual_price_twd_cents': 3040000,  # ~$990 USD in TWD
            'is_popular': False,
            'is_enterprise': True,
            'color_scheme': 'gold',
            'sort_order': 3,
            'is_active': True,
            'is_visible': True,
            'extra_data': {
                'beta_limits': True,
                'cost_control': 'monitored',
                'note': '*Conservative limits during beta testing'
            }
        }
    ]
    
    with engine.connect() as conn:
        # Check if plans already exist
        result = conn.execute(text("SELECT COUNT(*) FROM plan_configurations"))
        count = result.scalar()
        
        if count > 0:
            print(f"⚠️  Plan configurations already exist ({count} records). Skipping seed.")
            return
        
        # Insert plan configurations
        print("🌱 Seeding beta plan configurations...")
        
        for plan in plan_configs:
            conn.execute(text("""
                INSERT INTO plan_configurations (
                    id, plan_type, plan_name, display_name, description, tagline,
                    limits, features, monthly_price_cents, annual_price_cents, currency,
                    monthly_price_twd_cents, annual_price_twd_cents, is_popular, is_enterprise,
                    color_scheme, sort_order, is_active, is_visible, extra_data,
                    created_at, updated_at
                ) VALUES (
                    :id, :plan_type, :plan_name, :display_name, :description, :tagline,
                    :limits, :features, :monthly_price_cents, :annual_price_cents, :currency,
                    :monthly_price_twd_cents, :annual_price_twd_cents, :is_popular, :is_enterprise,
                    :color_scheme, :sort_order, :is_active, :is_visible, :extra_data,
                    :created_at, :updated_at
                )
            """), {
                **plan,
                'limits': json.dumps(plan['limits']),  # Proper JSON serialization
                'features': json.dumps(plan['features']),  # Proper JSON serialization
                'extra_data': json.dumps(plan['extra_data']),  # Proper JSON serialization
                'created_at': datetime.now(UTC),
                'updated_at': datetime.now(UTC)
            })
            
            print(f"✅ Seeded {plan['plan_name']} plan")
        
        conn.commit()
        
        # Verify seeding
        result = conn.execute(text("SELECT plan_name, display_name FROM plan_configurations ORDER BY sort_order"))
        plans = list(result)
        print(f"\n📋 Beta plan configurations created:")
        for plan_name, display_name in plans:
            print(f"  - {plan_name}: {display_name}")
        
        # Show current free plan limits
        result = conn.execute(text("SELECT plan_name, limits FROM plan_configurations WHERE plan_name = 'free'"))
        free_plan = result.fetchone()
        if free_plan:
            print(f"\n📊 Free plan limits:")
            print(f"  - Sessions: 10 per month")
            print(f"  - Transcription minutes: 200 per month")  
            print(f"  - Transcriptions: 5 per month")
            print(f"  - Max file size: 60MB (up to 40 min per recording)")

if __name__ == "__main__":
    seed_beta_plan_configs()