# US002: Plan Tiers Implementation

## 📋 User Story

**As a** platform user and business stakeholder  
**I want** clearly defined plan tiers with specific limits and features  
**So that** users can choose the right plan for their needs and the business can scale revenue

## 💼 Business Value

### Current Problem
- All users have the same unlimited access regardless of value provided
- No revenue differentiation based on usage or feature needs
- Cannot scale business model or optimize for different user segments
- No clear upgrade path for growing users

### Business Impact
- **Revenue Loss**: Missing ~$50K-100K/month from plan differentiation
- **Resource Waste**: Heavy users consuming resources without appropriate compensation
- **Market Positioning**: Cannot compete with tiered SaaS offerings
- **User Confusion**: No clear value proposition for different user needs

### Value Delivered
- **Revenue Generation**: Clear pricing tiers drive subscription revenue
- **User Segmentation**: Different plans serve different user needs optimally
- **Resource Optimization**: Usage-based pricing ensures sustainable economics
- **Market Competitiveness**: Standard SaaS model with clear upgrade path

## 🎯 Acceptance Criteria

### Plan Configuration System
1. **Dynamic Plan Configuration**
   - [ ] Plan limits stored in database (not hardcoded)
   - [ ] Admin interface to modify plan features and limits
   - [ ] Plan versioning for grandfathering existing users
   - [ ] A/B testing support for plan configurations

2. **Free Tier Implementation**
   - [ ] 10 sessions per month limit
   - [ ] 120 minutes total audio per month
   - [ ] 20 transcript exports per month
   - [ ] 50MB max file size per upload
   - [ ] JSON and TXT export formats only
   - [ ] 1 concurrent transcription processing
   - [ ] 30-day data retention

3. **Pro Tier Implementation**
   - [ ] 100 sessions per month limit
   - [ ] 1,200 minutes (20 hours) total audio per month
   - [ ] 200 transcript exports per month
   - [ ] 200MB max file size per upload
   - [ ] All export formats: JSON, TXT, VTT, SRT
   - [ ] 3 concurrent transcription processing
   - [ ] Priority email support
   - [ ] 1-year data retention

4. **Business Tier Implementation**
   - [ ] Unlimited sessions per month
   - [ ] Unlimited total audio minutes per month
   - [ ] Unlimited transcript exports per month
   - [ ] 500MB max file size per upload
   - [ ] All export formats including XLSX
   - [ ] 10 concurrent transcription processing
   - [ ] Priority support with SLA
   - [ ] Permanent data retention

### Plan Management
5. **User Plan Assignment**
   - [ ] New users automatically assigned Free tier
   - [ ] Plan information displayed in user dashboard
   - [ ] Plan limits clearly communicated to users
   - [ ] Grace period handling for plan changes

6. **Plan Validation Integration**
   - [ ] Real-time validation before resource-intensive operations
   - [ ] Clear error messages with upgrade suggestions
   - [ ] Soft limits with upgrade prompts (not hard blocks)
   - [ ] Usage warnings at 80% of limits

## 🏗️ Technical Implementation

### Plan Configuration Database
```sql
-- Flexible plan configuration system
CREATE TABLE plan_configurations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Plan Identity
    plan_name VARCHAR(20) UNIQUE NOT NULL CHECK (plan_name IN ('free', 'pro', 'business')),
    display_name VARCHAR(50) NOT NULL,
    description TEXT,
    tagline VARCHAR(100),
    
    -- Usage Limits (-1 = unlimited)
    max_sessions INTEGER NOT NULL CHECK (max_sessions = -1 OR max_sessions > 0),
    max_total_minutes INTEGER NOT NULL CHECK (max_total_minutes = -1 OR max_total_minutes > 0),
    max_transcription_count INTEGER NOT NULL CHECK (max_transcription_count = -1 OR max_transcription_count > 0),
    max_file_size_mb INTEGER NOT NULL CHECK (max_file_size_mb > 0),
    
    -- Feature Configuration
    export_formats JSONB NOT NULL DEFAULT '["json", "txt"]',
    priority_support BOOLEAN DEFAULT false NOT NULL,
    concurrent_processing INTEGER DEFAULT 1 NOT NULL CHECK (concurrent_processing > 0),
    
    -- Data Management
    retention_days INTEGER NOT NULL CHECK (retention_days = -1 OR retention_days > 0),
    
    -- Pricing (for display purposes)
    monthly_price_usd DECIMAL(10,2) DEFAULT 0 NOT NULL CHECK (monthly_price_usd >= 0),
    annual_price_usd DECIMAL(10,2) DEFAULT 0 NOT NULL CHECK (annual_price_usd >= 0),
    annual_discount_percentage DECIMAL(5,2) DEFAULT 0 CHECK (annual_discount_percentage >= 0 AND annual_discount_percentage <= 100),
    
    -- Stripe Integration
    stripe_monthly_price_id VARCHAR(100),
    stripe_annual_price_id VARCHAR(100),
    
    -- Display Configuration
    is_active BOOLEAN DEFAULT true NOT NULL,
    is_popular BOOLEAN DEFAULT false NOT NULL,
    sort_order INTEGER DEFAULT 0 NOT NULL,
    color_scheme VARCHAR(20) DEFAULT 'blue',
    
    -- Feature Flags
    feature_flags JSONB DEFAULT '{}',
    
    -- System Fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    version INTEGER DEFAULT 1 NOT NULL
);

-- Insert default plan configurations
INSERT INTO plan_configurations (
    plan_name, display_name, description, tagline,
    max_sessions, max_total_minutes, max_transcription_count, max_file_size_mb,
    export_formats, priority_support, concurrent_processing, retention_days,
    monthly_price_usd, annual_price_usd, annual_discount_percentage,
    is_popular, sort_order, color_scheme
) VALUES 
    ('free', 'Free Trial', 'Perfect for trying out the platform', 'Get started for free',
     10, 120, 20, 50,
     '["json", "txt"]', false, 1, 30,
     0.00, 0.00, 0,
     false, 1, 'gray'),
    ('pro', 'Pro Plan', 'For professional coaches', 'Most popular choice',
     100, 1200, 200, 200,
     '["json", "txt", "vtt", "srt"]', true, 3, 365,
     29.99, 299.90, 17,
     true, 2, 'blue'),
    ('business', 'Business Plan', 'For coaching organizations', 'Scale your team',
     -1, -1, -1, 500,
     '["json", "txt", "vtt", "srt", "xlsx"]', true, 10, -1,
     99.99, 999.90, 17,
     false, 3, 'purple');
```

### Plan Limits Service
```python
# packages/core-logic/src/coaching_assistant/services/plan_service.py

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from ..models.plan_configuration import PlanConfiguration
from ..models.user import User, UserPlan

class PlanService:
    """Service for plan management and configuration."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_plan_configuration(self, plan: UserPlan) -> Dict[str, Any]:
        """Get configuration for specific plan."""
        
        config = self.db.query(PlanConfiguration).filter(
            and_(
                PlanConfiguration.plan_name == plan.value,
                PlanConfiguration.is_active == True
            )
        ).first()
        
        if not config:
            # Fallback to default Free plan limits
            return self._get_default_free_plan()
        
        return {
            "plan_name": config.plan_name,
            "display_name": config.display_name,
            "description": config.description,
            "limits": {
                "max_sessions": config.max_sessions,
                "max_total_minutes": config.max_total_minutes,
                "max_transcription_count": config.max_transcription_count,
                "max_file_size_mb": config.max_file_size_mb,
                "export_formats": config.export_formats,
                "concurrent_processing": config.concurrent_processing,
                "retention_days": config.retention_days
            },
            "features": {
                "priority_support": config.priority_support,
                "export_formats": config.export_formats,
                "concurrent_processing": config.concurrent_processing
            },
            "pricing": {
                "monthly_usd": float(config.monthly_price_usd),
                "annual_usd": float(config.annual_price_usd),
                "annual_discount_percentage": float(config.annual_discount_percentage)
            },
            "display": {
                "is_popular": config.is_popular,
                "color_scheme": config.color_scheme,
                "tagline": config.tagline
            }
        }
    
    def get_all_active_plans(self) -> List[Dict[str, Any]]:
        """Get all active plan configurations."""
        
        configs = self.db.query(PlanConfiguration).filter(
            PlanConfiguration.is_active == True
        ).order_by(PlanConfiguration.sort_order).all()
        
        return [
            {
                "plan_name": config.plan_name,
                "display_name": config.display_name,
                "description": config.description,
                "tagline": config.tagline,
                "limits": {
                    "max_sessions": "unlimited" if config.max_sessions == -1 else config.max_sessions,
                    "max_total_minutes": "unlimited" if config.max_total_minutes == -1 else config.max_total_minutes,
                    "max_transcription_count": "unlimited" if config.max_transcription_count == -1 else config.max_transcription_count,
                    "max_file_size_mb": config.max_file_size_mb,
                    "retention_days": "permanent" if config.retention_days == -1 else config.retention_days
                },
                "features": {
                    "export_formats": config.export_formats,
                    "priority_support": config.priority_support,
                    "concurrent_processing": config.concurrent_processing
                },
                "pricing": {
                    "monthly_usd": float(config.monthly_price_usd),
                    "annual_usd": float(config.annual_price_usd),
                    "annual_discount_percentage": float(config.annual_discount_percentage),
                    "annual_savings_usd": float(config.monthly_price_usd * 12 - config.annual_price_usd)
                },
                "display": {
                    "is_popular": config.is_popular,
                    "color_scheme": config.color_scheme,
                    "sort_order": config.sort_order
                },
                "stripe": {
                    "monthly_price_id": config.stripe_monthly_price_id,
                    "annual_price_id": config.stripe_annual_price_id
                }
            }
            for config in configs
        ]
    
    def validate_plan_limits(self, user: User, action: str, **kwargs) -> Dict[str, Any]:
        """Validate if user can perform action within plan limits."""
        
        plan_config = self.get_plan_configuration(user.plan)
        limits = plan_config["limits"]
        
        validation_result = {
            "allowed": True,
            "message": "Action permitted",
            "limit_info": None,
            "upgrade_suggestion": None
        }
        
        if action == "create_session":
            if limits["max_sessions"] != -1 and user.session_count >= limits["max_sessions"]:
                validation_result.update({
                    "allowed": False,
                    "message": f"Session limit exceeded ({limits['max_sessions']} sessions per month)",
                    "limit_info": {
                        "type": "max_sessions",
                        "current": user.session_count,
                        "limit": limits["max_sessions"]
                    },
                    "upgrade_suggestion": self._get_upgrade_suggestion(user.plan)
                })
        
        elif action == "upload_file":
            file_size_mb = kwargs.get("file_size_mb", 0)
            if file_size_mb > limits["max_file_size_mb"]:
                validation_result.update({
                    "allowed": False,
                    "message": f"File size exceeds limit ({limits['max_file_size_mb']}MB)",
                    "limit_info": {
                        "type": "max_file_size_mb",
                        "current": file_size_mb,
                        "limit": limits["max_file_size_mb"]
                    },
                    "upgrade_suggestion": self._get_upgrade_suggestion(user.plan)
                })
        
        elif action == "export_transcript":
            export_format = kwargs.get("format", "").lower()
            if export_format not in limits["export_formats"]:
                validation_result.update({
                    "allowed": False,
                    "message": f"Export format '{export_format}' not available on {user.plan.value} plan",
                    "limit_info": {
                        "type": "export_formats",
                        "requested": export_format,
                        "available": limits["export_formats"]
                    },
                    "upgrade_suggestion": self._get_upgrade_suggestion(user.plan)
                })
        
        elif action == "transcribe":
            if limits["max_transcription_count"] != -1 and user.transcription_count >= limits["max_transcription_count"]:
                validation_result.update({
                    "allowed": False,
                    "message": f"Transcription limit exceeded ({limits['max_transcription_count']} transcriptions per month)",
                    "limit_info": {
                        "type": "max_transcription_count",
                        "current": user.transcription_count,
                        "limit": limits["max_transcription_count"]
                    },
                    "upgrade_suggestion": self._get_upgrade_suggestion(user.plan)
                })
        
        return validation_result
    
    def get_usage_status(self, user: User) -> Dict[str, Any]:
        """Get detailed usage status against plan limits."""
        
        plan_config = self.get_plan_configuration(user.plan)
        limits = plan_config["limits"]
        
        def calculate_percentage(current: int, limit: int) -> Optional[float]:
            if limit == -1:  # Unlimited
                return None
            return (current / limit * 100) if limit > 0 else 0
        
        def is_approaching_limit(current: int, limit: int, threshold: float = 80.0) -> bool:
            if limit == -1:  # Unlimited
                return False
            return (current / limit * 100) >= threshold if limit > 0 else False
        
        usage_status = {
            "user_id": str(user.id),
            "plan": user.plan.value,
            "plan_display_name": plan_config["display_name"],
            "current_usage": {
                "sessions": user.session_count,
                "minutes": user.usage_minutes,
                "transcriptions": user.transcription_count
            },
            "plan_limits": {
                "sessions": "unlimited" if limits["max_sessions"] == -1 else limits["max_sessions"],
                "minutes": "unlimited" if limits["max_total_minutes"] == -1 else limits["max_total_minutes"],
                "transcriptions": "unlimited" if limits["max_transcription_count"] == -1 else limits["max_transcription_count"],
                "file_size_mb": limits["max_file_size_mb"],
                "export_formats": limits["export_formats"]
            },
            "usage_percentages": {
                "sessions": calculate_percentage(user.session_count, limits["max_sessions"]),
                "minutes": calculate_percentage(user.usage_minutes, limits["max_total_minutes"]),
                "transcriptions": calculate_percentage(user.transcription_count, limits["max_transcription_count"])
            },
            "approaching_limits": {
                "sessions": is_approaching_limit(user.session_count, limits["max_sessions"]),
                "minutes": is_approaching_limit(user.usage_minutes, limits["max_total_minutes"]),
                "transcriptions": is_approaching_limit(user.transcription_count, limits["max_transcription_count"])
            },
            "next_reset": user.current_month_start.replace(month=user.current_month_start.month + 1) if user.current_month_start else None
        }
        
        # Add upgrade suggestions if approaching limits
        approaching_any = any(usage_status["approaching_limits"].values())
        if approaching_any:
            usage_status["upgrade_suggestion"] = self._get_upgrade_suggestion(user.plan)
        
        return usage_status
    
    def _get_upgrade_suggestion(self, current_plan: UserPlan) -> Optional[Dict[str, Any]]:
        """Get upgrade suggestion for current plan."""
        
        upgrade_path = {
            UserPlan.FREE: UserPlan.PRO,
            UserPlan.PRO: UserPlan.BUSINESS,
            UserPlan.BUSINESS: None
        }
        
        suggested_plan = upgrade_path.get(current_plan)
        if not suggested_plan:
            return None
        
        suggested_config = self.get_plan_configuration(suggested_plan)
        
        return {
            "suggested_plan": suggested_plan.value,
            "display_name": suggested_config["display_name"],
            "key_benefits": self._get_upgrade_benefits(current_plan, suggested_plan),
            "pricing": suggested_config["pricing"],
            "tagline": suggested_config["display"].get("tagline")
        }
    
    def _get_upgrade_benefits(self, current: UserPlan, suggested: UserPlan) -> List[str]:
        """Get key benefits of upgrading to suggested plan."""
        
        benefits = {
            (UserPlan.FREE, UserPlan.PRO): [
                "10x more sessions (100 vs 10)",
                "10x more audio time (20 hours vs 2 hours)",
                "All export formats (VTT, SRT)",
                "Priority support",
                "1 year data retention"
            ],
            (UserPlan.PRO, UserPlan.BUSINESS): [
                "Unlimited sessions and audio",
                "Advanced export formats (XLSX)",
                "10 concurrent processing slots",
                "Permanent data retention",
                "Premium support with SLA"
            ]
        }
        
        return benefits.get((current, suggested), [])
    
    def _get_default_free_plan(self) -> Dict[str, Any]:
        """Fallback free plan configuration."""
        return {
            "plan_name": "free",
            "display_name": "Free Trial",
            "description": "Basic plan with essential features",
            "limits": {
                "max_sessions": 10,
                "max_total_minutes": 120,
                "max_transcription_count": 20,
                "max_file_size_mb": 50,
                "export_formats": ["json", "txt"],
                "concurrent_processing": 1,
                "retention_days": 30
            },
            "features": {
                "priority_support": False,
                "export_formats": ["json", "txt"],
                "concurrent_processing": 1
            },
            "pricing": {
                "monthly_usd": 0.0,
                "annual_usd": 0.0,
                "annual_discount_percentage": 0.0
            },
            "display": {
                "is_popular": False,
                "color_scheme": "gray",
                "tagline": "Get started for free"
            }
        }
```

### API Implementation
```python
# packages/core-logic/src/coaching_assistant/api/plans.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..dependencies import get_db, get_current_user_dependency
from ..models.user import User
from ..services.plan_service import PlanService

router = APIRouter(prefix="/plans", tags=["plans"])

@router.get("/")
async def get_available_plans(
    db: Session = Depends(get_db)
) -> Dict[str, List[Dict[str, Any]]]:
    """Get all available billing plans with features and pricing."""
    
    plan_service = PlanService(db)
    plans = plan_service.get_all_active_plans()
    
    return {
        "plans": plans,
        "currency": "USD",
        "billing_cycles": ["monthly", "annual"],
        "features_comparison": {
            "sessions": "Number of coaching sessions you can upload per month",
            "audio_minutes": "Total minutes of audio you can transcribe per month",
            "transcription_exports": "Number of transcript exports per month",
            "file_size": "Maximum size per audio file upload",
            "export_formats": "Available transcript export formats",
            "concurrent_processing": "Number of files you can transcribe simultaneously",
            "priority_support": "Priority email support with faster response times",
            "data_retention": "How long your data is stored on our platform"
        }
    }

@router.get("/current")
async def get_current_plan(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get current user's plan details and usage status."""
    
    plan_service = PlanService(db)
    plan_config = plan_service.get_plan_configuration(current_user.plan)
    usage_status = plan_service.get_usage_status(current_user)
    
    return {
        "current_plan": plan_config,
        "usage_status": usage_status,
        "subscription_info": {
            "start_date": current_user.subscription_start_date.isoformat() if current_user.subscription_start_date else None,
            "end_date": current_user.subscription_end_date.isoformat() if current_user.subscription_end_date else None,
            "active": current_user.subscription_active,
            "stripe_subscription_id": current_user.subscription_stripe_id
        }
    }

@router.get("/compare")
async def compare_plans(
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Get plan comparison focused on upgrade paths."""
    
    plan_service = PlanService(db)
    all_plans = plan_service.get_all_active_plans()
    current_plan_config = plan_service.get_plan_configuration(current_user.plan)
    
    # Highlight differences from current plan
    for plan in all_plans:
        if plan["plan_name"] == current_user.plan.value:
            plan["is_current"] = True
        else:
            plan["is_current"] = False
            # Add comparison highlights
            plan["improvements_over_current"] = plan_service._get_upgrade_benefits(
                current_user.plan,
                UserPlan(plan["plan_name"])
            )
    
    return {
        "current_plan": current_user.plan.value,
        "plans": all_plans,
        "recommended_upgrade": plan_service._get_upgrade_suggestion(current_user.plan)
    }
```

## 🧪 Test Scenarios

### Unit Tests
```python
def test_plan_configuration_loading():
    """Test plan configurations are loaded correctly from database"""
    plan_service = PlanService(db)
    
    free_config = plan_service.get_plan_configuration(UserPlan.FREE)
    assert free_config["limits"]["max_sessions"] == 10
    assert free_config["limits"]["max_total_minutes"] == 120
    assert "json" in free_config["limits"]["export_formats"]
    assert "xlsx" not in free_config["limits"]["export_formats"]
    
    business_config = plan_service.get_plan_configuration(UserPlan.BUSINESS)
    assert business_config["limits"]["max_sessions"] == -1  # Unlimited
    assert business_config["features"]["priority_support"] == True

def test_plan_limit_validation():
    """Test plan limit validation works correctly"""
    user = create_test_user(plan=UserPlan.FREE)
    user.session_count = 10  # At limit
    
    plan_service = PlanService(db)
    
    # Should fail validation
    result = plan_service.validate_plan_limits(user, "create_session")
    assert result["allowed"] == False
    assert "session limit" in result["message"].lower()
    assert result["upgrade_suggestion"]["suggested_plan"] == "pro"
    
    # File size validation
    result = plan_service.validate_plan_limits(user, "upload_file", file_size_mb=60)
    assert result["allowed"] == False
    assert result["limit_info"]["limit"] == 50

def test_usage_status_calculation():
    """Test usage status and percentage calculations"""
    user = create_test_user(plan=UserPlan.FREE)
    user.session_count = 8  # 80% of limit
    user.usage_minutes = 100  # ~83% of limit
    
    plan_service = PlanService(db)
    status = plan_service.get_usage_status(user)
    
    assert status["usage_percentages"]["sessions"] == 80.0
    assert status["usage_percentages"]["minutes"] == pytest.approx(83.33, rel=1e-2)
    assert status["approaching_limits"]["sessions"] == True
    assert status["approaching_limits"]["minutes"] == True
    assert status["upgrade_suggestion"] is not None

def test_unlimited_plan_handling():
    """Test unlimited plans handle limits correctly"""
    user = create_test_user(plan=UserPlan.BUSINESS)
    user.session_count = 1000  # Large number
    
    plan_service = PlanService(db)
    
    # Should always allow for unlimited plan
    result = plan_service.validate_plan_limits(user, "create_session")
    assert result["allowed"] == True
    
    status = plan_service.get_usage_status(user)
    assert status["usage_percentages"]["sessions"] is None  # Unlimited
    assert status["approaching_limits"]["sessions"] == False
```

### Integration Tests
```python
def test_plan_api_endpoints():
    """Test plan API endpoints return correct data"""
    # Test getting available plans
    response = client.get("/api/plans/")
    assert response.status_code == 200
    plans_data = response.json()
    
    assert len(plans_data["plans"]) == 3  # free, pro, business
    assert plans_data["currency"] == "USD"
    
    # Verify plan structure
    free_plan = next(p for p in plans_data["plans"] if p["plan_name"] == "free")
    assert free_plan["limits"]["max_sessions"] == 10
    assert free_plan["pricing"]["monthly_usd"] == 0.0
    
    pro_plan = next(p for p in plans_data["plans"] if p["plan_name"] == "pro")
    assert pro_plan["display"]["is_popular"] == True
    assert pro_plan["pricing"]["monthly_usd"] > 0

def test_current_plan_endpoint():
    """Test current plan endpoint with authenticated user"""
    user = create_test_user(plan=UserPlan.PRO)
    user.session_count = 25
    
    with authenticate_as(user):
        response = client.get("/api/v1/plans/current")
        assert response.status_code == 200
        
        data = response.json()
        assert data["current_plan"]["plan_name"] == "pro"
        assert data["usage_status"]["current_usage"]["sessions"] == 25
        assert data["usage_status"]["plan_limits"]["sessions"] == 100
```

## 📊 Success Metrics

### Business Metrics
- **Plan Adoption**: >60% of active users on paid plans within 6 months
- **Revenue Per User**: Average revenue increases by 300% from plan introduction
- **Conversion Rate**: >15% free-to-paid conversion rate
- **Upgrade Rate**: >25% of users upgrade within first 3 months

### Technical Metrics
- **Plan Validation Performance**: <50ms response time for limit checks
- **Configuration Flexibility**: 100% of plan changes deployable without code changes
- **API Response Time**: <200ms for plan comparison endpoints
- **Data Consistency**: 100% accuracy in plan limit enforcement

### User Experience Metrics
- **Limit Clarity**: >90% user satisfaction with plan limit communication
- **Upgrade Flow**: >80% completion rate for initiated upgrades
- **Support Reduction**: 50% reduction in plan-related support tickets

## 📋 Definition of Done

- [ ] **Plan Configuration System**: Database-driven plan management
- [ ] **Three-Tier Structure**: Free, Pro, Business plans with distinct limits
- [ ] **Dynamic Validation**: Real-time plan limit checking
- [ ] **User Plan Assignment**: Automatic Free tier assignment for new users
- [ ] **API Endpoints**: Complete plan information and comparison APIs
- [ ] **Usage Status**: Detailed usage tracking against plan limits
- [ ] **Upgrade Suggestions**: Intelligent upgrade recommendations
- [ ] **Admin Interface**: Plan configuration management (future story)
- [ ] **Stripe Integration**: Payment processing setup for paid plans
- [ ] **Data Migration**: Existing users assigned appropriate plans
- [ ] **Unit Tests**: >90% coverage for plan validation logic
- [ ] **Integration Tests**: End-to-end plan enforcement testing
- [ ] **Performance Tests**: Plan validation performance benchmarks
- [ ] **Documentation**: Complete plan feature documentation

## 🔄 Dependencies & Risks

### Dependencies
- ✅ User authentication system
- ✅ Database migration framework  
- ⏳ Payment processing integration (Stripe)
- ⏳ Usage tracking system (US001)
- ⏳ Admin interface for plan management

### Risks & Mitigations
- **Risk**: Existing users confused by new plan limitations
  - **Mitigation**: Grandfathering strategy, clear communication, gradual rollout
- **Risk**: Plan limits too restrictive, high churn
  - **Mitigation**: A/B testing, usage analytics, flexible adjustment capability
- **Risk**: Performance impact of real-time limit checking
  - **Mitigation**: Caching, optimized queries, async validation where possible

## 📞 Stakeholders

**Product Owner**: Business Strategy Team, Revenue Operations  
**Technical Lead**: Backend Engineering, Payment Systems  
**Reviewers**: Finance (Pricing), Marketing (Positioning), UX (User Communication)  
**QA Focus**: Plan enforcement accuracy, Performance, User experience