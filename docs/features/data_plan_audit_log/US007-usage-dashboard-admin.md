# US007: Usage Dashboard for Admins

## 📋 User Story

**As a** platform administrator and business stakeholder  
**I want** comprehensive usage analytics dashboards with real-time insights and historical trends  
**So that** I can monitor platform health, optimize resources, and make data-driven business decisions

## 💼 Business Value

### Current Problem
- No centralized dashboard for monitoring platform usage and performance
- Limited visibility into user behavior patterns and resource utilization
- Difficult to identify trends, anomalies, or optimization opportunities
- Manual effort required to generate business reports and compliance summaries

### Business Impact
- **Limited Visibility**: Cannot effectively monitor platform health and user engagement
- **Resource Planning**: Insufficient data for capacity planning and cost optimization
- **Business Intelligence**: Missing insights for product development and strategy
- **Compliance Reporting**: Manual effort to generate regulatory and audit reports

### Value Delivered
- **Real-time Monitoring**: Live dashboard with key performance indicators and alerts
- **Business Intelligence**: Historical trends and predictive analytics for strategic planning
- **Resource Optimization**: Data-driven insights for cost reduction and capacity planning
- **Automated Reporting**: Self-service reports for compliance, finance, and management

## 🎯 Acceptance Criteria

### Real-time Usage Dashboard
1. **Key Performance Indicators**
   - [ ] Real-time transcription processing statistics (active, completed, failed)
   - [ ] User activity metrics (active users, new registrations, retention rates)
   - [ ] Resource utilization (STT provider usage, storage consumption, processing time)
   - [ ] Revenue metrics (usage-based billing, plan distributions, cost per user)

2. **System Health Monitoring**
   - [ ] Service availability and uptime statistics
   - [ ] Error rates and failure patterns by component
   - [ ] Performance metrics (API response times, transcription speeds)
   - [ ] Alert notifications for anomalies and threshold breaches

3. **Interactive Data Visualization**
   - [ ] Customizable time ranges (real-time, hourly, daily, weekly, monthly)
   - [ ] Drill-down capabilities for detailed analysis
   - [ ] Comparative analysis (current vs previous periods)
   - [ ] Export capabilities for charts and data

### Historical Analytics
4. **Usage Trend Analysis**
   - [ ] User growth patterns and cohort analysis
   - [ ] Transcription volume trends by time period and user segment
   - [ ] Feature adoption rates and usage patterns
   - [ ] Geographic distribution and market penetration

5. **Financial Analytics**
   - [ ] Revenue trends and forecasting
   - [ ] Cost analysis by STT provider and resource type
   - [ ] Unit economics (cost per transcription, revenue per user)
   - [ ] Billing accuracy and payment success rates

### Compliance and Reporting
6. **Automated Report Generation**
   - [ ] Daily, weekly, monthly executive summaries
   - [ ] GDPR compliance reports (data processing activities)
   - [ ] Financial reports for accounting and billing reconciliation
   - [ ] Custom report builder for ad-hoc analysis

## 🏗️ Technical Implementation

### Analytics Data Model
```python
# packages/core-logic/src/coaching_assistant/models/analytics.py

import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import BaseModel

class MetricType(enum.Enum):
    """Types of metrics collected"""
    COUNTER = "counter"         # Incrementing values (sessions created)
    GAUGE = "gauge"            # Point-in-time values (active users)
    HISTOGRAM = "histogram"    # Distribution values (processing times)
    RATE = "rate"             # Rate calculations (requests per minute)

class MetricCategory(enum.Enum):
    """Categories of metrics"""
    USAGE = "usage"           # User activity and feature usage
    PERFORMANCE = "performance"  # System performance metrics
    BUSINESS = "business"     # Revenue and business metrics
    SYSTEM = "system"         # Infrastructure and system health
    COMPLIANCE = "compliance" # GDPR and regulatory metrics

class DashboardMetric(BaseModel):
    """Real-time and historical metrics for dashboard"""
    
    # Metric identification
    metric_name = Column(String(100), nullable=False, index=True)
    metric_type = Column(Enum(MetricType), nullable=False)
    category = Column(Enum(MetricCategory), nullable=False, index=True)
    
    # Metric value and metadata
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=True)  # "count", "seconds", "bytes", "usd"
    
    # Dimensions for filtering and grouping
    dimensions = Column(JSONB, default={})  # {"stt_provider": "google", "plan": "pro"}
    
    # Time information
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    period_start = Column(DateTime(timezone=True), nullable=True)  # For aggregated metrics
    period_end = Column(DateTime(timezone=True), nullable=True)
    
    # Aggregation metadata
    aggregation_level = Column(String(20), default="raw")  # "raw", "hourly", "daily", "monthly"
    sample_count = Column(Integer, default=1)  # Number of samples aggregated
    
    def __repr__(self):
        return f"<DashboardMetric(name={self.metric_name}, value={self.value}, timestamp={self.timestamp})>"

class DashboardAlert(BaseModel):
    """Alert definitions and status"""
    
    # Alert configuration
    alert_name = Column(String(100), nullable=False, unique=True)
    description = Column(String(500), nullable=True)
    
    # Trigger conditions
    metric_name = Column(String(100), nullable=False)
    threshold_value = Column(Float, nullable=False)
    comparison_operator = Column(String(10), nullable=False)  # ">", "<", ">=", "<=", "=="
    
    # Alert settings
    is_active = Column(Boolean, default=True)
    alert_level = Column(String(20), default="warning")  # "info", "warning", "error", "critical"
    
    # Notification settings
    notification_channels = Column(JSONB, default=[])  # ["email", "slack", "webhook"]
    cooldown_minutes = Column(Integer, default=60)  # Minimum time between alerts
    
    # Alert status
    last_triggered = Column(DateTime(timezone=True), nullable=True)
    trigger_count = Column(Integer, default=0)
    is_acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(UUID(as_uuid=True), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    def should_trigger(self, current_value: float) -> bool:
        """Check if alert should trigger based on current value"""
        if not self.is_active:
            return False
            
        # Check cooldown period
        if self.last_triggered:
            cooldown_end = self.last_triggered + timedelta(minutes=self.cooldown_minutes)
            if datetime.utcnow() < cooldown_end:
                return False
        
        # Evaluate condition
        if self.comparison_operator == ">":
            return current_value > self.threshold_value
        elif self.comparison_operator == "<":
            return current_value < self.threshold_value
        elif self.comparison_operator == ">=":
            return current_value >= self.threshold_value
        elif self.comparison_operator == "<=":
            return current_value <= self.threshold_value
        elif self.comparison_operator == "==":
            return abs(current_value - self.threshold_value) < 0.001
        
        return False
```

### Analytics Service
```python
# packages/core-logic/src/coaching_assistant/services/analytics_service.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)

class AnalyticsService:
    """Service for collecting and serving analytics data"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType,
        category: MetricCategory,
        dimensions: Optional[Dict] = None,
        unit: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ) -> DashboardMetric:
        """Record a metric data point"""
        
        metric = DashboardMetric(
            metric_name=metric_name,
            metric_type=metric_type,
            category=category,
            value=value,
            unit=unit,
            dimensions=dimensions or {},
            timestamp=timestamp or datetime.utcnow(),
            aggregation_level="raw"
        )
        
        self.db.add(metric)
        self.db.commit()
        
        # Check for alert triggers
        self._check_alert_triggers(metric_name, value)
        
        return metric
    
    def get_real_time_kpis(self) -> Dict:
        """Get real-time key performance indicators"""
        
        now = datetime.utcnow()
        last_hour = now - timedelta(hours=1)
        last_24h = now - timedelta(hours=24)
        
        # Active transcriptions (currently processing)
        active_transcriptions = self.db.query(Session).filter(
            Session.status == SessionStatus.PROCESSING
        ).count()
        
        # Transcriptions completed in last hour
        recent_completions = self.db.query(Session).filter(
            and_(
                Session.status == SessionStatus.COMPLETED,
                Session.updated_at >= last_hour
            )
        ).count()
        
        # Active users (users with activity in last 24h)
        active_users = self.db.query(func.count(func.distinct(UsageLog.user_id))).filter(
            UsageLog.created_at >= last_24h
        ).scalar()
        
        # Error rate (failed transcriptions in last hour)
        failed_transcriptions = self.db.query(Session).filter(
            and_(
                Session.status == SessionStatus.FAILED,
                Session.updated_at >= last_hour
            )
        ).count()
        
        total_transcriptions = recent_completions + failed_transcriptions
        error_rate = (failed_transcriptions / max(total_transcriptions, 1)) * 100
        
        # Revenue metrics (last 24h)
        daily_revenue = self.db.query(func.sum(UsageLog.cost_usd)).filter(
            and_(
                UsageLog.created_at >= last_24h,
                UsageLog.is_billable == True
            )
        ).scalar() or 0
        
        return {
            "real_time": {
                "active_transcriptions": active_transcriptions,
                "transcriptions_last_hour": recent_completions,
                "active_users_24h": active_users,
                "error_rate_percent": round(error_rate, 2),
                "daily_revenue_usd": float(daily_revenue)
            },
            "timestamp": now.isoformat()
        }
    
    def get_usage_trends(
        self, 
        start_date: datetime, 
        end_date: datetime,
        granularity: str = "daily"
    ) -> Dict:
        """Get usage trends over time period"""
        
        # Determine grouping based on granularity
        if granularity == "hourly":
            date_trunc = func.date_trunc('hour', UsageLog.created_at)
        elif granularity == "daily":
            date_trunc = func.date_trunc('day', UsageLog.created_at)
        elif granularity == "monthly":
            date_trunc = func.date_trunc('month', UsageLog.created_at)
        else:
            date_trunc = func.date_trunc('day', UsageLog.created_at)
        
        # Transcription volume over time
        transcription_trend = self.db.query(
            date_trunc.label('period'),
            func.count(UsageLog.id).label('session_count'),
            func.sum(UsageLog.duration_minutes).label('total_minutes'),
            func.sum(UsageLog.cost_usd).label('total_cost')
        ).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).group_by('period').order_by('period').all()
        
        # User activity trend
        user_trend = self.db.query(
            date_trunc.label('period'),
            func.count(func.distinct(UsageLog.user_id)).label('active_users')
        ).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).group_by('period').order_by('period').all()
        
        # STT provider usage
        provider_usage = self.db.query(
            UsageLog.stt_provider,
            func.count(UsageLog.id).label('session_count'),
            func.sum(UsageLog.duration_minutes).label('total_minutes'),
            func.sum(UsageLog.cost_usd).label('total_cost')
        ).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).group_by(UsageLog.stt_provider).all()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "granularity": granularity
            },
            "transcription_trend": [
                {
                    "period": trend.period.isoformat(),
                    "session_count": trend.session_count,
                    "total_minutes": trend.total_minutes or 0,
                    "total_cost": float(trend.total_cost or 0)
                }
                for trend in transcription_trend
            ],
            "user_activity_trend": [
                {
                    "period": trend.period.isoformat(),
                    "active_users": trend.active_users
                }
                for trend in user_trend
            ],
            "provider_breakdown": [
                {
                    "provider": usage.stt_provider,
                    "session_count": usage.session_count,
                    "total_minutes": usage.total_minutes or 0,
                    "total_cost": float(usage.total_cost or 0),
                    "avg_cost_per_minute": float((usage.total_cost or 0) / max(usage.total_minutes or 1, 1))
                }
                for usage in provider_usage
            ]
        }
    
    def get_user_analytics(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Get detailed user analytics"""
        
        # User registration trend
        user_registrations = self.db.query(
            func.date_trunc('day', User.created_at).label('date'),
            func.count(User.id).label('registrations')
        ).filter(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date
            )
        ).group_by('date').order_by('date').all()
        
        # Plan distribution
        plan_distribution = self.db.query(
            User.plan,
            func.count(User.id).label('user_count')
        ).group_by(User.plan).all()
        
        # Usage by plan
        plan_usage = self.db.query(
            User.plan,
            func.count(UsageLog.id).label('total_sessions'),
            func.sum(UsageLog.duration_minutes).label('total_minutes'),
            func.sum(UsageLog.cost_usd).label('total_cost')
        ).join(UsageLog, User.id == UsageLog.user_id).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).group_by(User.plan).all()
        
        # Heavy users (top 10% by usage)
        heavy_users_threshold = self.db.query(
            func.percentile_cont(0.9).within_group(User.usage_minutes)
        ).scalar()
        
        heavy_users_count = self.db.query(User).filter(
            User.usage_minutes >= heavy_users_threshold
        ).count()
        
        return {
            "registration_trend": [
                {
                    "date": reg.date.isoformat(),
                    "registrations": reg.registrations
                }
                for reg in user_registrations
            ],
            "plan_distribution": [
                {
                    "plan": dist.plan.value,
                    "user_count": dist.user_count,
                    "percentage": (dist.user_count / sum(d.user_count for d in plan_distribution)) * 100
                }
                for dist in plan_distribution
            ],
            "plan_usage_analysis": [
                {
                    "plan": usage.plan.value,
                    "total_sessions": usage.total_sessions,
                    "total_minutes": usage.total_minutes or 0,
                    "total_cost": float(usage.total_cost or 0),
                    "avg_sessions_per_user": usage.total_sessions / max(next((d.user_count for d in plan_distribution if d.plan == usage.plan), 1), 1)
                }
                for usage in plan_usage
            ],
            "user_segments": {
                "heavy_users_count": heavy_users_count,
                "heavy_users_threshold_minutes": heavy_users_threshold or 0
            }
        }
    
    def get_system_performance_metrics(self) -> Dict:
        """Get system performance and health metrics"""
        
        last_hour = datetime.utcnow() - timedelta(hours=1)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        
        # Average transcription processing time
        avg_processing_time = self.db.query(
            func.avg(Session.duration_seconds).label('avg_duration')
        ).filter(
            and_(
                Session.status == SessionStatus.COMPLETED,
                Session.updated_at >= last_24h
            )
        ).scalar()
        
        # Error rates by component
        total_sessions_24h = self.db.query(Session).filter(
            Session.created_at >= last_24h
        ).count()
        
        failed_sessions_24h = self.db.query(Session).filter(
            and_(
                Session.status == SessionStatus.FAILED,
                Session.created_at >= last_24h
            )
        ).count()
        
        success_rate = ((total_sessions_24h - failed_sessions_24h) / max(total_sessions_24h, 1)) * 100
        
        # STT provider performance comparison
        provider_performance = self.db.query(
            Session.stt_provider,
            func.count(Session.id).label('total_sessions'),
            func.count(case((Session.status == SessionStatus.COMPLETED, 1))).label('successful_sessions'),
            func.avg(Session.duration_seconds).label('avg_processing_time')
        ).filter(
            Session.updated_at >= last_24h
        ).group_by(Session.stt_provider).all()
        
        return {
            "overall_health": {
                "success_rate_percent": round(success_rate, 2),
                "avg_processing_time_seconds": float(avg_processing_time or 0),
                "total_sessions_24h": total_sessions_24h,
                "failed_sessions_24h": failed_sessions_24h
            },
            "provider_performance": [
                {
                    "provider": perf.stt_provider,
                    "total_sessions": perf.total_sessions,
                    "successful_sessions": perf.successful_sessions,
                    "success_rate": (perf.successful_sessions / max(perf.total_sessions, 1)) * 100,
                    "avg_processing_time": float(perf.avg_processing_time or 0)
                }
                for perf in provider_performance
            ]
        }
    
    def _check_alert_triggers(self, metric_name: str, value: float):
        """Check if any alerts should trigger for this metric"""
        
        alerts = self.db.query(DashboardAlert).filter(
            and_(
                DashboardAlert.metric_name == metric_name,
                DashboardAlert.is_active == True
            )
        ).all()
        
        for alert in alerts:
            if alert.should_trigger(value):
                self._trigger_alert(alert, value)
    
    def _trigger_alert(self, alert: DashboardAlert, current_value: float):
        """Trigger an alert notification"""
        
        alert.last_triggered = datetime.utcnow()
        alert.trigger_count += 1
        alert.is_acknowledged = False
        
        self.db.commit()
        
        # Send notifications (implement based on notification_channels)
        logger.warning(
            f"Alert triggered: {alert.alert_name} - "
            f"Current value: {current_value}, Threshold: {alert.threshold_value}"
        )
        
        # TODO: Implement actual notification sending (email, Slack, etc.)
```

### Dashboard API Endpoints
```python
# packages/core-logic/src/coaching_assistant/api/admin/dashboard.py

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from ...services.analytics_service import AnalyticsService

router = APIRouter()

@router.get("/kpis")
async def get_real_time_kpis(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get real-time key performance indicators"""
    
    analytics_service = AnalyticsService(db)
    kpis = analytics_service.get_real_time_kpis()
    
    return kpis

@router.get("/usage-trends")
async def get_usage_trends(
    start_date: datetime = Query(..., description="Start date for analysis"),
    end_date: datetime = Query(..., description="End date for analysis"),
    granularity: str = Query("daily", regex="^(hourly|daily|monthly)$"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get usage trends over specified time period"""
    
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    analytics_service = AnalyticsService(db)
    trends = analytics_service.get_usage_trends(start_date, end_date, granularity)
    
    return trends

@router.get("/user-analytics")
async def get_user_analytics(
    start_date: datetime = Query(default_factory=lambda: datetime.utcnow() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=lambda: datetime.utcnow()),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get detailed user analytics and segmentation"""
    
    analytics_service = AnalyticsService(db)
    user_analytics = analytics_service.get_user_analytics(start_date, end_date)
    
    return user_analytics

@router.get("/system-performance")
async def get_system_performance(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get system performance and health metrics"""
    
    analytics_service = AnalyticsService(db)
    performance_metrics = analytics_service.get_system_performance_metrics()
    
    return performance_metrics

@router.get("/compliance-summary")
async def get_compliance_summary(
    start_date: datetime = Query(default_factory=lambda: datetime.utcnow() - timedelta(days=30)),
    end_date: datetime = Query(default_factory=lambda: datetime.utcnow()),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get GDPR and compliance metrics summary"""
    
    # GDPR processing activities
    gdpr_requests = db.query(GDPRAnonymization).filter(
        and_(
            GDPRAnonymization.request_date >= start_date,
            GDPRAnonymization.request_date <= end_date
        )
    ).all()
    
    # Data retention policy executions
    retention_executions = db.query(DataRetentionExecution).filter(
        and_(
            DataRetentionExecution.started_at >= start_date,
            DataRetentionExecution.started_at <= end_date
        )
    ).all()
    
    # Audit log statistics
    audit_log_count = db.query(AuditLog).filter(
        and_(
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date
        )
    ).count()
    
    critical_audit_events = db.query(AuditLog).filter(
        and_(
            AuditLog.timestamp >= start_date,
            AuditLog.timestamp <= end_date,
            AuditLog.severity == AuditSeverity.CRITICAL
        )
    ).count()
    
    return {
        "period": {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        },
        "gdpr_compliance": {
            "total_requests": len(gdpr_requests),
            "erasure_requests": len([r for r in gdpr_requests if r.request_type == 'erasure']),
            "access_requests": len([r for r in gdpr_requests if r.request_type == 'access']),
            "avg_processing_time_hours": sum(
                (r.processed_date - r.request_date).total_seconds() / 3600 
                for r in gdpr_requests if r.processed_date
            ) / max(len(gdpr_requests), 1)
        },
        "data_retention": {
            "policy_executions": len(retention_executions),
            "successful_executions": len([e for e in retention_executions if e.status == 'completed']),
            "records_processed": sum(e.records_processed for e in retention_executions),
            "records_anonymized": sum(e.actions_taken.get('anonymized', 0) for e in retention_executions),
            "records_deleted": sum(e.actions_taken.get('deleted', 0) for e in retention_executions)
        },
        "audit_trail": {
            "total_audit_entries": audit_log_count,
            "critical_events": critical_audit_events,
            "audit_coverage_percent": 100  # Assuming full coverage
        }
    }

@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get active alerts and their status"""
    
    alerts = db.query(DashboardAlert).filter(
        DashboardAlert.is_active == True
    ).order_by(DashboardAlert.last_triggered.desc()).all()
    
    return {
        "alerts": [
            {
                "id": str(alert.id),
                "alert_name": alert.alert_name,
                "description": alert.description,
                "metric_name": alert.metric_name,
                "threshold_value": alert.threshold_value,
                "comparison_operator": alert.comparison_operator,
                "alert_level": alert.alert_level,
                "last_triggered": alert.last_triggered.isoformat() if alert.last_triggered else None,
                "trigger_count": alert.trigger_count,
                "is_acknowledged": alert.is_acknowledged
            }
            for alert in alerts
        ]
    }

@router.post("/export-report")
async def export_analytics_report(
    report_type: str = Query(..., regex="^(executive|compliance|financial|technical)$"),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    format: str = Query("json", regex="^(json|csv|pdf)$"),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Export comprehensive analytics report"""
    
    analytics_service = AnalyticsService(db)
    
    # Collect data based on report type
    report_data = {}
    
    if report_type == "executive":
        report_data = {
            "kpis": analytics_service.get_real_time_kpis(),
            "usage_trends": analytics_service.get_usage_trends(start_date, end_date, "daily"),
            "user_analytics": analytics_service.get_user_analytics(start_date, end_date),
            "system_performance": analytics_service.get_system_performance_metrics()
        }
    
    elif report_type == "compliance":
        # Get compliance data from previous endpoint
        pass
    
    # Format response based on requested format
    if format == "json":
        return {
            "report_type": report_type,
            "generated_at": datetime.utcnow().isoformat(),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat()
            },
            "data": report_data
        }
    
    # TODO: Implement CSV and PDF export
    return {"message": "Report generation not implemented for this format"}
```

### Frontend Dashboard Components
```tsx
// apps/web/app/admin/dashboard/page.tsx

'use client'

import { useState, useEffect } from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

interface KPIs {
  real_time: {
    active_transcriptions: number
    transcriptions_last_hour: number
    active_users_24h: number
    error_rate_percent: number
    daily_revenue_usd: number
  }
  timestamp: string
}

export default function AdminDashboard() {
  const [kpis, setKpis] = useState<KPIs | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchKPIs = async () => {
      try {
        const response = await fetch('/api/v1/admin/dashboard/kpis')
        if (!response.ok) throw new Error('Failed to fetch KPIs')
        
        const data = await response.json()
        setKpis(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchKPIs()
    
    // Refresh every 30 seconds
    const interval = setInterval(fetchKPIs, 30000)
    return () => clearInterval(interval)
  }, [])

  if (loading) return <div className="p-6">Loading dashboard...</div>
  if (error) return <Alert><AlertDescription>Error: {error}</AlertDescription></Alert>
  if (!kpis) return <Alert><AlertDescription>No data available</AlertDescription></Alert>

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Admin Dashboard</h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date(kpis.timestamp).toLocaleTimeString()}
        </div>
      </div>

      {/* Real-time KPIs */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <KPICard
          title="Active Transcriptions"
          value={kpis.real_time.active_transcriptions}
          unit="sessions"
          description="Currently processing"
        />
        <KPICard
          title="Completions (1h)"
          value={kpis.real_time.transcriptions_last_hour}
          unit="sessions"
          description="Last hour"
        />
        <KPICard
          title="Active Users"
          value={kpis.real_time.active_users_24h}
          unit="users"
          description="Last 24 hours"
        />
        <KPICard
          title="Error Rate"
          value={kpis.real_time.error_rate_percent}
          unit="%"
          description="Last hour"
          isError={kpis.real_time.error_rate_percent > 5}
        />
        <KPICard
          title="Daily Revenue"
          value={kpis.real_time.daily_revenue_usd}
          unit="USD"
          prefix="$"
          description="Last 24 hours"
        />
      </div>

      {/* Charts and detailed analytics would go here */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <UsageTrendsChart />
        <SystemHealthChart />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <UserAnalyticsCard />
        <ProviderPerformanceCard />
        <ComplianceStatusCard />
      </div>
    </div>
  )
}

function KPICard({ 
  title, 
  value, 
  unit, 
  prefix = '', 
  description, 
  isError = false 
}: {
  title: string
  value: number
  unit: string
  prefix?: string
  description: string
  isError?: boolean
}) {
  const formatValue = (val: number) => {
    if (unit === 'USD') return val.toFixed(2)
    if (val >= 1000) return `${(val / 1000).toFixed(1)}k`
    return val.toString()
  }

  return (
    <Card className={isError ? 'border-red-500' : ''}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-2xl font-bold ${isError ? 'text-red-600' : ''}`}>
          {prefix}{formatValue(value)} {unit !== 'USD' && unit}
        </div>
        <p className="text-xs text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  )
}

function UsageTrendsChart() {
  // Implementation with chart library (e.g., recharts)
  return (
    <Card>
      <CardHeader>
        <CardTitle>Usage Trends (7 days)</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Chart implementation */}
        <div className="h-64 flex items-center justify-center text-gray-500">
          Usage trends chart placeholder
        </div>
      </CardContent>
    </Card>
  )
}

function SystemHealthChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>System Health</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-64 flex items-center justify-center text-gray-500">
          System health metrics placeholder
        </div>
      </CardContent>
    </Card>
  )
}

function UserAnalyticsCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>User Analytics</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>New Users (7d):</span>
            <span className="font-semibold">24</span>
          </div>
          <div className="flex justify-between">
            <span>Free Plan:</span>
            <span className="font-semibold">85%</span>
          </div>
          <div className="flex justify-between">
            <span>Pro Plan:</span>
            <span className="font-semibold">15%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ProviderPerformanceCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>STT Providers</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Google STT:</span>
            <span className="font-semibold text-green-600">98.5%</span>
          </div>
          <div className="flex justify-between">
            <span>AssemblyAI:</span>
            <span className="font-semibold text-green-600">97.2%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ComplianceStatusCard() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Compliance Status</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>GDPR Requests:</span>
            <span className="font-semibold text-green-600">2 (processed)</span>
          </div>
          <div className="flex justify-between">
            <span>Data Retention:</span>
            <span className="font-semibold text-green-600">Compliant</span>
          </div>
          <div className="flex justify-between">
            <span>Audit Coverage:</span>
            <span className="font-semibold text-green-600">100%</span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
```

## 🧪 Test Scenarios

### Analytics Service Tests
```python
def test_real_time_kpis_calculation():
    """Test real-time KPI calculations"""
    # Create test data
    active_session = create_test_session(db, user_id, status=SessionStatus.PROCESSING)
    completed_session = create_test_session(db, user_id, status=SessionStatus.COMPLETED)
    usage_log = create_usage_log(db, session_id=completed_session.id, cost_usd=0.05)
    
    analytics_service = AnalyticsService(db)
    kpis = analytics_service.get_real_time_kpis()
    
    assert kpis["real_time"]["active_transcriptions"] >= 1
    assert kpis["real_time"]["daily_revenue_usd"] >= 0.05
    assert "timestamp" in kpis

def test_usage_trends_aggregation():
    """Test usage trends calculation over time periods"""
    # Create usage data over multiple days
    start_date = datetime.utcnow() - timedelta(days=7)
    end_date = datetime.utcnow()
    
    for i in range(7):
        date = start_date + timedelta(days=i)
        create_usage_log(db, created_at=date, duration_minutes=30, cost_usd=0.10)
    
    analytics_service = AnalyticsService(db)
    trends = analytics_service.get_usage_trends(start_date, end_date, "daily")
    
    assert len(trends["transcription_trend"]) == 7
    assert all(trend["session_count"] >= 1 for trend in trends["transcription_trend"])
```

### Dashboard API Tests
```bash
# Test: Real-time KPIs endpoint
curl -X GET "/api/v1/admin/dashboard/kpis" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns real-time metrics with proper structure

# Test: Usage trends with date range
curl -X GET "/api/v1/admin/dashboard/usage-trends?start_date=2025-08-01&end_date=2025-08-14&granularity=daily" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns daily usage trends for specified period
```

## 📊 Success Metrics

### Dashboard Performance
- **Load Time**: <2 seconds for dashboard initial load
- **Refresh Rate**: Real-time updates every 30 seconds
- **Data Accuracy**: 100% accuracy in KPI calculations
- **Query Performance**: <500ms for analytics queries

### Business Value
- **Decision Speed**: 50% faster business decision-making with real-time insights
- **Issue Detection**: 90% of system issues detected within 5 minutes
- **Resource Optimization**: 25% improvement in resource allocation efficiency

## 📋 Definition of Done

- [ ] **Analytics Data Model**: Comprehensive metrics and alerts model
- [ ] **Analytics Service**: Real-time KPIs, trends, and performance analytics
- [ ] **Dashboard API**: Complete admin dashboard API endpoints
- [ ] **Frontend Dashboard**: Interactive admin dashboard with real-time updates
- [ ] **Alert System**: Configurable alerts for system monitoring
- [ ] **Export Functionality**: Report generation in multiple formats
- [ ] **Performance Optimization**: Sub-second response times for dashboard queries
- [ ] **Unit Tests**: >85% coverage for analytics components
- [ ] **Integration Tests**: End-to-end dashboard functionality
- [ ] **Documentation**: Admin guide for dashboard usage and configuration

## 🔄 Dependencies & Risks

### Dependencies
- ✅ US001 (Usage Analytics Foundation) - Required for usage data
- ✅ US005 (Audit Trail Logging) - Required for compliance metrics
- ⏳ Data visualization library for frontend charts
- ⏳ Real-time data streaming infrastructure

### Risks & Mitigations
- **Risk**: Dashboard performance impact on main database
  - **Mitigation**: Read replicas, caching, optimized queries
- **Risk**: Information overload in dashboard interface
  - **Mitigation**: Progressive disclosure, customizable views, clear priorities
- **Risk**: Data privacy in admin dashboards
  - **Mitigation**: Aggregated data only, role-based access, audit logging

## 📞 Stakeholders

**Product Owner**: Business Operations Team  
**Technical Lead**: Frontend/Backend Engineering, Data Analytics  
**Reviewers**: Business Intelligence, Product Management, DevOps  
**QA Focus**: Data accuracy, Performance testing, User experience