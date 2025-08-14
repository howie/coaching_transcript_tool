# Billing Plan Limitation System - Technical Design

## 📋 Overview

This document outlines the technical architecture and implementation details for the Billing Plan Limitation & Usage Management System.

## 🏗️ System Architecture

### High-Level Architecture
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External      │
│   (Next.js)     │    │   (FastAPI)     │    │   Services      │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Dashboard     │    │ • Plan Services │    │ • Stripe        │
│ • Billing UI    │◄──►│ • Usage Track.  │◄──►│ • Email Service │
│ • Admin Panel   │    │ • Validation    │    │ • Analytics     │
│ • Components    │    │ • Analytics     │    │ • Monitoring    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Database      │
                    │   (PostgreSQL)  │
                    ├─────────────────┤
                    │ • Users         │
                    │ • Sessions      │
                    │ • Usage Logs    │
                    │ • Plans         │
                    │ • Analytics     │
                    └─────────────────┘
```

### Component Architecture
```
Backend Services:
├── BillingPlanService        # Plan management and validation
├── UsageTrackingService      # Usage logging and analytics
├── SmartBillingService       # Retry vs re-transcription logic
├── PlanValidationMiddleware  # Real-time limit checking
├── SubscriptionService       # Plan upgrades/downgrades
├── AnalyticsService          # Usage and billing analytics
└── GDPRComplianceService     # Data retention and privacy

Frontend Components:
├── billing/
│   ├── PlanSelector.tsx      # Plan comparison and selection
│   ├── UsageProgressBar.tsx  # Usage visualization
│   ├── UpgradePrompt.tsx     # Plan upgrade prompts
│   └── BillingHistory.tsx    # Transaction history
├── dashboard/
│   ├── UsageDashboard.tsx    # Main usage dashboard
│   └── PlanLimitBanner.tsx   # Limit warnings
└── admin/
    └── BillingAnalytics.tsx  # Admin analytics
```

## 🗄️ Database Design

### Enhanced User Model
```sql
CREATE TABLE "user" (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    
    -- Existing fields...
    hashed_password VARCHAR(255),
    google_id VARCHAR(255),
    avatar_url VARCHAR(512),
    preferences TEXT,
    
    -- Billing Plan Information
    plan VARCHAR(20) DEFAULT 'free' NOT NULL,
    subscription_start_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    subscription_end_date TIMESTAMP WITH TIME ZONE,
    subscription_active BOOLEAN DEFAULT true NOT NULL,
    
    -- Monthly Usage Tracking (resets monthly)
    usage_minutes INTEGER DEFAULT 0 NOT NULL,
    session_count INTEGER DEFAULT 0 NOT NULL,
    transcription_count INTEGER DEFAULT 0 NOT NULL,
    current_month_start TIMESTAMP WITH TIME ZONE DEFAULT date_trunc('month', NOW()),
    
    -- Cumulative Analytics (never resets)
    total_sessions_created INTEGER DEFAULT 0 NOT NULL,
    total_transcriptions_generated INTEGER DEFAULT 0 NOT NULL,
    total_minutes_processed DECIMAL(10,2) DEFAULT 0 NOT NULL,
    
    -- Billing Metadata
    billing_metadata JSONB DEFAULT '{}' NOT NULL,
    
    -- Standard fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_user_plan ON "user"(plan);
CREATE INDEX idx_user_subscription_active ON "user"(subscription_active);
CREATE INDEX idx_user_current_month ON "user"(current_month_start);
```

### Independent Usage Logging System
```sql
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Core References
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    session_id UUID NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    client_id UUID REFERENCES client(id) ON DELETE SET NULL,
    
    -- Usage Details
    duration_minutes INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    cost_usd DECIMAL(10,6),
    stt_provider VARCHAR(50) NOT NULL,
    
    -- Billing Classification (Smart Billing)
    transcription_type VARCHAR(20) NOT NULL, -- 'original', 'retry_failed', 'retry_success'
    is_billable BOOLEAN DEFAULT true NOT NULL,
    billing_reason VARCHAR(100),
    parent_usage_log_id UUID REFERENCES usage_logs(id),
    
    -- Plan Information (snapshot)
    user_plan VARCHAR(20) NOT NULL,
    plan_limits JSONB,
    
    -- Session Context
    language VARCHAR(20),
    enable_diarization BOOLEAN DEFAULT true,
    
    -- Timestamps
    transcription_started_at TIMESTAMP WITH TIME ZONE,
    transcription_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Provider Metadata
    provider_metadata JSONB DEFAULT '{}'
);

-- Indexes for performance and analytics
CREATE INDEX idx_usage_logs_user_id ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_session_id ON usage_logs(session_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);
CREATE INDEX idx_usage_logs_user_plan ON usage_logs(user_plan);
CREATE INDEX idx_usage_logs_transcription_type ON usage_logs(transcription_type);
CREATE INDEX idx_usage_logs_billable ON usage_logs(is_billable);

-- Monthly analytics view
CREATE INDEX idx_usage_logs_month_user ON usage_logs(date_trunc('month', created_at), user_id);
```

### Plan Configuration System
```sql
CREATE TABLE plan_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Plan Identity
    plan_name VARCHAR(20) UNIQUE NOT NULL,
    display_name VARCHAR(50) NOT NULL,
    description TEXT,
    
    -- Usage Limits (-1 = unlimited)
    max_sessions INTEGER NOT NULL,
    max_total_minutes INTEGER NOT NULL,
    max_transcription_count INTEGER NOT NULL,
    max_file_size_mb INTEGER NOT NULL,
    
    -- Feature Availability
    export_formats JSONB NOT NULL DEFAULT '["json", "txt"]',
    priority_support BOOLEAN DEFAULT false,
    concurrent_processing INTEGER DEFAULT 1,
    
    -- Data Management
    retention_days INTEGER NOT NULL, -- -1 = permanent
    
    -- Pricing (for display)
    monthly_price_usd DECIMAL(10,2),
    annual_price_usd DECIMAL(10,2),
    
    -- Configuration
    is_active BOOLEAN DEFAULT true,
    sort_order INTEGER DEFAULT 0,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Default plan configurations
INSERT INTO plan_configurations (
    plan_name, display_name, description,
    max_sessions, max_total_minutes, max_transcription_count, max_file_size_mb,
    export_formats, priority_support, concurrent_processing, retention_days,
    monthly_price_usd, sort_order
) VALUES 
    ('free', 'Free Trial', 'Perfect for trying out the platform', 
     10, 120, 20, 50,
     '["json", "txt"]', false, 1, 30,
     0.00, 1),
    ('pro', 'Pro Plan', 'For professional coaches', 
     100, 1200, 200, 200,
     '["json", "txt", "vtt", "srt"]', true, 3, 365,
     29.99, 2),
    ('business', 'Business Plan', 'For coaching organizations', 
     -1, -1, -1, 500,
     '["json", "txt", "vtt", "srt", "xlsx"]', true, 10, -1,
     99.99, 3);
```

### Subscription Change Tracking
```sql
CREATE TABLE subscription_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- User Reference
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    
    -- Change Details
    old_plan VARCHAR(20),
    new_plan VARCHAR(20) NOT NULL,
    change_type VARCHAR(20) NOT NULL, -- 'upgrade', 'downgrade', 'renewal', 'cancellation'
    change_reason TEXT,
    
    -- Financial Information
    prorated_amount DECIMAL(10,2),
    payment_method VARCHAR(50),
    transaction_id VARCHAR(100),
    
    -- Timing
    effective_date TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Metadata
    change_metadata JSONB DEFAULT '{}',
    
    -- Admin info (if changed by admin)
    changed_by_user_id UUID REFERENCES "user"(id),
    admin_notes TEXT
);

-- Indexes
CREATE INDEX idx_subscription_history_user_id ON subscription_history(user_id);
CREATE INDEX idx_subscription_history_effective_date ON subscription_history(effective_date);
CREATE INDEX idx_subscription_history_change_type ON subscription_history(change_type);
```

### Monthly Usage Analytics
```sql
CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- User and Time Dimension
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    month_year VARCHAR(7) NOT NULL, -- 'YYYY-MM'
    
    -- Plan Information
    user_plan VARCHAR(20) NOT NULL,
    plan_changed_during_month BOOLEAN DEFAULT false,
    
    -- Usage Metrics
    sessions_created INTEGER DEFAULT 0,
    transcriptions_completed INTEGER DEFAULT 0,
    total_minutes_processed DECIMAL(10,2) DEFAULT 0,
    total_cost_usd DECIMAL(10,4) DEFAULT 0,
    
    -- Billing Classification
    original_transcriptions INTEGER DEFAULT 0,
    free_retries INTEGER DEFAULT 0,
    paid_retranscriptions INTEGER DEFAULT 0,
    
    -- Provider Breakdown
    google_stt_minutes DECIMAL(10,2) DEFAULT 0,
    assemblyai_minutes DECIMAL(10,2) DEFAULT 0,
    
    -- Export Activity
    exports_by_format JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, month_year)
);

-- Indexes for analytics queries
CREATE INDEX idx_usage_analytics_month_year ON usage_analytics(month_year);
CREATE INDEX idx_usage_analytics_user_plan ON usage_analytics(user_plan);
CREATE INDEX idx_usage_analytics_user_month ON usage_analytics(user_id, month_year);
```

## 🔧 Core Services Implementation

### Plan Validation Service
```python
# packages/core-logic/src/coaching_assistant/services/plan_validation.py

from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.user import User, UserPlan, PlanLimits
from ..models.session import Session as SessionModel
from ..exceptions import PlanLimitExceeded

class PlanValidationService:
    """Service for validating user actions against plan limits."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def validate_session_creation(self, user: User) -> bool:
        """Validate if user can create a new session."""
        limits = PlanLimits.get_limits(user.plan)
        
        if PlanLimits.is_unlimited(user.plan, "max_sessions"):
            return True
        
        if user.session_count >= limits["max_sessions"]:
            raise PlanLimitExceeded(
                message=f"Session limit exceeded. Upgrade to continue.",
                limit_type="max_sessions",
                current_usage=user.session_count,
                plan_limit=limits["max_sessions"],
                suggested_plan=self._get_next_plan(user.plan)
            )
        
        return True
    
    def validate_file_size(self, user: User, file_size_bytes: int) -> bool:
        """Validate file size against plan limits."""
        limits = PlanLimits.get_limits(user.plan)
        max_size_bytes = limits["max_file_size_mb"] * 1024 * 1024
        
        if file_size_bytes > max_size_bytes:
            raise PlanLimitExceeded(
                message=f"File size exceeds {limits['max_file_size_mb']}MB limit",
                limit_type="max_file_size_mb",
                current_usage=file_size_bytes // (1024 * 1024),
                plan_limit=limits["max_file_size_mb"],
                suggested_plan=self._get_next_plan(user.plan)
            )
        
        return True
    
    def validate_export_format(self, user: User, format: str) -> bool:
        """Validate export format availability for plan."""
        limits = PlanLimits.get_limits(user.plan)
        
        if format.lower() not in limits["export_formats"]:
            available_formats = ", ".join(limits["export_formats"])
            raise PlanLimitExceeded(
                message=f"Format '{format}' not available. Available: {available_formats}",
                limit_type="export_formats",
                current_usage=format,
                plan_limit=limits["export_formats"],
                suggested_plan=self._get_next_plan(user.plan)
            )
        
        return True
    
    def validate_transcription_count(self, user: User) -> bool:
        """Validate transcription count against plan limits."""
        limits = PlanLimits.get_limits(user.plan)
        
        if PlanLimits.is_unlimited(user.plan, "max_transcription_count"):
            return True
        
        if user.transcription_count >= limits["max_transcription_count"]:
            raise PlanLimitExceeded(
                message="Transcription limit exceeded for this month",
                limit_type="max_transcription_count",
                current_usage=user.transcription_count,
                plan_limit=limits["max_transcription_count"],
                suggested_plan=self._get_next_plan(user.plan)
            )
        
        return True
    
    def _get_next_plan(self, current_plan: UserPlan) -> Optional[UserPlan]:
        """Get suggested upgrade plan."""
        upgrade_path = {
            UserPlan.FREE: UserPlan.PRO,
            UserPlan.PRO: UserPlan.BUSINESS,
            UserPlan.BUSINESS: None
        }
        return upgrade_path.get(current_plan)
    
    def get_usage_summary(self, user: User) -> Dict[str, Any]:
        """Get comprehensive usage summary for user."""
        limits = PlanLimits.get_limits(user.plan)
        
        return {
            "user_id": str(user.id),
            "plan": user.plan.value,
            "current_usage": {
                "sessions": user.session_count,
                "minutes": user.usage_minutes,
                "transcriptions": user.transcription_count
            },
            "plan_limits": {
                "max_sessions": limits["max_sessions"] if limits["max_sessions"] != -1 else "unlimited",
                "max_minutes": limits["max_total_minutes"] if limits["max_total_minutes"] != -1 else "unlimited",
                "max_transcriptions": limits["max_transcription_count"] if limits["max_transcription_count"] != -1 else "unlimited",
                "max_file_size_mb": limits["max_file_size_mb"],
                "export_formats": limits["export_formats"],
                "concurrent_processing": limits["concurrent_processing"]
            },
            "usage_percentages": {
                "sessions": self._calculate_usage_percentage(user.session_count, limits["max_sessions"]),
                "minutes": self._calculate_usage_percentage(user.usage_minutes, limits["max_total_minutes"]),
                "transcriptions": self._calculate_usage_percentage(user.transcription_count, limits["max_transcription_count"])
            },
            "approaching_limits": self._check_approaching_limits(user, limits),
            "subscription_info": {
                "start_date": user.subscription_start_date.isoformat() if user.subscription_start_date else None,
                "end_date": user.subscription_end_date.isoformat() if user.subscription_end_date else None,
                "active": user.subscription_active,
                "days_until_reset": self._days_until_month_reset(user.current_month_start)
            }
        }
    
    def _calculate_usage_percentage(self, current: int, limit: int) -> Optional[float]:
        """Calculate usage percentage, handling unlimited plans."""
        if limit == -1:  # Unlimited
            return None
        return (current / limit * 100) if limit > 0 else 0
    
    def _check_approaching_limits(self, user: User, limits: Dict) -> Dict[str, bool]:
        """Check if user is approaching any limits (>80% usage)."""
        return {
            "sessions": self._is_approaching_limit(user.session_count, limits["max_sessions"]),
            "minutes": self._is_approaching_limit(user.usage_minutes, limits["max_total_minutes"]),
            "transcriptions": self._is_approaching_limit(user.transcription_count, limits["max_transcription_count"])
        }
    
    def _is_approaching_limit(self, current: int, limit: int) -> bool:
        """Check if usage is approaching limit (>80%)."""
        if limit == -1:  # Unlimited
            return False
        return (current / limit) > 0.8 if limit > 0 else False
    
    def _days_until_month_reset(self, current_month_start: datetime) -> int:
        """Calculate days until monthly usage reset."""
        next_month = current_month_start.replace(month=current_month_start.month + 1)
        return (next_month - datetime.now(current_month_start.tzinfo)).days
```

### Usage Tracking Service
```python
# packages/core-logic/src/coaching_assistant/services/usage_tracking.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, extract
from ..models.user import User
from ..models.session import Session as SessionModel
from ..models.usage_log import UsageLog, TranscriptionType
from ..models.usage_analytics import UsageAnalytics

class UsageTrackingService:
    """Service for tracking and managing user usage."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_usage_log(
        self,
        session: SessionModel,
        transcription_type: TranscriptionType,
        duration_seconds: int,
        cost_usd: Optional[float] = None,
        is_billable: bool = True,
        billing_reason: str = "transcription_completed"
    ) -> UsageLog:
        """Create usage log entry for transcription."""
        
        # Get user for plan information
        user = self.db.query(User).filter(User.id == session.user_id).first()
        
        # Find parent log if this is a retry/re-transcription
        parent_log = None
        if transcription_type != TranscriptionType.ORIGINAL:
            parent_log = self.db.query(UsageLog).filter(
                UsageLog.session_id == session.id
            ).order_by(UsageLog.created_at.asc()).first()
        
        # Create usage log
        usage_log = UsageLog(
            user_id=session.user_id,
            session_id=session.id,
            client_id=getattr(session, 'client_id', None),
            
            duration_minutes=int(duration_seconds / 60),
            duration_seconds=duration_seconds,
            cost_usd=cost_usd if is_billable else 0.0,
            stt_provider=session.stt_provider,
            
            transcription_type=transcription_type,
            is_billable=is_billable,
            billing_reason=billing_reason,
            parent_usage_log_id=parent_log.id if parent_log else None,
            
            user_plan=user.plan.value,
            plan_limits=PlanLimits.get_limits(user.plan),
            
            language=session.language,
            
            transcription_started_at=datetime.utcnow(),
            transcription_completed_at=datetime.utcnow(),
            
            provider_metadata=session.provider_metadata or {}
        )
        
        self.db.add(usage_log)
        self.db.flush()
        
        # Update user usage counters (only for billable transcriptions)
        if is_billable:
            self._update_user_usage(user, int(duration_seconds / 60))
        
        # Update monthly analytics
        self._update_monthly_analytics(user.id, usage_log)
        
        self.db.commit()
        
        return usage_log
    
    def _update_user_usage(self, user: User, minutes: int):
        """Update user's current month usage counters."""
        
        # Check if we need to reset monthly usage
        self._check_and_reset_monthly_usage(user)
        
        # Update usage counters
        user.usage_minutes += minutes
        user.transcription_count += 1
        
        # Update cumulative counters
        user.total_transcriptions_generated += 1
        user.total_minutes_processed += minutes
        
        self.db.flush()
    
    def increment_session_count(self, user: User):
        """Increment user's session count."""
        self._check_and_reset_monthly_usage(user)
        
        user.session_count += 1
        user.total_sessions_created += 1
        
        self.db.flush()
    
    def _check_and_reset_monthly_usage(self, user: User):
        """Check if monthly usage should be reset."""
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if user.current_month_start < current_month:
            user.usage_minutes = 0
            user.session_count = 0
            user.transcription_count = 0
            user.current_month_start = current_month
            
            self.db.flush()
    
    def _update_monthly_analytics(self, user_id: str, usage_log: UsageLog):
        """Update or create monthly analytics record."""
        month_year = usage_log.created_at.strftime('%Y-%m')
        
        analytics = self.db.query(UsageAnalytics).filter(
            and_(
                UsageAnalytics.user_id == user_id,
                UsageAnalytics.month_year == month_year
            )
        ).first()
        
        if not analytics:
            analytics = UsageAnalytics(
                user_id=user_id,
                month_year=month_year,
                user_plan=usage_log.user_plan
            )
            self.db.add(analytics)
        
        # Update metrics
        if usage_log.transcription_type == TranscriptionType.ORIGINAL:
            analytics.original_transcriptions += 1
        elif usage_log.transcription_type == TranscriptionType.RETRY_FAILED:
            analytics.free_retries += 1
        elif usage_log.transcription_type == TranscriptionType.RETRY_SUCCESS:
            analytics.paid_retranscriptions += 1
        
        analytics.transcriptions_completed += 1
        analytics.total_minutes_processed += usage_log.duration_minutes
        analytics.total_cost_usd += (usage_log.cost_usd or 0)
        
        # Update provider breakdown
        if usage_log.stt_provider == 'google':
            analytics.google_stt_minutes += usage_log.duration_minutes
        elif usage_log.stt_provider == 'assemblyai':
            analytics.assemblyai_minutes += usage_log.duration_minutes
        
        self.db.flush()
    
    def get_user_usage_history(
        self,
        user_id: str,
        months: int = 12
    ) -> List[Dict[str, Any]]:
        """Get user's usage history for specified months."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
        
        usage_logs = self.db.query(UsageLog).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= cutoff_date
            )
        ).order_by(UsageLog.created_at.desc()).all()
        
        return [
            {
                "id": str(log.id),
                "session_id": str(log.session_id),
                "transcription_type": log.transcription_type.value,
                "duration_minutes": log.duration_minutes,
                "cost_usd": float(log.cost_usd) if log.cost_usd else 0.0,
                "is_billable": log.is_billable,
                "billing_reason": log.billing_reason,
                "stt_provider": log.stt_provider,
                "user_plan": log.user_plan,
                "created_at": log.created_at.isoformat(),
                "billing_description": log.billing_description
            }
            for log in usage_logs
        ]
    
    def get_analytics_summary(
        self,
        user_id: Optional[str] = None,
        months: int = 12
    ) -> Dict[str, Any]:
        """Get analytics summary for user or system-wide."""
        
        cutoff_date = datetime.utcnow() - timedelta(days=months * 30)
        
        query = self.db.query(UsageAnalytics).filter(
            UsageAnalytics.created_at >= cutoff_date
        )
        
        if user_id:
            query = query.filter(UsageAnalytics.user_id == user_id)
        
        analytics = query.all()
        
        if not analytics:
            return self._empty_analytics_summary()
        
        # Aggregate metrics
        total_sessions = sum(a.sessions_created for a in analytics)
        total_transcriptions = sum(a.transcriptions_completed for a in analytics)
        total_minutes = sum(a.total_minutes_processed for a in analytics)
        total_cost = sum(a.total_cost_usd for a in analytics)
        
        # Plan distribution
        plan_distribution = {}
        for analytic in analytics:
            plan = analytic.user_plan
            plan_distribution[plan] = plan_distribution.get(plan, 0) + 1
        
        # Provider breakdown
        google_minutes = sum(a.google_stt_minutes for a in analytics)
        assemblyai_minutes = sum(a.assemblyai_minutes for a in analytics)
        
        return {
            "summary": {
                "total_sessions": total_sessions,
                "total_transcriptions": total_transcriptions,
                "total_minutes_processed": float(total_minutes),
                "total_cost_usd": float(total_cost),
                "average_session_duration": float(total_minutes / total_sessions) if total_sessions > 0 else 0
            },
            "plan_distribution": plan_distribution,
            "provider_breakdown": {
                "google_stt_minutes": float(google_minutes),
                "assemblyai_minutes": float(assemblyai_minutes),
                "google_percentage": float(google_minutes / total_minutes * 100) if total_minutes > 0 else 0,
                "assemblyai_percentage": float(assemblyai_minutes / total_minutes * 100) if total_minutes > 0 else 0
            },
            "billing_classification": {
                "original_transcriptions": sum(a.original_transcriptions for a in analytics),
                "free_retries": sum(a.free_retries for a in analytics),
                "paid_retranscriptions": sum(a.paid_retranscriptions for a in analytics)
            },
            "time_range": {
                "months": months,
                "start_date": cutoff_date.isoformat(),
                "end_date": datetime.utcnow().isoformat()
            }
        }
    
    def _empty_analytics_summary(self) -> Dict[str, Any]:
        """Return empty analytics summary structure."""
        return {
            "summary": {
                "total_sessions": 0,
                "total_transcriptions": 0,
                "total_minutes_processed": 0.0,
                "total_cost_usd": 0.0,
                "average_session_duration": 0.0
            },
            "plan_distribution": {},
            "provider_breakdown": {
                "google_stt_minutes": 0.0,
                "assemblyai_minutes": 0.0,
                "google_percentage": 0.0,
                "assemblyai_percentage": 0.0
            },
            "billing_classification": {
                "original_transcriptions": 0,
                "free_retries": 0,
                "paid_retranscriptions": 0
            }
        }
```

## 🔌 API Implementation

### Billing Management API
```python
# packages/core-logic/src/coaching_assistant/api/billing.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from ..dependencies import get_db, get_current_user_dependency
from ..models.user import User, UserPlan
from ..services.plan_validation import PlanValidationService
from ..services.subscription_service import SubscriptionService
from ..services.usage_tracking import UsageTrackingService

router = APIRouter(prefix="/billing", tags=["billing"])

@router.get("/plans")
async def get_available_plans(
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get available billing plans and their features."""
    
    from ..models.plan_configuration import PlanConfiguration
    
    plans = db.query(PlanConfiguration).filter(
        PlanConfiguration.is_active == True
    ).order_by(PlanConfiguration.sort_order).all()
    
    return {
        "plans": [
            {
                "name": plan.plan_name,
                "display_name": plan.display_name,
                "description": plan.description,
                "features": {
                    "max_sessions": plan.max_sessions if plan.max_sessions != -1 else "unlimited",
                    "max_total_minutes": plan.max_total_minutes if plan.max_total_minutes != -1 else "unlimited",
                    "max_transcription_count": plan.max_transcription_count if plan.max_transcription_count != -1 else "unlimited",
                    "max_file_size_mb": plan.max_file_size_mb,
                    "export_formats": plan.export_formats,
                    "priority_support": plan.priority_support,
                    "concurrent_processing": plan.concurrent_processing,
                    "retention_days": plan.retention_days if plan.retention_days != -1 else "permanent"
                },
                "pricing": {
                    "monthly_usd": float(plan.monthly_price_usd) if plan.monthly_price_usd else 0.0,
                    "annual_usd": float(plan.annual_price_usd) if plan.annual_price_usd else 0.0
                }
            }
            for plan in plans
        ]
    }

@router.get("/usage")
async def get_current_usage(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current user's usage statistics and limits."""
    
    validation_service = PlanValidationService(db)
    return validation_service.get_usage_summary(current_user)

@router.get("/usage/history")
async def get_usage_history(
    months: int = 3,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's usage history."""
    
    tracking_service = UsageTrackingService(db)
    history = tracking_service.get_user_usage_history(
        user_id=str(current_user.id),
        months=months
    )
    
    return {
        "user_id": str(current_user.id),
        "months_requested": months,
        "usage_history": history
    }

@router.post("/upgrade")
async def upgrade_plan(
    upgrade_request: Dict[str, str],  # {"plan": "pro", "payment_method": "pm_xxx"}
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Upgrade user's plan."""
    
    new_plan = upgrade_request.get("plan")
    payment_method = upgrade_request.get("payment_method")
    
    if not new_plan or new_plan not in ["pro", "business"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid plan. Choose 'pro' or 'business'"
        )
    
    subscription_service = SubscriptionService(db)
    
    try:
        result = await subscription_service.upgrade_user_plan(
            user=current_user,
            new_plan=UserPlan(new_plan),
            payment_method=payment_method
        )
        
        return {
            "message": f"Successfully upgraded to {new_plan.title()} plan",
            "user_id": str(current_user.id),
            "new_plan": new_plan,
            "transaction": {
                "id": result["transaction_id"],
                "amount": result["amount"],
                "prorated_amount": result.get("prorated_amount"),
                "effective_date": result["effective_date"]
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Plan upgrade failed: {str(e)}"
        )

@router.post("/downgrade")
async def downgrade_plan(
    downgrade_request: Dict[str, str],  # {"plan": "free"}
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Downgrade user's plan."""
    
    new_plan = downgrade_request.get("plan")
    
    if not new_plan:
        raise HTTPException(
            status_code=400,
            detail="Plan is required"
        )
    
    subscription_service = SubscriptionService(db)
    
    try:
        result = await subscription_service.downgrade_user_plan(
            user=current_user,
            new_plan=UserPlan(new_plan)
        )
        
        return {
            "message": f"Plan will be changed to {new_plan.title()} at end of billing cycle",
            "user_id": str(current_user.id),
            "new_plan": new_plan,
            "effective_date": result["effective_date"],
            "current_plan_expires": result["current_plan_expires"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Plan downgrade failed: {str(e)}"
        )

@router.get("/limits/check")
async def check_limits(
    action: str,  # 'create_session', 'transcribe', 'export'
    format: Optional[str] = None,  # For export format validation
    file_size: Optional[int] = None,  # For file size validation (bytes)
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Check if user can perform specific action against plan limits."""
    
    validation_service = PlanValidationService(db)
    
    try:
        if action == "create_session":
            validation_service.validate_session_creation(current_user)
            
        elif action == "transcribe":
            validation_service.validate_transcription_count(current_user)
            
        elif action == "export" and format:
            validation_service.validate_export_format(current_user, format)
            
        elif action == "upload" and file_size:
            validation_service.validate_file_size(current_user, file_size)
            
        else:
            raise HTTPException(status_code=400, detail="Invalid action or missing parameters")
        
        return {
            "allowed": True,
            "message": "Action is allowed"
        }
        
    except PlanLimitExceeded as e:
        return {
            "allowed": False,
            "message": str(e),
            "limit_exceeded": {
                "type": e.limit_type,
                "current_usage": e.current_usage,
                "plan_limit": e.plan_limit,
                "suggested_plan": e.suggested_plan.value if e.suggested_plan else None
            }
        }

@router.get("/analytics")
async def get_billing_analytics(
    months: int = 12,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's billing and usage analytics."""
    
    tracking_service = UsageTrackingService(db)
    analytics = tracking_service.get_analytics_summary(
        user_id=str(current_user.id),
        months=months
    )
    
    return {
        "user_id": str(current_user.id),
        "plan": current_user.plan.value,
        "analytics_period_months": months,
        **analytics
    }
```

This technical design provides a comprehensive foundation for implementing the billing plan limitation system with proper architecture, database design, and service implementations.

---

**Document Owner**: Technical Architecture Team  
**Last Updated**: August 14, 2025  
**Review Schedule**: Weekly architecture reviews  
**Implementation Status**: Ready for development