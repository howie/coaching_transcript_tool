"""Plans management API endpoints."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...api.auth import get_current_user_dependency
from ...models import User
from ...services.plan_limits import get_global_plan_limits, PlanName

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/plans", tags=["Plans"])


class PlanLimits(BaseModel):
    max_total_minutes: int  # Only limit based on minutes
    max_file_size_mb: int


class PlanPricing(BaseModel):
    monthly_twd: int  # Amount in cents
    annual_twd: int  # Amount in cents
    monthly_usd: int  # Amount in cents
    annual_usd: int  # Amount in cents


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
    db: Session = Depends(get_db),
):
    """Get all available subscription plans."""

    try:
        # Generate plan data dynamically from PlanLimits service
        plans_data = []
        
        # Define plan metadata
        plan_metadata = {
            PlanName.FREE: {
                "id": "FREE",
                "name": "FREE", 
                "display_name": "免費試用方案",
                "description": "開始您的教練旅程",
                "features": [
                    "每月 200 分鐘轉錄額度",
                    "最大檔案 60MB",
                    "基本匯出格式",
                    "Email 支援",
                ],
                "sort_order": 1,
            },
            PlanName.STUDENT: {
                "id": "STUDENT",
                "name": "STUDENT",
                "display_name": "學習方案", 
                "description": "學生專屬優惠方案",
                "features": [
                    "每月 500 分鐘轉錄額度",
                    "最大檔案 100MB",
                    "所有匯出格式",
                    "Email 支援",
                    "6 個月資料保存",
                ],
                "sort_order": 2,
            },
            PlanName.PRO: {
                "id": "PRO",
                "name": "PRO",
                "display_name": "專業方案",
                "description": "專業教練的最佳選擇",
                "features": [
                    "每月 3000 分鐘轉錄額度",
                    "最大檔案 200MB",
                    "所有匯出格式",
                    "優先 Email 支援",
                    "進階分析報告",
                ],
                "sort_order": 3,
            },
        }
        
        # Generate plans dynamically using PlanLimits service
        plan_limits_service = get_global_plan_limits()
        
        for plan_name in [PlanName.FREE, PlanName.STUDENT, PlanName.PRO]:
            limits = plan_limits_service.get_plan_limit(plan_name)
            metadata = plan_metadata[plan_name]
            
            plan_data = {
                **metadata,
                "pricing": {
                    "monthly_twd": limits.monthly_price_twd,
                    "annual_twd": limits.annual_price_twd,
                    "monthly_usd": limits.monthly_price_usd,
                    "annual_usd": limits.annual_price_usd,
                },
                "limits": {
                    "max_total_minutes": limits.max_minutes,
                    "max_file_size_mb": limits.max_file_size_mb,
                },
                "is_active": True,
            }
            plans_data.append(plan_data)

        plans = [PlanResponse(**plan) for plan in plans_data]

        logger.info(f"Retrieved {len(plans)} plans for user {current_user.id}")

        return PlansListResponse(plans=plans, total=len(plans))

    except Exception as e:
        logger.error(f"Failed to get available plans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available plans.",
        )


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan_by_id(
    plan_id: str,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db),
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
            detail=f"Plan {plan_id} not found.",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get plan {plan_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve plan information.",
        )
