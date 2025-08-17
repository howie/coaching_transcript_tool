"""
Usage History Analytics API endpoints.

Provides historical usage data, trends, predictions, and insights for users.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..core.database import get_db
from ..models.user import User
from ..models.usage_history import UsageHistory
from ..services.usage_analytics_service import UsageAnalyticsService
from ..api.auth import get_current_user_dependency

logger = logging.getLogger(__name__)

router = APIRouter()


class UsageHistoryResponse(BaseModel):
    """Response model for usage history data."""
    id: str
    recorded_at: str
    period_type: str
    period_start: str
    period_end: str
    usage_metrics: Dict[str, Any]
    plan_context: Dict[str, Any]
    cost_metrics: Dict[str, Any]
    provider_breakdown: Dict[str, Any]
    export_activity: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: str
    updated_at: str


class UsageTrendResponse(BaseModel):
    """Response model for usage trend data."""
    date: str
    sessions: int
    minutes: float
    hours: float
    transcriptions: int
    exports: int
    cost: float
    utilization: float
    success_rate: float
    avg_duration: float


class UsagePredictionResponse(BaseModel):
    """Response model for usage predictions."""
    predicted_sessions: int
    predicted_minutes: int
    estimated_limit_date: Optional[str]
    confidence: float
    recommendation: str
    growth_rate: float
    current_trend: str


class UsageInsightResponse(BaseModel):
    """Response model for usage insights."""
    type: str  # "pattern", "optimization", "warning", "trend", "cost"
    title: str
    message: str
    suggestion: str
    priority: str  # "low", "medium", "high"
    action: Optional[str]  # "upgrade", "downgrade", "review", None


class UsageAnalyticsResponse(BaseModel):
    """Response model for comprehensive usage analytics."""
    current_period: Dict[str, Any]
    trends: List[UsageTrendResponse]
    predictions: UsagePredictionResponse
    insights: List[UsageInsightResponse]
    summary: Dict[str, Any]


@router.get("/")
async def usage_history_root():
    """Usage History API root endpoint."""
    return {"message": "Usage History Analytics API v1.0"}


@router.get("/history", response_model=List[UsageHistoryResponse])
async def get_usage_history(
    period: str = Query("30d", description="Time period: 7d, 30d, 3m, 12m, or custom"),
    from_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD) for custom period"),
    to_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD) for custom period"),
    period_type: str = Query("daily", description="Aggregation level: hourly, daily, monthly"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get historical usage data for the current user.
    
    Returns aggregated usage data for specified time period and granularity.
    """
    try:
        logger.info(f"📊 Getting usage history for user {current_user.id}, period: {period}")
        
        # Calculate date range
        if period == "custom" and from_date and to_date:
            start_date = datetime.fromisoformat(from_date)
            end_date = datetime.fromisoformat(to_date)
        else:
            # Parse standard periods
            end_date = datetime.utcnow()
            if period == "7d":
                start_date = end_date - timedelta(days=7)
            elif period == "30d":
                start_date = end_date - timedelta(days=30)
            elif period == "3m":
                start_date = end_date - timedelta(days=90)
            elif period == "12m":
                start_date = end_date - timedelta(days=365)
            else:
                start_date = end_date - timedelta(days=30)  # Default to 30 days
        
        # Query usage history
        history_query = db.query(UsageHistory).filter(
            UsageHistory.user_id == current_user.id,
            UsageHistory.period_type == period_type,
            UsageHistory.period_start >= start_date,
            UsageHistory.period_start <= end_date
        ).order_by(UsageHistory.period_start.desc())
        
        history_records = history_query.all()
        
        # Convert to response format
        response_data = []
        for record in history_records:
            record_dict = record.to_dict()
            response_data.append(UsageHistoryResponse(**record_dict))
        
        logger.info(f"✅ Retrieved {len(response_data)} usage history records for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting usage history for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage history"
        )


@router.get("/trends", response_model=List[UsageTrendResponse])
async def get_usage_trends(
    period: str = Query("30d", description="Time period: 7d, 30d, 3m, 12m"),
    group_by: str = Query("day", description="Grouping: day, week, month"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get usage trends and patterns over time.
    
    Returns trend data optimized for visualization and analysis.
    """
    try:
        logger.info(f"📈 Getting usage trends for user {current_user.id}")
        
        analytics_service = UsageAnalyticsService(db)
        trends_data = analytics_service.get_usage_trends(
            user_id=current_user.id,
            period=period,
            group_by=group_by
        )
        
        # Convert to response format
        response_data = [UsageTrendResponse(**trend) for trend in trends_data]
        
        logger.info(f"✅ Retrieved {len(response_data)} trend data points for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting usage trends for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve usage trends"
        )


@router.get("/predictions", response_model=UsagePredictionResponse)
async def get_usage_predictions(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get usage predictions based on historical patterns.
    
    Returns predicted usage for the next period and recommendations.
    """
    try:
        logger.info(f"🔮 Getting usage predictions for user {current_user.id}")
        
        analytics_service = UsageAnalyticsService(db)
        predictions = analytics_service.predict_usage(user_id=current_user.id)
        
        response_data = UsagePredictionResponse(**predictions)
        
        logger.info(f"✅ Generated usage predictions for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting usage predictions for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate usage predictions"
        )


@router.get("/insights", response_model=List[UsageInsightResponse])
async def get_usage_insights(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get personalized usage insights and recommendations.
    
    Returns actionable insights based on usage patterns and behavior.
    """
    try:
        logger.info(f"💡 Getting usage insights for user {current_user.id}")
        
        analytics_service = UsageAnalyticsService(db)
        insights = analytics_service.generate_insights(user_id=current_user.id)
        
        # Convert to response format
        response_data = [UsageInsightResponse(**insight) for insight in insights]
        
        logger.info(f"✅ Generated {len(response_data)} insights for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting usage insights for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate usage insights"
        )


@router.get("/analytics", response_model=UsageAnalyticsResponse)
async def get_comprehensive_analytics(
    period: str = Query("30d", description="Time period for analysis"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive usage analytics including trends, predictions, and insights.
    
    Returns a complete analytics package for dashboard display.
    """
    try:
        logger.info(f"📊 Getting comprehensive analytics for user {current_user.id}")
        
        analytics_service = UsageAnalyticsService(db)
        
        # Get all analytics data
        trends = analytics_service.get_usage_trends(current_user.id, period, "day")
        predictions = analytics_service.predict_usage(current_user.id)
        insights = analytics_service.generate_insights(current_user.id)
        
        # Calculate current period summary
        current_period = {
            "total_sessions": sum(t["sessions"] for t in trends[-7:]) if trends else 0,
            "total_minutes": sum(t["minutes"] for t in trends[-7:]) if trends else 0,
            "total_transcriptions": sum(t["transcriptions"] for t in trends[-7:]) if trends else 0,
            "avg_daily_usage": (sum(t["minutes"] for t in trends[-7:]) / 7) if trends else 0,
            "period_start": trends[-7]["date"] if len(trends) >= 7 else (trends[0]["date"] if trends else None),
            "period_end": trends[-1]["date"] if trends else None
        }
        
        # Calculate summary statistics
        summary = {
            "data_points": len(trends),
            "date_range": f"{trends[0]['date']} to {trends[-1]['date']}" if trends else "No data",
            "total_cost": sum(t["cost"] for t in trends),
            "avg_utilization": sum(t["utilization"] for t in trends) / len(trends) if trends else 0,
            "peak_usage_day": max(trends, key=lambda x: x["minutes"])["date"] if trends else None,
            "insights_count": len(insights),
            "prediction_confidence": predictions["confidence"]
        }
        
        response_data = UsageAnalyticsResponse(
            current_period=current_period,
            trends=[UsageTrendResponse(**t) for t in trends],
            predictions=UsagePredictionResponse(**predictions),
            insights=[UsageInsightResponse(**i) for i in insights],
            summary=summary
        )
        
        logger.info(f"✅ Generated comprehensive analytics for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error getting comprehensive analytics for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comprehensive analytics"
        )


@router.post("/snapshot")
async def create_usage_snapshot(
    period_type: str = Query("daily", description="Snapshot type: hourly, daily, monthly"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Create a usage snapshot for the current period.
    
    Manually trigger usage data aggregation (normally done automatically).
    """
    try:
        logger.info(f"📸 Creating usage snapshot for user {current_user.id}")
        
        analytics_service = UsageAnalyticsService(db)
        snapshot = analytics_service.record_usage_snapshot(
            user_id=current_user.id,
            period_type=period_type
        )
        
        response_data = UsageHistoryResponse(**snapshot.to_dict())
        
        logger.info(f"✅ Created usage snapshot for user {current_user.id}")
        return response_data
        
    except Exception as e:
        logger.error(f"❌ Error creating usage snapshot for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create usage snapshot"
        )


@router.get("/export")
async def export_usage_data(
    format: str = Query("csv", description="Export format: csv, json, pdf"),
    period: str = Query("30d", description="Time period to export"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """
    Export usage data in specified format.
    
    Returns downloadable usage data for external analysis.
    """
    try:
        logger.info(f"📤 Exporting usage data for user {current_user.id}, format: {format}")
        
        analytics_service = UsageAnalyticsService(db)
        trends = analytics_service.get_usage_trends(current_user.id, period, "day")
        
        if format.lower() == "csv":
            # TODO: Implement CSV export
            return {"message": "CSV export not yet implemented", "data": trends}
        elif format.lower() == "json":
            return {"format": "json", "period": period, "data": trends}
        elif format.lower() == "pdf":
            # TODO: Implement PDF export
            return {"message": "PDF export not yet implemented", "data": trends}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported export format. Use csv, json, or pdf."
            )
        
    except Exception as e:
        logger.error(f"❌ Error exporting usage data for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export usage data"
        )