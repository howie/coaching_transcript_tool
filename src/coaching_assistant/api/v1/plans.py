"""Plans management API endpoints."""

import logging
from typing import List, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.auth import get_current_user_dependency
from ...models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/plans", tags=["Plans"])


class PlanLimits(BaseModel):
    max_sessions: int
    max_transcriptions: int
    max_total_minutes: int
    max_file_size_mb: int


class PlanPricing(BaseModel):
    monthly_twd: int  # Amount in cents
    annual_twd: int   # Amount in cents
    monthly_usd: int  # Amount in cents
    annual_usd: int   # Amount in cents


class PlanResponse(BaseModel):
    id: str
    name: str
    display_name: str
    description: str
    pricing: PlanPricing
    features: List[str]
    limits: PlanLimits
    is_active: bool
    sort_order: int


class PlansListResponse(BaseModel):
    plans: List[PlanResponse]
    total: int


@router.get("", response_model=PlansListResponse)
async def get_available_plans(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get all available subscription plans."""
    
    try:
        # For now, return static plan data that matches database configuration
        # In production, this would fetch from a plans table in the database
        plans_data = [
            {
                "id": "FREE",
                "name": "FREE",
                "display_name": "免費版",
                "description": "開始您的教練旅程",
                "pricing": {
                    "monthly_twd": 0,
                    "annual_twd": 0,
                    "monthly_usd": 0,
                    "annual_usd": 0
                },
                "features": [
                    "每月 10 個會談記錄",
                    "每月 5 個轉錄",
                    "每月 200 分鐘轉錄額度",
                    "錄音檔最長 40 分鐘",
                    "最大檔案 60MB",
                    "基本匯出格式",
                    "Email 支援"
                ],
                "limits": {
                    "max_sessions": 10,
                    "max_transcriptions": 5,
                    "max_total_minutes": 200,
                    "max_file_size_mb": 60
                },
                "is_active": True,
                "sort_order": 1
            },
            {
                "id": "PRO",
                "name": "PRO",
                "display_name": "專業版",
                "description": "專業教練的最佳選擇",
                "pricing": {
                    "monthly_twd": 89900,  # NT$899.00
                    "annual_twd": 749900,  # NT$7499.00 (17% discount)
                    "monthly_usd": 2800,   # $28.00
                    "annual_usd": 25200    # $252.00
                },
                "features": [
                    "每月 25 個會談記錄",
                    "每月 50 個轉錄",
                    "每月 300 分鐘轉錄額度",
                    "錄音檔最長 90 分鐘",
                    "最大檔案 200MB",
                    "所有匯出格式",
                    "優先 Email 支援",
                    "進階分析報告",
                    "自訂品牌"
                ],
                "limits": {
                    "max_sessions": 25,
                    "max_transcriptions": 50,
                    "max_total_minutes": 300,
                    "max_file_size_mb": 200
                },
                "is_active": True,
                "sort_order": 2
            },
            {
                "id": "ENTERPRISE",
                "name": "ENTERPRISE",
                "display_name": "企業版",
                "description": "團隊與機構的企業解決方案",
                "pricing": {
                    "monthly_twd": 299900,  # NT$2999.00
                    "annual_twd": 2499900,  # NT$24999.00 (17% discount)
                    "monthly_usd": 9500,    # $95.00
                    "annual_usd": 85500     # $855.00
                },
                "features": [
                    "每月 500 個會談記錄",
                    "每月 1000 個轉錄",
                    "每月 1500 分鐘轉錄額度",
                    "錄音檔最長 4 小時",
                    "最大檔案 500MB",
                    "所有匯出格式",
                    "專屬客戶經理",
                    "24/7 電話支援",
                    "團隊協作功能",
                    "API 存取權限",
                    "自訂整合",
                    "SLA 服務保證"
                ],
                "limits": {
                    "max_sessions": 500,
                    "max_transcriptions": 1000,
                    "max_total_minutes": 1500,
                    "max_file_size_mb": 500
                },
                "is_active": True,
                "sort_order": 3
            }
        ]
        
        plans = [PlanResponse(**plan) for plan in plans_data]
        
        logger.info(f"Retrieved {len(plans)} plans for user {current_user.id}")
        
        return PlansListResponse(
            plans=plans,
            total=len(plans)
        )
        
    except Exception as e:
        logger.error(f"Failed to get available plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available plans."
        )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan_by_id(
    plan_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
):
    """Get specific plan by ID."""
    
    try:
        # Get all plans and find the requested one
        plans_response = await get_available_plans(current_user, db)
        
        for plan in plans_response.plans:
            if plan.id == plan_id.upper():
                return plan
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plan {plan_id} not found."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan information."
        )