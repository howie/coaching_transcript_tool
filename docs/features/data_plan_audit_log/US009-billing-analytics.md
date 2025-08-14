# US009: Billing Analytics & Insights

## 📋 User Story

**As a** business stakeholder and finance team member  
**I want** comprehensive billing analytics and financial insights  
**So that** I can optimize pricing, forecast revenue, and analyze unit economics

## 💼 Business Value

### Current Problem
- Limited visibility into billing patterns and revenue metrics
- No detailed cost analysis by STT provider or user segment
- Difficult to identify pricing optimization opportunities
- Manual effort required for financial reporting and forecasting

### Business Impact
- **Revenue Optimization**: Missing insights for pricing strategy improvements
- **Cost Management**: Inability to optimize STT provider costs and margins
- **Financial Planning**: Limited data for revenue forecasting and budgeting
- **Business Intelligence**: Lack of unit economics and profitability analysis

### Value Delivered
- **Revenue Insights**: Detailed analysis of revenue patterns and growth drivers
- **Cost Optimization**: Provider cost analysis and margin improvement opportunities
- **Financial Forecasting**: Data-driven revenue and usage predictions
- **Unit Economics**: Complete understanding of customer lifetime value and costs

## 🎯 Acceptance Criteria

### Revenue Analytics
1. **Revenue Tracking and Trends**
   - [ ] Monthly, quarterly, and annual revenue reporting
   - [ ] Revenue growth rates and trend analysis
   - [ ] Revenue breakdown by user plan and segment
   - [ ] Average revenue per user (ARPU) calculations

2. **Billing Efficiency Analysis**
   - [ ] Successful vs failed billing transactions
   - [ ] Payment method performance and success rates
   - [ ] Revenue recognition and accrual tracking
   - [ ] Churn analysis and revenue impact

### Cost Analysis
3. **STT Provider Cost Analysis**
   - [ ] Cost breakdown by provider (Google STT, AssemblyAI)
   - [ ] Provider performance vs cost comparison
   - [ ] Usage patterns and provider optimization opportunities
   - [ ] Margin analysis by provider and service type

4. **Unit Economics**
   - [ ] Cost per transcription by provider and duration
   - [ ] Customer acquisition cost (CAC) and lifetime value (CLV)
   - [ ] Gross margin analysis by user segment
   - [ ] Break-even analysis for different plan types

### Business Intelligence
5. **Usage-Based Billing Analytics**
   - [ ] Usage patterns and billing accuracy verification
   - [ ] Free tier conversion rates to paid plans
   - [ ] Usage limit breaches and upgrade triggers
   - [ ] Seasonal usage patterns and revenue impact

6. **Financial Forecasting**
   - [ ] Revenue forecasting based on usage trends
   - [ ] Cost projections for capacity planning
   - [ ] Scenario analysis for pricing changes
   - [ ] Budget variance reporting and alerts

## 🏗️ Technical Implementation

### Billing Analytics Models
```python
# packages/core-logic/src/coaching_assistant/models/billing_analytics.py

import enum
from datetime import datetime, timedelta
from sqlalchemy import Column, String, Integer, Float, DateTime, Enum, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from .base import BaseModel

class RevenueMetricType(enum.Enum):
    """Types of revenue metrics"""
    MONTHLY_RECURRING_REVENUE = "mrr"
    ANNUAL_RECURRING_REVENUE = "arr"
    AVERAGE_REVENUE_PER_USER = "arpu"
    CUSTOMER_LIFETIME_VALUE = "clv"
    CHURN_RATE = "churn_rate"
    CONVERSION_RATE = "conversion_rate"

class CostMetricType(enum.Enum):
    """Types of cost metrics"""
    STT_PROVIDER_COST = "stt_provider_cost"
    INFRASTRUCTURE_COST = "infrastructure_cost"
    CUSTOMER_ACQUISITION_COST = "cac"
    GROSS_MARGIN = "gross_margin"
    COST_PER_TRANSCRIPTION = "cost_per_transcription"

class BillingAnalytics(BaseModel):
    """Aggregated billing analytics data"""
    
    # Time period
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False)  # "daily", "weekly", "monthly", "quarterly"
    
    # Revenue metrics
    total_revenue = Column(Float, default=0.0)
    recurring_revenue = Column(Float, default=0.0)  # Subscription revenue
    usage_based_revenue = Column(Float, default=0.0)  # Pay-per-use revenue
    
    # User metrics
    active_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    churned_users = Column(Integer, default=0)
    
    # Usage metrics
    total_transcriptions = Column(Integer, default=0)
    total_minutes_transcribed = Column(Integer, default=0)
    billable_transcriptions = Column(Integer, default=0)
    free_transcriptions = Column(Integer, default=0)  # Retries, free tier
    
    # Cost metrics
    total_stt_costs = Column(Float, default=0.0)
    google_stt_costs = Column(Float, default=0.0)
    assemblyai_costs = Column(Float, default=0.0)
    
    # Plan breakdown
    plan_metrics = Column(JSONB, default={})  # {"free": {"users": 100, "revenue": 0}, "pro": {...}}
    
    # Provider performance
    provider_metrics = Column(JSONB, default={})  # Provider-specific analytics
    
    # Calculated KPIs
    average_revenue_per_user = Column(Float, default=0.0)
    cost_per_transcription = Column(Float, default=0.0)
    gross_margin_percent = Column(Float, default=0.0)
    
    def __repr__(self):
        return f"<BillingAnalytics(period={self.period_start.date()}-{self.period_end.date()}, revenue=${self.total_revenue:.2f})>"
    
    @property
    def revenue_per_minute(self) -> float:
        """Calculate revenue per minute transcribed"""
        if self.total_minutes_transcribed > 0:
            return self.usage_based_revenue / self.total_minutes_transcribed
        return 0.0
    
    @property
    def conversion_rate(self) -> float:
        """Calculate conversion rate from free to paid users"""
        if self.new_users > 0:
            paid_conversions = sum(
                metrics.get('new_users', 0) 
                for plan, metrics in self.plan_metrics.items() 
                if plan != 'free'
            )
            return (paid_conversions / self.new_users) * 100
        return 0.0

class RevenueProjection(BaseModel):
    """Revenue forecasting and projections"""
    
    # Projection period
    projection_date = Column(DateTime(timezone=True), nullable=False)
    projection_period_months = Column(Integer, nullable=False)  # 1, 3, 6, 12 months
    
    # Projection basis
    based_on_period_start = Column(DateTime(timezone=True), nullable=False)
    based_on_period_end = Column(DateTime(timezone=True), nullable=False)
    
    # Projected metrics
    projected_revenue = Column(Float, nullable=False)
    projected_users = Column(Integer, nullable=False)
    projected_usage_minutes = Column(Integer, nullable=False)
    
    # Confidence and assumptions
    confidence_level = Column(Float, default=80.0)  # Percentage confidence
    assumptions = Column(JSONB, default={})  # Growth rates, seasonal factors
    
    # Model metadata
    model_type = Column(String(50), default="linear_regression")
    model_accuracy = Column(Float, nullable=True)  # R-squared or similar
    
    created_by = Column(UUID(as_uuid=True), nullable=False)
    
    @property
    def monthly_growth_rate(self) -> float:
        """Calculate implied monthly growth rate"""
        if self.projection_period_months > 0:
            # Calculate compound monthly growth rate
            import math
            period_months = (self.based_on_period_end - self.based_on_period_start).days / 30.44
            if period_months > 0:
                current_monthly_revenue = self.projected_revenue / self.projection_period_months
                # This is simplified - actual calculation would use historical data
                return 5.0  # Placeholder
        return 0.0
```

### Billing Analytics Service
```python
# packages/core-logic/src/coaching_assistant/services/billing_analytics_service.py

from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
import numpy as np
from sklearn.linear_model import LinearRegression
import logging

logger = logging.getLogger(__name__)

class BillingAnalyticsService:
    """Service for billing analytics and financial insights"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def generate_period_analytics(
        self,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "monthly"
    ) -> BillingAnalytics:
        """Generate comprehensive billing analytics for period"""
        
        # Revenue calculations
        revenue_data = self._calculate_revenue_metrics(period_start, period_end)
        
        # User metrics
        user_data = self._calculate_user_metrics(period_start, period_end)
        
        # Usage metrics
        usage_data = self._calculate_usage_metrics(period_start, period_end)
        
        # Cost metrics
        cost_data = self._calculate_cost_metrics(period_start, period_end)
        
        # Plan breakdown
        plan_data = self._calculate_plan_metrics(period_start, period_end)
        
        # Provider performance
        provider_data = self._calculate_provider_metrics(period_start, period_end)
        
        # Calculate derived KPIs
        arpu = revenue_data['total_revenue'] / max(user_data['active_users'], 1)
        cost_per_transcription = cost_data['total_costs'] / max(usage_data['total_transcriptions'], 1)
        gross_margin = ((revenue_data['total_revenue'] - cost_data['total_costs']) / max(revenue_data['total_revenue'], 1)) * 100
        
        analytics = BillingAnalytics(
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            
            total_revenue=revenue_data['total_revenue'],
            recurring_revenue=revenue_data['recurring_revenue'],
            usage_based_revenue=revenue_data['usage_based_revenue'],
            
            active_users=user_data['active_users'],
            new_users=user_data['new_users'],
            churned_users=user_data['churned_users'],
            
            total_transcriptions=usage_data['total_transcriptions'],
            total_minutes_transcribed=usage_data['total_minutes'],
            billable_transcriptions=usage_data['billable_transcriptions'],
            free_transcriptions=usage_data['free_transcriptions'],
            
            total_stt_costs=cost_data['total_costs'],
            google_stt_costs=cost_data['google_costs'],
            assemblyai_costs=cost_data['assemblyai_costs'],
            
            plan_metrics=plan_data,
            provider_metrics=provider_data,
            
            average_revenue_per_user=arpu,
            cost_per_transcription=cost_per_transcription,
            gross_margin_percent=gross_margin
        )
        
        self.db.add(analytics)
        self.db.commit()
        
        logger.info(f"Generated billing analytics for {period_start.date()} to {period_end.date()}")
        
        return analytics
    
    def _calculate_revenue_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate revenue metrics for period"""
        
        # Usage-based revenue from transcriptions
        usage_revenue = self.db.query(func.sum(UsageLog.cost_usd)).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date,
                UsageLog.is_billable == True
            )
        ).scalar() or 0.0
        
        # TODO: Add subscription revenue when implemented
        recurring_revenue = 0.0  # Placeholder for subscription revenue
        
        total_revenue = usage_revenue + recurring_revenue
        
        return {
            'total_revenue': float(total_revenue),
            'usage_based_revenue': float(usage_revenue),
            'recurring_revenue': float(recurring_revenue)
        }
    
    def _calculate_user_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate user metrics for period"""
        
        # Active users (users with activity in period)
        active_users = self.db.query(func.count(func.distinct(UsageLog.user_id))).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).scalar() or 0
        
        # New users (registered in period)
        new_users = self.db.query(User).filter(
            and_(
                User.created_at >= start_date,
                User.created_at <= end_date
            )
        ).count()
        
        # TODO: Calculate churned users based on inactivity
        churned_users = 0  # Placeholder
        
        return {
            'active_users': active_users,
            'new_users': new_users,
            'churned_users': churned_users
        }
    
    def _calculate_usage_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate usage metrics for period"""
        
        usage_stats = self.db.query(
            func.count(UsageLog.id).label('total_transcriptions'),
            func.sum(UsageLog.duration_minutes).label('total_minutes'),
            func.count(case((UsageLog.is_billable == True, 1))).label('billable_transcriptions'),
            func.count(case((UsageLog.is_billable == False, 1))).label('free_transcriptions')
        ).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).first()
        
        return {
            'total_transcriptions': usage_stats.total_transcriptions or 0,
            'total_minutes': usage_stats.total_minutes or 0,
            'billable_transcriptions': usage_stats.billable_transcriptions or 0,
            'free_transcriptions': usage_stats.free_transcriptions or 0
        }
    
    def _calculate_cost_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate cost metrics for period"""
        
        # STT provider costs
        cost_by_provider = self.db.query(
            UsageLog.stt_provider,
            func.sum(UsageLog.cost_usd).label('total_cost')
        ).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).group_by(UsageLog.stt_provider).all()
        
        google_costs = 0.0
        assemblyai_costs = 0.0
        total_costs = 0.0
        
        for provider_cost in cost_by_provider:
            cost = float(provider_cost.total_cost or 0)
            total_costs += cost
            
            if provider_cost.stt_provider == 'google':
                google_costs = cost
            elif provider_cost.stt_provider == 'assemblyai':
                assemblyai_costs = cost
        
        return {
            'total_costs': total_costs,
            'google_costs': google_costs,
            'assemblyai_costs': assemblyai_costs
        }
    
    def _calculate_plan_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate metrics breakdown by user plan"""
        
        plan_stats = self.db.query(
            User.plan,
            func.count(func.distinct(UsageLog.user_id)).label('active_users'),
            func.sum(UsageLog.cost_usd).label('revenue'),
            func.count(UsageLog.id).label('transcriptions')
        ).join(
            UsageLog, User.id == UsageLog.user_id
        ).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date
            )
        ).group_by(User.plan).all()
        
        plan_metrics = {}
        for stat in plan_stats:
            plan_metrics[stat.plan.value] = {
                'active_users': stat.active_users or 0,
                'revenue': float(stat.revenue or 0),
                'transcriptions': stat.transcriptions or 0,
                'revenue_per_user': float(stat.revenue or 0) / max(stat.active_users or 1, 1)
            }
        
        return plan_metrics
    
    def _calculate_provider_metrics(self, start_date: datetime, end_date: datetime) -> Dict:
        """Calculate STT provider performance metrics"""
        
        provider_stats = self.db.query(
            UsageLog.stt_provider,
            func.count(UsageLog.id).label('transcriptions'),
            func.sum(UsageLog.duration_minutes).label('minutes'),
            func.sum(UsageLog.cost_usd).label('cost'),
            func.avg(UsageLog.cost_usd / UsageLog.duration_minutes).label('cost_per_minute')
        ).filter(
            and_(
                UsageLog.created_at >= start_date,
                UsageLog.created_at <= end_date,
                UsageLog.duration_minutes > 0
            )
        ).group_by(UsageLog.stt_provider).all()
        
        provider_metrics = {}
        for stat in provider_stats:
            provider_metrics[stat.stt_provider] = {
                'transcriptions': stat.transcriptions or 0,
                'minutes': stat.minutes or 0,
                'cost': float(stat.cost or 0),
                'cost_per_minute': float(stat.cost_per_minute or 0),
                'market_share_percent': 0.0  # Calculate after loop
            }
        
        # Calculate market share
        total_transcriptions = sum(m['transcriptions'] for m in provider_metrics.values())
        for provider in provider_metrics:
            provider_metrics[provider]['market_share_percent'] = (
                provider_metrics[provider]['transcriptions'] / max(total_transcriptions, 1)
            ) * 100
        
        return provider_metrics
    
    def generate_revenue_forecast(
        self,
        forecast_months: int = 6,
        confidence_level: float = 80.0
    ) -> RevenueProjection:
        """Generate revenue forecast using historical data"""
        
        # Get historical monthly data for trend analysis
        monthly_data = self.db.query(BillingAnalytics).filter(
            BillingAnalytics.period_type == 'monthly'
        ).order_by(BillingAnalytics.period_start.desc()).limit(12).all()
        
        if len(monthly_data) < 3:
            raise ValueError("Insufficient historical data for forecasting (need at least 3 months)")
        
        # Prepare data for regression
        X = np.array([i for i in range(len(monthly_data))]).reshape(-1, 1)
        y = np.array([float(data.total_revenue) for data in reversed(monthly_data)])
        
        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate forecast
        future_X = np.array([len(monthly_data) + i for i in range(1, forecast_months + 1)]).reshape(-1, 1)
        future_revenue = model.predict(future_X)
        
        # Calculate total projected revenue
        projected_revenue = float(np.sum(future_revenue))
        
        # Estimate other metrics based on historical averages
        avg_arpu = np.mean([data.average_revenue_per_user for data in monthly_data])
        projected_users = int(projected_revenue / (avg_arpu * forecast_months)) if avg_arpu > 0 else 0
        
        avg_minutes_per_dollar = np.mean([
            data.total_minutes_transcribed / max(data.total_revenue, 1) 
            for data in monthly_data
        ])
        projected_usage_minutes = int(projected_revenue * avg_minutes_per_dollar)
        
        # Calculate model accuracy (R-squared)
        model_accuracy = float(model.score(X, y))
        
        projection = RevenueProjection(
            projection_date=datetime.utcnow(),
            projection_period_months=forecast_months,
            based_on_period_start=monthly_data[-1].period_start,
            based_on_period_end=monthly_data[0].period_end,
            projected_revenue=projected_revenue,
            projected_users=projected_users,
            projected_usage_minutes=projected_usage_minutes,
            confidence_level=confidence_level,
            model_type="linear_regression",
            model_accuracy=model_accuracy,
            assumptions={
                'historical_months_used': len(monthly_data),
                'avg_monthly_growth_rate': float(model.coef_[0]),
                'seasonal_adjustments': False
            },
            created_by=UUID('00000000-0000-0000-0000-000000000001')  # System user
        )
        
        self.db.add(projection)
        self.db.commit()
        
        return projection
    
    def get_unit_economics_analysis(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict:
        """Generate comprehensive unit economics analysis"""
        
        # Get period analytics
        analytics = self.db.query(BillingAnalytics).filter(
            and_(
                BillingAnalytics.period_start >= start_date,
                BillingAnalytics.period_end <= end_date
            )
        ).all()
        
        if not analytics:
            raise ValueError("No analytics data found for specified period")
        
        # Aggregate metrics
        total_revenue = sum(a.total_revenue for a in analytics)
        total_costs = sum(a.total_stt_costs for a in analytics)
        total_users = sum(a.active_users for a in analytics) / len(analytics)  # Average
        total_transcriptions = sum(a.total_transcriptions for a in analytics)
        
        # Calculate unit economics
        customer_lifetime_value = total_revenue / max(total_users, 1) * 12  # Annualized
        customer_acquisition_cost = 0.0  # TODO: Implement when marketing costs tracked
        gross_margin = ((total_revenue - total_costs) / max(total_revenue, 1)) * 100
        
        # Provider efficiency analysis
        provider_efficiency = {}
        for analytics_period in analytics:
            for provider, metrics in analytics_period.provider_metrics.items():
                if provider not in provider_efficiency:
                    provider_efficiency[provider] = {
                        'total_cost': 0,
                        'total_minutes': 0,
                        'total_transcriptions': 0
                    }
                
                provider_efficiency[provider]['total_cost'] += metrics.get('cost', 0)
                provider_efficiency[provider]['total_minutes'] += metrics.get('minutes', 0)
                provider_efficiency[provider]['total_transcriptions'] += metrics.get('transcriptions', 0)
        
        # Calculate efficiency metrics
        for provider in provider_efficiency:
            pe = provider_efficiency[provider]
            pe['cost_per_minute'] = pe['total_cost'] / max(pe['total_minutes'], 1)
            pe['cost_per_transcription'] = pe['total_cost'] / max(pe['total_transcriptions'], 1)
        
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'financial_metrics': {
                'total_revenue': total_revenue,
                'total_costs': total_costs,
                'gross_profit': total_revenue - total_costs,
                'gross_margin_percent': gross_margin
            },
            'unit_economics': {
                'customer_lifetime_value': customer_lifetime_value,
                'customer_acquisition_cost': customer_acquisition_cost,
                'ltv_cac_ratio': customer_lifetime_value / max(customer_acquisition_cost, 1) if customer_acquisition_cost > 0 else float('inf'),
                'average_revenue_per_user': total_revenue / max(total_users, 1),
                'cost_per_transcription': total_costs / max(total_transcriptions, 1)
            },
            'provider_efficiency': provider_efficiency,
            'optimization_recommendations': self._generate_optimization_recommendations(provider_efficiency, gross_margin)
        }
    
    def _generate_optimization_recommendations(self, provider_efficiency: Dict, gross_margin: float) -> List[str]:
        """Generate optimization recommendations based on analysis"""
        
        recommendations = []
        
        # Margin optimization
        if gross_margin < 70:
            recommendations.append("Consider negotiating better rates with STT providers or increasing pricing")
        
        # Provider optimization
        if len(provider_efficiency) > 1:
            costs = [(p, data['cost_per_minute']) for p, data in provider_efficiency.items()]
            costs.sort(key=lambda x: x[1])
            
            if len(costs) >= 2 and costs[1][1] > costs[0][1] * 1.2:  # 20% more expensive
                recommendations.append(f"Consider shifting more volume to {costs[0][0]} for cost optimization")
        
        # Usage patterns
        if gross_margin > 80:
            recommendations.append("Strong margins detected - consider investing in growth or reducing prices")
        
        return recommendations
```

### Billing Analytics API
```python
# packages/core-logic/src/coaching_assistant/api/admin/billing_analytics.py

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query, HTTPException
from ...services.billing_analytics_service import BillingAnalyticsService

router = APIRouter()

@router.get("/overview")
async def get_billing_overview(
    period_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get billing analytics overview"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    analytics_service = BillingAnalyticsService(db)
    
    # Get or generate analytics for the period
    analytics = db.query(BillingAnalytics).filter(
        and_(
            BillingAnalytics.period_start >= start_date,
            BillingAnalytics.period_end <= end_date,
            BillingAnalytics.period_type == 'monthly'
        )
    ).order_by(BillingAnalytics.period_start.desc()).all()
    
    # Calculate summary metrics
    total_revenue = sum(a.total_revenue for a in analytics)
    total_costs = sum(a.total_stt_costs for a in analytics)
    total_transcriptions = sum(a.total_transcriptions for a in analytics)
    
    return {
        'period': {
            'days': period_days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'summary': {
            'total_revenue': total_revenue,
            'total_costs': total_costs,
            'gross_profit': total_revenue - total_costs,
            'gross_margin_percent': ((total_revenue - total_costs) / max(total_revenue, 1)) * 100,
            'total_transcriptions': total_transcriptions,
            'average_revenue_per_transcription': total_revenue / max(total_transcriptions, 1)
        },
        'monthly_breakdown': [
            {
                'period': f"{a.period_start.year}-{a.period_start.month:02d}",
                'revenue': a.total_revenue,
                'costs': a.total_stt_costs,
                'transcriptions': a.total_transcriptions,
                'active_users': a.active_users,
                'arpu': a.average_revenue_per_user
            }
            for a in analytics
        ]
    }

@router.get("/revenue-forecast")
async def get_revenue_forecast(
    months: int = Query(6, ge=1, le=24),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate revenue forecast"""
    
    analytics_service = BillingAnalyticsService(db)
    
    try:
        projection = analytics_service.generate_revenue_forecast(
            forecast_months=months,
            confidence_level=80.0
        )
        
        return {
            'forecast_period_months': months,
            'projected_revenue': projection.projected_revenue,
            'projected_users': projection.projected_users,
            'projected_usage_minutes': projection.projected_usage_minutes,
            'confidence_level': projection.confidence_level,
            'model_accuracy': projection.model_accuracy,
            'monthly_average': projection.projected_revenue / months,
            'assumptions': projection.assumptions,
            'generated_at': projection.created_at.isoformat()
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/unit-economics")
async def get_unit_economics(
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Get unit economics analysis"""
    
    if end_date <= start_date:
        raise HTTPException(status_code=400, detail="End date must be after start date")
    
    analytics_service = BillingAnalyticsService(db)
    
    try:
        unit_economics = analytics_service.get_unit_economics_analysis(start_date, end_date)
        return unit_economics
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/provider-comparison")
async def get_provider_comparison(
    period_days: int = Query(30, ge=7, le=365),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Compare STT provider performance and costs"""
    
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)
    
    # Get provider metrics from recent analytics
    analytics = db.query(BillingAnalytics).filter(
        and_(
            BillingAnalytics.period_start >= start_date,
            BillingAnalytics.period_end <= end_date
        )
    ).all()
    
    # Aggregate provider metrics
    provider_aggregates = {}
    for a in analytics:
        for provider, metrics in a.provider_metrics.items():
            if provider not in provider_aggregates:
                provider_aggregates[provider] = {
                    'transcriptions': 0,
                    'minutes': 0,
                    'cost': 0.0,
                    'periods': 0
                }
            
            pa = provider_aggregates[provider]
            pa['transcriptions'] += metrics.get('transcriptions', 0)
            pa['minutes'] += metrics.get('minutes', 0)
            pa['cost'] += metrics.get('cost', 0)
            pa['periods'] += 1
    
    # Calculate comparison metrics
    comparison = {}
    total_transcriptions = sum(pa['transcriptions'] for pa in provider_aggregates.values())
    
    for provider, data in provider_aggregates.items():
        comparison[provider] = {
            'total_transcriptions': data['transcriptions'],
            'total_minutes': data['minutes'],
            'total_cost': data['cost'],
            'market_share_percent': (data['transcriptions'] / max(total_transcriptions, 1)) * 100,
            'cost_per_transcription': data['cost'] / max(data['transcriptions'], 1),
            'cost_per_minute': data['cost'] / max(data['minutes'], 1),
            'average_transcription_length': data['minutes'] / max(data['transcriptions'], 1)
        }
    
    # Cost efficiency ranking
    cost_ranking = sorted(
        comparison.items(),
        key=lambda x: x[1]['cost_per_minute']
    )
    
    return {
        'period': {
            'days': period_days,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat()
        },
        'provider_comparison': comparison,
        'cost_efficiency_ranking': [
            {
                'rank': idx + 1,
                'provider': provider,
                'cost_per_minute': data['cost_per_minute']
            }
            for idx, (provider, data) in enumerate(cost_ranking)
        ],
        'recommendations': [
            f"Most cost-effective provider: {cost_ranking[0][0]}" if cost_ranking else "No data available",
            f"Potential savings: ${(cost_ranking[-1][1]['cost_per_minute'] - cost_ranking[0][1]['cost_per_minute']) * sum(pa['minutes'] for pa in provider_aggregates.values()):.2f}" if len(cost_ranking) > 1 else "Single provider in use"
        ]
    }

@router.post("/generate-monthly-analytics")
async def generate_monthly_analytics(
    year: int = Query(..., ge=2025),
    month: int = Query(..., ge=1, le=12),
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """Generate monthly billing analytics (admin action)"""
    
    from calendar import monthrange
    
    start_date = datetime(year, month, 1)
    _, last_day = monthrange(year, month)
    end_date = datetime(year, month, last_day, 23, 59, 59)
    
    analytics_service = BillingAnalyticsService(db)
    
    # Check if analytics already exist
    existing = db.query(BillingAnalytics).filter(
        and_(
            BillingAnalytics.period_start == start_date,
            BillingAnalytics.period_type == 'monthly'
        )
    ).first()
    
    if existing:
        return {
            'message': 'Monthly analytics already exist',
            'analytics_id': str(existing.id),
            'revenue': existing.total_revenue
        }
    
    # Generate new analytics
    analytics = analytics_service.generate_period_analytics(
        period_start=start_date,
        period_end=end_date,
        period_type='monthly'
    )
    
    return {
        'message': 'Monthly analytics generated successfully',
        'analytics_id': str(analytics.id),
        'period': f"{year}-{month:02d}",
        'revenue': analytics.total_revenue,
        'users': analytics.active_users,
        'transcriptions': analytics.total_transcriptions
    }
```

## 🧪 Test Scenarios

### Analytics Service Tests
```python
def test_period_analytics_generation():
    """Test comprehensive billing analytics generation"""
    # Create test data
    user = create_test_user(db, plan=UserPlan.PRO)
    session = create_test_session(db, user.id)
    usage_log = create_usage_log(db, user.id, session.id, cost_usd=0.15, duration_minutes=30)
    
    # Generate analytics
    analytics_service = BillingAnalyticsService(db)
    start_date = datetime.utcnow() - timedelta(days=30)
    end_date = datetime.utcnow()
    
    analytics = analytics_service.generate_period_analytics(start_date, end_date, "monthly")
    
    assert analytics.total_revenue >= 0.15
    assert analytics.total_transcriptions >= 1
    assert analytics.active_users >= 1
    assert analytics.average_revenue_per_user > 0

def test_revenue_forecasting():
    """Test revenue forecasting with historical data"""
    # Create historical analytics data
    for i in range(6):
        date = datetime.utcnow() - timedelta(days=30 * i)
        analytics = create_billing_analytics(db, period_start=date, total_revenue=1000 + i * 100)
    
    analytics_service = BillingAnalyticsService(db)
    projection = analytics_service.generate_revenue_forecast(forecast_months=3)
    
    assert projection.projected_revenue > 0
    assert projection.confidence_level == 80.0
    assert projection.model_accuracy is not None
```

### API Integration Tests
```bash
# Test: Billing overview
curl -X GET "/api/v1/admin/billing-analytics/overview?period_days=30" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns comprehensive billing metrics

# Test: Revenue forecast
curl -X GET "/api/v1/admin/billing-analytics/revenue-forecast?months=6" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns revenue projection with confidence levels

# Test: Provider comparison
curl -X GET "/api/v1/admin/billing-analytics/provider-comparison" \
  -H "Authorization: Bearer $ADMIN_TOKEN"

# Expected: Returns STT provider cost and performance comparison
```

## 📊 Success Metrics

### Financial Intelligence
- **Revenue Tracking Accuracy**: 100% accurate revenue calculation and reporting
- **Cost Analysis Completeness**: Complete visibility into STT provider costs and margins
- **Forecasting Accuracy**: >85% accuracy in 6-month revenue projections
- **Unit Economics Insights**: Clear understanding of customer lifetime value and costs

### Business Impact
- **Pricing Optimization**: Data-driven pricing decisions improve margins by 15%
- **Cost Reduction**: Provider optimization reduces STT costs by 20%
- **Revenue Growth**: Better insights drive 25% improvement in revenue per user

## 📋 Definition of Done

- [ ] **Billing Analytics Models**: Comprehensive revenue and cost tracking models
- [ ] **Analytics Service**: Complete billing analytics generation and forecasting
- [ ] **Financial APIs**: Revenue, cost, and unit economics analysis endpoints
- [ ] **Forecasting Engine**: ML-based revenue forecasting with confidence intervals
- [ ] **Provider Comparison**: STT provider cost and performance analysis
- [ ] **Unit Economics**: Customer lifetime value and acquisition cost tracking
- [ ] **Automated Reporting**: Scheduled generation of monthly billing analytics
- [ ] **Unit Tests**: >85% coverage for billing analytics components
- [ ] **Integration Tests**: End-to-end financial reporting workflows
- [ ] **Documentation**: Finance team guide for billing analytics and reporting

## 🔄 Dependencies & Risks

### Dependencies
- ✅ US001 (Usage Analytics Foundation) - Required for usage data
- ✅ US004 (Smart Re-transcription Billing) - Required for accurate billing classification
- ⏳ Machine learning libraries for forecasting (scikit-learn, numpy)
- ⏳ Business intelligence dashboard for financial reporting

### Risks & Mitigations
- **Risk**: Financial data accuracy and compliance
  - **Mitigation**: Comprehensive testing, audit trails, financial controls
- **Risk**: Forecasting model accuracy and reliability
  - **Mitigation**: Multiple models, confidence intervals, regular validation
- **Risk**: Performance impact of complex analytics queries
  - **Mitigation**: Optimized queries, caching, background processing

## 📞 Stakeholders

**Product Owner**: Finance Team, Business Operations  
**Technical Lead**: Backend Engineering, Data Analytics  
**Reviewers**: CFO, Finance Controller, Business Intelligence Team  
**QA Focus**: Financial accuracy, Data integrity, Forecasting validation