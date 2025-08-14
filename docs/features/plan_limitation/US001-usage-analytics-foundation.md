# US001: Usage Analytics Foundation

## 📋 User Story

**As a** business stakeholder and platform user  
**I want** independent usage analytics and tracking system  
**So that** usage records are preserved regardless of client/coach deletions and billing is always accurate

## 💼 Business Value

### Current Problem
- Usage records are lost when clients or coaches are deleted from the system
- User.usage_minutes field can become inconsistent with actual transcription activity
- No historical usage data for business analytics or compliance auditing
- Billing inaccuracies due to data loss during client management operations
- Cannot track detailed usage patterns for plan optimization

### Business Impact  
- **Revenue Risk**: Lost usage data = potential billing discrepancies (~$X,XXX/month potential loss)
- **Compliance Risk**: GDPR requires audit trails, current system has gaps  
- **Analytics Gap**: Cannot track user behavior patterns or platform usage trends
- **Support Issues**: No data trail for customer support resolution
- **Plan Optimization**: Cannot analyze usage patterns to optimize plan limits

### Value Delivered
- **100% Usage Tracking**: Never lose usage records again
- **Business Intelligence**: Historical usage data for growth analytics and plan optimization
- **Compliance Ready**: Complete audit trails for regulatory requirements
- **Billing Accuracy**: Reliable usage data for precise billing calculations
- **Customer Support**: Complete usage history for dispute resolution

## 🎯 Acceptance Criteria

### Core Requirements
1. **Independent Usage Logging**
   - [ ] Every transcription creates a permanent usage log entry
   - [ ] Usage logs survive client/coach deletions (foreign key RESTRICT)
   - [ ] Usage logs include: session_id, user_id, duration, cost, timestamp, transcription_type
   - [ ] Soft deletion support maintains referential integrity

2. **Usage Analytics Aggregation**
   - [ ] Daily batch job aggregates usage data into monthly summaries  
   - [ ] Analytics include: total minutes, session count, cost breakdown, user activity
   - [ ] Aggregations handle client anonymization properly
   - [ ] Performance optimized for reporting queries

3. **Integration with Transcription Workflow**
   - [ ] Usage logging happens automatically after successful transcription
   - [ ] Failed transcriptions don't create billable usage records
   - [ ] User.usage_minutes field stays synchronized with actual usage
   - [ ] Monthly usage reset functionality maintains accuracy

4. **API Endpoints**
   - [ ] GET /api/usage/summary - User's current usage summary
   - [ ] GET /api/usage/history - User's historical usage data (3-12 months)
   - [ ] GET /api/admin/usage/analytics - Admin analytics (requires admin role)
   - [ ] GET /api/usage/analytics - User's personal analytics

### Data Requirements
5. **Database Schema**
   - [ ] New `usage_logs` table with proper indexing for performance
   - [ ] New `usage_analytics` table for pre-aggregated monthly data
   - [ ] Foreign key relationships preserve data integrity
   - [ ] Migration handles existing usage data with backfill
   - [ ] Partitioning strategy for high-volume usage logs

6. **Data Integrity**
   - [ ] Usage logs are immutable after creation
   - [ ] Referential integrity maintained even after client deletion
   - [ ] Database constraints prevent duplicate usage entries
   - [ ] Checksums and validation for data accuracy

## 🏗️ Technical Implementation

### Database Schema
```sql
-- Usage log for individual transcription events
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE RESTRICT,
    session_id UUID NOT NULL REFERENCES session(id) ON DELETE CASCADE,
    client_id UUID REFERENCES client(id) ON DELETE SET NULL,
    
    -- Usage details
    duration_minutes INTEGER NOT NULL,
    duration_seconds INTEGER NOT NULL,
    cost_usd DECIMAL(10,6),
    stt_provider VARCHAR(50) NOT NULL,
    
    -- Billing classification (US004 integration)
    transcription_type VARCHAR(20) NOT NULL DEFAULT 'original',
    is_billable BOOLEAN DEFAULT true NOT NULL,
    billing_reason VARCHAR(100),
    parent_usage_log_id UUID REFERENCES usage_logs(id),
    
    -- Plan context (snapshot for historical accuracy)
    user_plan VARCHAR(20) NOT NULL,
    plan_limits JSONB DEFAULT '{}',
    
    -- Timestamps
    transcription_started_at TIMESTAMP WITH TIME ZONE,
    transcription_completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Session context
    language VARCHAR(20),
    enable_diarization BOOLEAN,
    original_filename VARCHAR(255),
    audio_file_size_mb DECIMAL(8,2),
    
    -- Provider metadata
    provider_metadata JSONB DEFAULT '{}'
);

-- Monthly aggregated analytics for performance
CREATE TABLE usage_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id) ON DELETE CASCADE,
    month_year VARCHAR(7) NOT NULL, -- 'YYYY-MM'
    
    -- Plan information
    primary_plan VARCHAR(20) NOT NULL,
    plan_changed_during_month BOOLEAN DEFAULT false,
    
    -- Aggregated metrics
    sessions_created INTEGER DEFAULT 0,
    transcriptions_completed INTEGER DEFAULT 0,
    total_minutes_processed DECIMAL(10,2) DEFAULT 0,
    total_cost_usd DECIMAL(12,4) DEFAULT 0,
    
    -- Billing breakdown
    original_transcriptions INTEGER DEFAULT 0,
    free_retries INTEGER DEFAULT 0,
    paid_retranscriptions INTEGER DEFAULT 0,
    
    -- Provider breakdown
    google_stt_minutes DECIMAL(10,2) DEFAULT 0,
    assemblyai_minutes DECIMAL(10,2) DEFAULT 0,
    
    -- Export activity
    exports_by_format JSONB DEFAULT '{}',
    total_exports INTEGER DEFAULT 0,
    
    -- Time period
    period_start TIMESTAMP WITH TIME ZONE,
    period_end TIMESTAMP WITH TIME ZONE,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, month_year)
);

-- Performance indexes
CREATE INDEX idx_usage_logs_user_created ON usage_logs(user_id, created_at);
CREATE INDEX idx_usage_logs_session ON usage_logs(session_id);
CREATE INDEX idx_usage_logs_monthly ON usage_logs(date_trunc('month', created_at), user_id);
CREATE INDEX idx_usage_analytics_month ON usage_analytics(month_year);
CREATE INDEX idx_usage_analytics_user ON usage_analytics(user_id, month_year);
```

### Usage Tracking Service
```python
# packages/core-logic/src/coaching_assistant/services/usage_tracking.py

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from ..models.user import User
from ..models.session import Session as SessionModel
from ..models.usage_log import UsageLog, TranscriptionType
from ..models.usage_analytics import UsageAnalytics

class UsageTrackingService:
    """Comprehensive usage tracking and analytics service."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_usage_log(
        self,
        session: SessionModel,
        transcription_type: TranscriptionType = TranscriptionType.ORIGINAL,
        cost_usd: Optional[float] = None,
        is_billable: bool = True,
        billing_reason: str = "transcription_completed"
    ) -> UsageLog:
        """Create comprehensive usage log entry."""
        
        user = self.db.query(User).filter(User.id == session.user_id).first()
        
        # Find parent log for retries/re-transcriptions
        parent_log = None
        if transcription_type != TranscriptionType.ORIGINAL:
            parent_log = self.db.query(UsageLog).filter(
                UsageLog.session_id == session.id
            ).order_by(UsageLog.created_at.asc()).first()
        
        # Create usage log with comprehensive data
        usage_log = UsageLog(
            user_id=session.user_id,
            session_id=session.id,
            client_id=getattr(session, 'client_id', None),
            
            duration_minutes=int(session.duration_seconds / 60) if session.duration_seconds else 0,
            duration_seconds=session.duration_seconds or 0,
            cost_usd=cost_usd if is_billable else 0.0,
            stt_provider=session.stt_provider,
            
            transcription_type=transcription_type,
            is_billable=is_billable,
            billing_reason=billing_reason,
            parent_usage_log_id=parent_log.id if parent_log else None,
            
            user_plan=user.plan.value,
            plan_limits=PlanLimits.get_limits(user.plan),
            
            language=session.language,
            enable_diarization=True,  # Default from session config
            original_filename=session.audio_filename,
            
            transcription_started_at=session.updated_at,
            transcription_completed_at=datetime.utcnow(),
            
            provider_metadata=session.provider_metadata or {}
        )
        
        self.db.add(usage_log)
        self.db.flush()
        
        # Update user usage counters (only for billable)
        if is_billable:
            self._update_user_usage_counters(user, usage_log)
        
        # Update monthly analytics
        self._update_monthly_analytics(user.id, usage_log)
        
        self.db.commit()
        
        return usage_log
    
    def _update_user_usage_counters(self, user: User, usage_log: UsageLog):
        """Update user's monthly usage counters with monthly reset logic."""
        
        # Check if we need to reset monthly usage
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if user.current_month_start < current_month:
            user.usage_minutes = 0
            user.session_count = 0
            user.transcription_count = 0
            user.current_month_start = current_month
        
        # Update current month counters
        user.usage_minutes += usage_log.duration_minutes
        user.transcription_count += 1
        
        # Update cumulative counters
        user.total_transcriptions_generated += 1
        user.total_minutes_processed += usage_log.duration_minutes
        user.total_cost_usd += (usage_log.cost_usd or 0)
        
        self.db.flush()
    
    def increment_session_count(self, user: User):
        """Increment session count with monthly reset check."""
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if user.current_month_start < current_month:
            user.session_count = 0
            user.current_month_start = current_month
        
        user.session_count += 1
        user.total_sessions_created += 1
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
            # Create new monthly analytics record
            analytics = UsageAnalytics(
                user_id=user_id,
                month_year=month_year,
                primary_plan=usage_log.user_plan,
                period_start=usage_log.created_at.replace(day=1, hour=0, minute=0, second=0),
                period_end=self._get_month_end(usage_log.created_at)
            )
            self.db.add(analytics)
        
        # Update metrics based on transcription type
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
        
        analytics.updated_at = datetime.utcnow()
        self.db.flush()
    
    def get_user_usage_summary(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive usage summary for user."""
        
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError("User not found")
        
        # Get recent usage logs
        recent_logs = self.db.query(UsageLog).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= datetime.utcnow() - timedelta(days=30)
            )
        ).order_by(UsageLog.created_at.desc()).limit(10).all()
        
        # Get monthly analytics
        monthly_analytics = self.db.query(UsageAnalytics).filter(
            and_(
                UsageAnalytics.user_id == user_id,
                UsageAnalytics.period_start >= datetime.utcnow() - timedelta(days=365)
            )
        ).order_by(UsageAnalytics.period_start.desc()).all()
        
        return {
            "user_id": str(user.id),
            "plan": user.plan.value,
            "current_month": {
                "usage_minutes": user.usage_minutes,
                "session_count": user.session_count,
                "transcription_count": user.transcription_count,
                "month_start": user.current_month_start.isoformat() if user.current_month_start else None
            },
            "lifetime_totals": {
                "sessions_created": user.total_sessions_created,
                "transcriptions_generated": user.total_transcriptions_generated,
                "minutes_processed": float(user.total_minutes_processed),
                "cost_usd": float(user.total_cost_usd)
            },
            "recent_activity": [
                {
                    "id": str(log.id),
                    "session_id": str(log.session_id),
                    "transcription_type": log.transcription_type.value,
                    "duration_minutes": log.duration_minutes,
                    "cost_usd": float(log.cost_usd) if log.cost_usd else 0.0,
                    "is_billable": log.is_billable,
                    "stt_provider": log.stt_provider,
                    "created_at": log.created_at.isoformat()
                }
                for log in recent_logs
            ],
            "monthly_trends": [
                {
                    "month_year": analytics.month_year,
                    "transcriptions": analytics.transcriptions_completed,
                    "minutes": float(analytics.total_minutes_processed),
                    "cost": float(analytics.total_cost_usd),
                    "plan": analytics.primary_plan
                }
                for analytics in monthly_analytics
            ]
        }
    
    def get_admin_analytics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        plan_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get system-wide analytics for admins."""
        
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=90)  # Default 3 months
        if not end_date:
            end_date = datetime.utcnow()
        
        # Build query
        query = self.db.query(UsageLog).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        )
        
        if plan_filter:
            query = query.filter(UsageLog.user_plan == plan_filter)
        
        usage_logs = query.all()
        
        # Calculate aggregate metrics
        total_transcriptions = len(usage_logs)
        total_minutes = sum(log.duration_minutes for log in usage_logs)
        total_cost = sum(float(log.cost_usd) for log in usage_logs if log.cost_usd)
        billable_transcriptions = len([log for log in usage_logs if log.is_billable])
        
        # Plan distribution
        plan_stats = {}
        for log in usage_logs:
            plan = log.user_plan
            if plan not in plan_stats:
                plan_stats[plan] = {"count": 0, "minutes": 0, "cost": 0.0}
            plan_stats[plan]["count"] += 1
            plan_stats[plan]["minutes"] += log.duration_minutes
            plan_stats[plan]["cost"] += float(log.cost_usd) if log.cost_usd else 0.0
        
        # Provider breakdown
        provider_stats = {}
        for log in usage_logs:
            provider = log.stt_provider
            if provider not in provider_stats:
                provider_stats[provider] = {"count": 0, "minutes": 0, "cost": 0.0}
            provider_stats[provider]["count"] += 1
            provider_stats[provider]["minutes"] += log.duration_minutes
            provider_stats[provider]["cost"] += float(log.cost_usd) if log.cost_usd else 0.0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_transcriptions": total_transcriptions,
                "total_minutes": total_minutes,
                "total_cost_usd": total_cost,
                "billable_transcriptions": billable_transcriptions,
                "avg_duration_minutes": total_minutes / total_transcriptions if total_transcriptions > 0 else 0,
                "avg_cost_per_transcription": total_cost / billable_transcriptions if billable_transcriptions > 0 else 0
            },
            "plan_distribution": plan_stats,
            "provider_breakdown": provider_stats,
            "unique_users": len(set(log.user_id for log in usage_logs)),
            "unique_sessions": len(set(log.session_id for log in usage_logs))
        }
    
    def _get_month_end(self, date: datetime) -> datetime:
        """Get end of month for given date."""
        if date.month == 12:
            return date.replace(year=date.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            return date.replace(month=date.month + 1, day=1) - timedelta(days=1)
```

### API Implementation
```python
# packages/core-logic/src/coaching_assistant/api/usage.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta
from ..dependencies import get_db, get_current_user_dependency, require_admin
from ..models.user import User
from ..services.usage_tracking import UsageTrackingService

router = APIRouter(prefix="/usage", tags=["usage"])

@router.get("/summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's comprehensive usage summary."""
    
    tracking_service = UsageTrackingService(db)
    return tracking_service.get_user_usage_summary(str(current_user.id))

@router.get("/history")
async def get_usage_history(
    months: int = Query(3, ge=1, le=12, description="Number of months of history"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's detailed usage history."""
    
    start_date = datetime.utcnow() - timedelta(days=months * 30)
    
    usage_logs = db.query(UsageLog).filter(
        and_(
            UsageLog.user_id == current_user.id,
            UsageLog.created_at >= start_date
        )
    ).order_by(UsageLog.created_at.desc()).all()
    
    return {
        "user_id": str(current_user.id),
        "months_requested": months,
        "start_date": start_date.isoformat(),
        "usage_history": [
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
                "language": log.language,
                "created_at": log.created_at.isoformat()
            }
            for log in usage_logs
        ]
    }

@router.get("/analytics")
async def get_user_analytics(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get user's usage analytics and trends."""
    
    # Get monthly analytics for past 12 months
    start_date = datetime.utcnow() - timedelta(days=365)
    
    monthly_analytics = db.query(UsageAnalytics).filter(
        and_(
            UsageAnalytics.user_id == current_user.id,
            UsageAnalytics.period_start >= start_date
        )
    ).order_by(UsageAnalytics.period_start.desc()).all()
    
    return {
        "user_id": str(current_user.id),
        "plan": current_user.plan.value,
        "analytics_period": "12_months",
        "monthly_data": [
            {
                "month_year": analytics.month_year,
                "plan": analytics.primary_plan,
                "sessions_created": analytics.sessions_created,
                "transcriptions_completed": analytics.transcriptions_completed,
                "minutes_processed": float(analytics.total_minutes_processed),
                "cost_usd": float(analytics.total_cost_usd),
                "billing_breakdown": {
                    "original": analytics.original_transcriptions,
                    "free_retries": analytics.free_retries,
                    "paid_retranscriptions": analytics.paid_retranscriptions
                },
                "provider_breakdown": {
                    "google_minutes": float(analytics.google_stt_minutes),
                    "assemblyai_minutes": float(analytics.assemblyai_minutes)
                }
            }
            for analytics in monthly_analytics
        ]
    }

# Admin-only endpoints
@router.get("/admin/analytics")
async def get_admin_usage_analytics(
    start_date: Optional[datetime] = Query(None, description="Start date for analytics"),
    end_date: Optional[datetime] = Query(None, description="End date for analytics"),
    plan_filter: Optional[str] = Query(None, description="Filter by plan"),
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get system-wide usage analytics (Admin only)."""
    
    tracking_service = UsageTrackingService(db)
    return tracking_service.get_admin_analytics(
        start_date=start_date,
        end_date=end_date,
        plan_filter=plan_filter
    )
```

## 🧪 Test Scenarios

### Unit Tests
```python
def test_usage_log_creation():
    """Test usage log entry creation preserves all data"""
    user = create_test_user(plan=UserPlan.FREE)
    session = create_test_session(user_id=user.id, duration_seconds=300)
    
    tracking_service = UsageTrackingService(db)
    usage_log = tracking_service.create_usage_log(
        session=session,
        transcription_type=TranscriptionType.ORIGINAL,
        cost_usd=0.05
    )
    
    assert usage_log.user_id == user.id
    assert usage_log.session_id == session.id
    assert usage_log.duration_minutes == 5
    assert usage_log.cost_usd == 0.05
    assert usage_log.user_plan == 'free'
    assert usage_log.is_billable == True

def test_usage_survives_client_deletion():
    """Test usage records persist after client soft deletion"""
    user = create_test_user()
    client = create_test_client(user_id=user.id)
    session = create_test_session(user_id=user.id, client_id=client.id)
    
    # Create usage log
    tracking_service = UsageTrackingService(db)
    usage_log = tracking_service.create_usage_log(session)
    
    # Soft delete client
    client_service.soft_delete_client(client.id)
    
    # Usage log should still exist with nullified client_id
    retrieved_log = db.query(UsageLog).filter_by(id=usage_log.id).first()
    assert retrieved_log is not None
    assert retrieved_log.client_id is None  # Nullified but preserved

def test_monthly_usage_reset():
    """Test monthly usage counters reset correctly"""
    user = create_test_user()
    user.usage_minutes = 50
    user.session_count = 5
    user.current_month_start = datetime(2025, 7, 1)  # Previous month
    
    tracking_service = UsageTrackingService(db)
    
    # Create usage log in new month
    with freeze_time(datetime(2025, 8, 15)):
        session = create_test_session(user_id=user.id)
        tracking_service.create_usage_log(session)
    
    # Usage counters should be reset for new month
    updated_user = db.query(User).filter_by(id=user.id).first()
    assert updated_user.current_month_start.month == 8
    assert updated_user.usage_minutes == session.duration_seconds // 60
    assert updated_user.session_count == 0  # Not incremented by usage log

def test_monthly_analytics_aggregation():
    """Test monthly analytics are correctly aggregated"""
    user = create_test_user()
    tracking_service = UsageTrackingService(db)
    
    # Create multiple usage logs in same month
    for i in range(3):
        session = create_test_session(user_id=user.id, duration_seconds=120)
        tracking_service.create_usage_log(
            session=session,
            cost_usd=0.02
        )
    
    # Check monthly analytics
    month_year = datetime.utcnow().strftime('%Y-%m')
    analytics = db.query(UsageAnalytics).filter(
        and_(
            UsageAnalytics.user_id == user.id,
            UsageAnalytics.month_year == month_year
        )
    ).first()
    
    assert analytics is not None
    assert analytics.transcriptions_completed == 3
    assert analytics.total_minutes_processed == 6  # 3 * 2 minutes
    assert analytics.total_cost_usd == 0.06  # 3 * 0.02
```

### Integration Tests
```python
def test_end_to_end_usage_tracking():
    """Test complete usage tracking workflow"""
    user = create_test_user(plan=UserPlan.FREE)
    
    # Create and complete session
    session_data = {"title": "Test Session", "language": "en-US"}
    response = client.post("/api/sessions", json=session_data)
    session_id = response.json()["session_id"]
    
    # Simulate transcription completion
    mock_transcription_result = create_mock_transcription_result(
        duration_seconds=180,
        cost_usd=0.03
    )
    
    # Complete transcription (triggers usage logging)
    complete_transcription_task(
        session_id=session_id,
        result=mock_transcription_result
    )
    
    # Verify usage log created
    usage_logs = client.get("/api/usage/history").json()["usage_history"]
    assert len(usage_logs) == 1
    assert usage_logs[0]["duration_minutes"] == 3
    assert usage_logs[0]["cost_usd"] == 0.03
    
    # Verify user counters updated
    usage_summary = client.get("/api/usage/summary").json()
    assert usage_summary["current_month"]["transcription_count"] == 1
    assert usage_summary["current_month"]["usage_minutes"] == 3
```

## 📊 Success Metrics

### Data Integrity Metrics
- **Usage Tracking Accuracy**: 100% of completed transcriptions create usage logs
- **Data Preservation**: 0% usage data loss during client/coach deletions
- **Billing Consistency**: User.usage_minutes matches sum of billable usage logs

### Performance Metrics
- **Usage Log Creation**: <50ms per log entry
- **Monthly Analytics Update**: <100ms per aggregation
- **Analytics Query Performance**: <200ms for 12-month user analytics
- **Admin Dashboard**: <2s for system-wide analytics

### Business Metrics  
- **Historical Data**: 100% usage history preserved for compliance
- **Analytics Accuracy**: Monthly analytics within 1% of raw usage logs
- **Reporting Speed**: 90% faster analytics queries vs. raw log aggregation

## 📋 Definition of Done

- [ ] **Independent Usage Logging**: UsageLog table created with proper foreign keys
- [ ] **Data Preservation**: Usage logs survive client/coach deletions with referential integrity
- [ ] **Monthly Analytics**: Pre-aggregated analytics for fast reporting
- [ ] **API Endpoints**: Complete REST API for usage data access
- [ ] **User Counter Sync**: Real-time sync between usage logs and user counters
- [ ] **Monthly Reset**: Automatic monthly usage counter reset functionality
- [ ] **Admin Analytics**: System-wide analytics for business intelligence
- [ ] **Data Migration**: Safe migration of existing usage data
- [ ] **Performance Optimization**: Proper indexing for all query patterns
- [ ] **Unit Tests**: >90% coverage for usage tracking logic
- [ ] **Integration Tests**: End-to-end usage tracking workflow tests
- [ ] **Documentation**: Complete API and service documentation

## 🔄 Dependencies & Risks

### Dependencies  
- ✅ Current session and user models
- ✅ Database migration framework
- ⏳ Plan configuration system (US002)
- ⏳ Smart billing logic (US004)

### Risks & Mitigations
- **Risk**: Large volume of usage logs affects database performance
  - **Mitigation**: Partitioning, proper indexing, archival strategy
- **Risk**: Data consistency issues between usage logs and user counters
  - **Mitigation**: Transaction boundaries, validation checks, reconciliation jobs
- **Risk**: Migration complexity with existing data
  - **Mitigation**: Incremental migration, rollback plans, validation scripts

## 📞 Stakeholders

**Product Owner**: Business Analytics Team, Finance Team  
**Technical Lead**: Backend Engineering, Data Engineering  
**Reviewers**: Data Architecture, Compliance Team, Performance Engineering  
**QA Focus**: Data integrity, Performance, Migration safety