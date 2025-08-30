# US-SUB-004: Plan Upgrades & Pricing

## 📋 User Story
**As a** Taiwan coaching professional  
**I want** to see clear pricing in TWD and easily upgrade my plan  
**So that** I can access enhanced features with transparent Taiwan pricing

## 🎯 Epic
SaaS Subscription Enhancement

## 📊 Story Details
- **Story ID**: US-SUB-004
- **Priority**: P1 (High)
- **Story Points**: 5
- **Sprint**: Week 2 (Days 9-10)

## 📋 Dependencies
- **Depends On**: 
  - US-SUB-001 (Credit Card Authorization) - Subscription foundation
  - US-SUB-002 (Subscription Management) - Upgrade functionality
- **Blocks**: None (Enhancement story)

## ✅ Acceptance Criteria
- [ ] Taiwan-optimized pricing display in TWD
- [ ] Clear monthly vs annual pricing comparison
- [ ] Annual discount prominently displayed (2 months free)
- [ ] Plan comparison table with feature differences
- [ ] Upgrade path guidance for current plan users
- [ ] One-click upgrade with prorated billing
- [ ] Traditional Chinese pricing terminology
- [ ] Mobile-responsive pricing display
- [ ] Competitive pricing vs international alternatives
- [ ] Clear value proposition for Taiwan market

## 🏗️ Technical Implementation

### Backend Tasks
- [ ] Taiwan pricing configuration
- [ ] Plan comparison API endpoint
- [ ] Upgrade recommendation logic
- [ ] Pricing calculation utilities
- [ ] Currency formatting for TWD

### Frontend Tasks
- [ ] Taiwan pricing table component
- [ ] Plan comparison interface
- [ ] Upgrade recommendation UI
- [ ] Annual savings calculator
- [ ] Mobile-optimized pricing display

### Taiwan Market Pricing Strategy
```python
# src/coaching_assistant/core/config/taiwan_pricing.py
from typing import Dict, Any

class TaiwanPricingConfig:
    """台灣市場定價配置"""
    
    # 基於市場研究的台灣定價策略
    TAIWAN_PLANS = {
        "FREE": {
            "price_monthly_twd": 0,
            "price_annual_twd": 0,
            "display_name": "免費方案",
            "subtitle": "適合初學者探索",
            "target_audience": "新手教練",
            "features": [
                "60MB 檔案大小上限",
                "基本語音轉文字",
                "3個會談記錄保存",
                "中文轉錄支援",
                "基本匯出功能"
            ],
            "limitations": [
                "檔案大小限制",
                "會談記錄有限",
                "無角色識別",
                "無進階分析"
            ],
            "popular": False
        },
        
        "PRO": {
            "price_monthly_twd": 89900,  # NT$899/月
            "price_annual_twd": 899900,  # NT$8,999/年 (省 NT$1,789)
            "display_name": "專業方案",
            "subtitle": "執業教練的最佳選擇",
            "target_audience": "專業教練",
            "features": [
                "200MB 檔案大小上限",
                "高品質語音轉文字",
                "無限會談記錄保存",
                "智能角色識別",
                "詳細會談分析報告",
                "多種匯出格式",
                "優先客服支援",
                "進階搜尋功能"
            ],
            "upgrade_benefits": [
                "檔案大小提升 233% (60MB→200MB)",
                "無限會談記錄儲存",
                "角色識別功能解鎖",
                "專業分析報告"
            ],
            "popular": True,
            "savings_annual": 178900,  # 年繳省 2 個月
            "monthly_equivalent_annual": 74992  # 年繳平均每月 NT$750
        },
        
        "ENTERPRISE": {
            "price_monthly_twd": 299900,  # NT$2,999/月
            "price_annual_twd": 2999900,  # NT$29,999/年 (省 NT$5,989)
            "display_name": "企業方案",
            "subtitle": "教練機構和團隊",
            "target_audience": "教練機構",
            "features": [
                "500MB 檔案大小上限",
                "企業級語音轉文字",
                "無限會談記錄保存",
                "多用戶團隊管理",
                "進階分析儀表板",
                "API 整合支援",
                "白標客製化",
                "專屬客戶經理",
                "24/7 技術支援",
                "法規遵循報告"
            ],
            "enterprise_features": [
                "團隊協作工具",
                "企業級資安",
                "客製化整合",
                "專屬技術支援"
            ],
            "popular": False,
            "savings_annual": 598900,  # 年繳省 2 個月
            "monthly_equivalent_annual": 249992  # 年繳平均每月 NT$2,500
        }
    }
    
    # 市場競爭分析
    COMPETITOR_COMPARISON = {
        "otter_ai": {
            "name": "Otter.ai",
            "price_usd": 16.99,
            "price_twd_equivalent": 51000,  # 約 NT$510 (假設匯率30)
            "features": ["基本轉錄", "有限儲存", "英文優化"],
            "limitations": ["中文支援有限", "無教練專業功能"]
        },
        "rev_ai": {
            "name": "Rev.ai",
            "price_usd": 22.00,
            "price_twd_equivalent": 66000,  # 約 NT$660
            "features": ["商業轉錄", "API 支援"],
            "limitations": ["無中文優化", "無教練專業分析"]
        },
        "local_competitors": {
            "name": "本土競爭者平均",
            "price_twd_range": [30000, 80000],  # NT$300-800
            "limitations": ["功能有限", "語音品質較差", "無持續更新"]
        }
    }
    
    # 價值主張
    VALUE_PROPOSITIONS = {
        "coaching_specific": "專為教練設計的轉錄和分析功能",
        "chinese_optimized": "完整繁體中文語音辨識優化",
        "taiwan_support": "台灣在地客服和技術支援",
        "gdpr_compliance": "符合台灣個資法規範",
        "competitive_pricing": "比國際工具更具競爭力的定價"
    }

    @classmethod
    def get_plan_pricing(cls, plan_id: str) -> Dict[str, Any]:
        """取得方案定價資訊"""
        return cls.TAIWAN_PLANS.get(plan_id, {})
    
    @classmethod
    def calculate_annual_savings(cls, plan_id: str) -> Dict[str, int]:
        """計算年繳節省金額"""
        plan = cls.TAIWAN_PLANS.get(plan_id, {})
        
        if not plan or plan_id == "FREE":
            return {"savings": 0, "percentage": 0}
        
        monthly_total = plan["price_monthly_twd"] * 12
        annual_price = plan["price_annual_twd"]
        savings = monthly_total - annual_price
        percentage = round((savings / monthly_total) * 100)
        
        return {
            "savings": savings,
            "percentage": percentage,
            "monthly_equivalent": annual_price // 12
        }
    
    @classmethod
    def get_upgrade_recommendation(cls, current_plan: str) -> Dict[str, Any]:
        """取得升級建議"""
        
        if current_plan == "FREE":
            return {
                "recommended_plan": "PRO",
                "reasons": [
                    "解鎖無限會談記錄",
                    "提升檔案大小限制 233%",
                    "獲得角色識別功能",
                    "享受專業分析報告"
                ],
                "urgency": "high",
                "trial_available": False
            }
        
        elif current_plan == "PRO":
            return {
                "recommended_plan": "ENTERPRISE",
                "reasons": [
                    "團隊協作功能",
                    "企業級安全性",
                    "API 整合支援",
                    "專屬客戶經理"
                ],
                "urgency": "medium",
                "trial_available": True
            }
        
        return {"recommended_plan": None}
```

### Pricing Display Components
```tsx
// apps/web/components/pricing/TaiwanPricingTable.tsx
import { useState } from 'react';
import { useTranslation } from 'react-i18next';

interface PricingTableProps {
  currentPlan?: string;
  showUpgradeRecommendation?: boolean;
}

export const TaiwanPricingTable: React.FC<PricingTableProps> = ({
  currentPlan,
  showUpgradeRecommendation = true
}) => {
  const { t } = useTranslation('pricing');
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  return (
    <div className="taiwan-pricing-table">
      {/* Billing cycle toggle */}
      <div className="billing-cycle-selector">
        <div className="toggle-container">
          <button 
            className={`cycle-btn ${billingCycle === 'monthly' ? 'active' : ''}`}
            onClick={() => setBillingCycle('monthly')}
          >
            月繳
          </button>
          <button 
            className={`cycle-btn ${billingCycle === 'annual' ? 'active' : ''}`}
            onClick={() => setBillingCycle('annual')}
          >
            年繳
            <span className="savings-badge">省 2 個月</span>
          </button>
        </div>
      </div>

      {/* Upgrade recommendation */}
      {showUpgradeRecommendation && currentPlan && (
        <UpgradeRecommendation currentPlan={currentPlan} />
      )}

      {/* Pricing cards */}
      <div className="pricing-grid">
        {Object.entries(TAIWAN_PLANS).map(([planId, plan]) => (
          <PricingCard
            key={planId}
            planId={planId}
            plan={plan}
            billingCycle={billingCycle}
            currentPlan={currentPlan}
            onUpgrade={handleUpgrade}
          />
        ))}
      </div>

      {/* Value proposition */}
      <TaiwanValueProposition />
      
      {/* Competitor comparison */}
      <CompetitorComparison />
    </div>
  );
};

const PricingCard: React.FC<{
  planId: string;
  plan: any;
  billingCycle: 'monthly' | 'annual';
  currentPlan?: string;
  onUpgrade: (planId: string, cycle: string) => void;
}> = ({ planId, plan, billingCycle, currentPlan, onUpgrade }) => {
  const isCurrentPlan = currentPlan === planId;
  const price = billingCycle === 'annual' ? plan.price_annual_twd : plan.price_monthly_twd;
  const monthlyEquivalent = billingCycle === 'annual' ? plan.monthly_equivalent_annual : price;

  return (
    <div className={`pricing-card ${plan.popular ? 'popular' : ''} ${isCurrentPlan ? 'current' : ''}`}>
      {plan.popular && <div className="popular-badge">最受歡迎</div>}
      {isCurrentPlan && <div className="current-badge">目前方案</div>}

      <div className="plan-header">
        <h3 className="plan-name">{plan.display_name}</h3>
        <p className="plan-subtitle">{plan.subtitle}</p>
      </div>

      <div className="plan-pricing">
        {planId !== 'FREE' ? (
          <>
            <div className="price-display">
              <span className="currency">NT$</span>
              <span className="amount">
                {formatNumber(price / 100)}
              </span>
              <span className="period">
                /{billingCycle === 'annual' ? '年' : '月'}
              </span>
            </div>
            
            {billingCycle === 'annual' && (
              <div className="annual-details">
                <div className="monthly-equivalent">
                  平均每月 NT${formatNumber(monthlyEquivalent / 100)}
                </div>
                <div className="savings-highlight">
                  年繳省 NT${formatNumber(plan.savings_annual / 100)}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="free-price">
            <span className="amount">免費</span>
          </div>
        )}
      </div>

      <div className="plan-features">
        <h4>功能特色</h4>
        <ul>
          {plan.features.map((feature: string, index: number) => (
            <li key={index}>
              <CheckIcon className="check-icon" />
              <span>{feature}</span>
            </li>
          ))}
        </ul>
        
        {plan.upgrade_benefits && (
          <div className="upgrade-benefits">
            <h5>升級優勢</h5>
            <ul className="benefits-list">
              {plan.upgrade_benefits.map((benefit: string, index: number) => (
                <li key={index} className="benefit-item">
                  <ArrowUpIcon className="upgrade-icon" />
                  <span>{benefit}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="plan-action">
        {isCurrentPlan ? (
          <button className="btn-current" disabled>
            目前使用中
          </button>
        ) : planId === 'FREE' ? (
          <button className="btn-secondary">
            開始免費使用
          </button>
        ) : (
          <button 
            className="btn-primary"
            onClick={() => onUpgrade(planId, billingCycle)}
          >
            {currentPlan === 'FREE' ? '立即升級' : '選擇此方案'}
          </button>
        )}
      </div>
    </div>
  );
};

const UpgradeRecommendation: React.FC<{ currentPlan: string }> = ({ currentPlan }) => {
  const recommendation = getUpgradeRecommendation(currentPlan);
  
  if (!recommendation.recommended_plan) return null;

  return (
    <div className="upgrade-recommendation">
      <div className="recommendation-content">
        <h3>為您推薦</h3>
        <p>
          基於您目前的 {getPlanDisplayName(currentPlan)} 方案，
          我們建議升級到 <strong>{getPlanDisplayName(recommendation.recommended_plan)}</strong>
        </p>
        
        <div className="recommendation-reasons">
          {recommendation.reasons.map((reason, index) => (
            <div key={index} className="reason-item">
              <StarIcon className="reason-icon" />
              <span>{reason}</span>
            </div>
          ))}
        </div>
        
        <button className="btn-recommendation">
          了解 {getPlanDisplayName(recommendation.recommended_plan)} 方案
        </button>
      </div>
    </div>
  );
};

const TaiwanValueProposition: React.FC = () => {
  return (
    <div className="value-proposition">
      <h3>為什麼選擇我們？</h3>
      <div className="value-grid">
        <ValueItem 
          icon="🎯" 
          title="專為教練設計"
          description="針對教練會談優化的轉錄和分析功能"
        />
        <ValueItem 
          icon="🇹🇼" 
          title="繁體中文優化"
          description="完整支援台灣用語和專業術語"
        />
        <ValueItem 
          icon="💰" 
          title="台灣在地定價"
          description="比國際工具更具競爭力的本土價格"
        />
        <ValueItem 
          icon="🛡️" 
          title="資料安全保護"
          description="符合台灣個資法規，資料在地保存"
        />
      </div>
    </div>
  );
};

const CompetitorComparison: React.FC = () => {
  return (
    <div className="competitor-comparison">
      <h3>價格比較</h3>
      <div className="comparison-table">
        <div className="comparison-header">
          <div>服務</div>
          <div>月費</div>
          <div>中文支援</div>
          <div>教練功能</div>
        </div>
        
        <div className="comparison-row our-service">
          <div>教練助理 (我們)</div>
          <div>NT$899</div>
          <div>✅ 完整支援</div>
          <div>✅ 專業優化</div>
        </div>
        
        <div className="comparison-row">
          <div>Otter.ai</div>
          <div>NT$510</div>
          <div>❌ 有限</div>
          <div>❌ 無</div>
        </div>
        
        <div className="comparison-row">
          <div>Rev.ai</div>
          <div>NT$660</div>
          <div>❌ 無</div>
          <div>❌ 無</div>
        </div>
      </div>
    </div>
  );
};
```

### Pricing API
```python
# src/coaching_assistant/api/v1/pricing.py
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/api/v1/pricing", tags=["Pricing"])

@router.get("/taiwan")
async def get_taiwan_pricing():
    """取得台灣市場定價"""
    
    pricing_data = {}
    
    for plan_id, plan_config in TaiwanPricingConfig.TAIWAN_PLANS.items():
        annual_savings = TaiwanPricingConfig.calculate_annual_savings(plan_id)
        
        pricing_data[plan_id] = {
            **plan_config,
            "annual_savings": annual_savings,
            "formatted_monthly": format_twd_currency(plan_config["price_monthly_twd"]),
            "formatted_annual": format_twd_currency(plan_config["price_annual_twd"])
        }
    
    return {
        "plans": pricing_data,
        "currency": "TWD",
        "market": "taiwan",
        "value_propositions": TaiwanPricingConfig.VALUE_PROPOSITIONS,
        "competitor_comparison": TaiwanPricingConfig.COMPETITOR_COMPARISON
    }

@router.get("/upgrade-recommendation")
async def get_upgrade_recommendation(
    current_user: User = Depends(get_current_user)
):
    """取得個人化升級建議"""
    
    current_plan = current_user.current_plan or "FREE"
    recommendation = TaiwanPricingConfig.get_upgrade_recommendation(current_plan)
    
    return {
        "current_plan": current_plan,
        "recommendation": recommendation,
        "pricing": TaiwanPricingConfig.get_plan_pricing(recommendation.get("recommended_plan"))
    }
```

## 🧪 Test Plan

### Unit Tests
```python
def test_taiwan_pricing_configuration():
    """測試台灣定價配置"""
    pro_plan = TaiwanPricingConfig.get_plan_pricing("PRO")
    
    assert pro_plan["price_monthly_twd"] == 89900  # NT$899
    assert pro_plan["price_annual_twd"] == 899900   # NT$8,999
    assert pro_plan["display_name"] == "專業方案"
    assert pro_plan["popular"] == True

def test_annual_savings_calculation():
    """測試年繳節省計算"""
    savings = TaiwanPricingConfig.calculate_annual_savings("PRO")
    
    assert savings["savings"] == 178900  # 省 NT$1,789 (2個月)
    assert savings["percentage"] == 17    # 省 17%
    assert savings["monthly_equivalent"] == 74992  # 年繳平均每月

def test_upgrade_recommendation():
    """測試升級建議"""
    # 免費用戶建議
    free_rec = TaiwanPricingConfig.get_upgrade_recommendation("FREE")
    assert free_rec["recommended_plan"] == "PRO"
    assert free_rec["urgency"] == "high"
    
    # PRO 用戶建議
    pro_rec = TaiwanPricingConfig.get_upgrade_recommendation("PRO")
    assert pro_rec["recommended_plan"] == "ENTERPRISE"
    assert pro_rec["urgency"] == "medium"

def test_currency_formatting():
    """測試台幣格式化"""
    assert format_twd_currency(89900) == "NT$899"
    assert format_twd_currency(899900) == "NT$8,999"
    assert format_twd_currency(2999900) == "NT$29,999"
```

### Integration Tests
```python
@pytest.mark.integration
async def test_pricing_api():
    """測試定價 API"""
    response = await client.get("/api/v1/pricing/taiwan")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "plans" in data
    assert "PRO" in data["plans"]
    assert data["plans"]["PRO"]["price_monthly_twd"] == 89900
    assert data["currency"] == "TWD"

@pytest.mark.integration
async def test_upgrade_recommendation_api():
    """測試升級建議 API"""
    # 以免費用戶身份測試
    user = await create_test_user(plan="FREE")
    
    response = await client.get("/api/v1/pricing/upgrade-recommendation")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["current_plan"] == "FREE"
    assert data["recommendation"]["recommended_plan"] == "PRO"
```

### Frontend Tests
```typescript
describe('Taiwan Pricing Display', () => {
  test('displays pricing in TWD correctly', () => {
    render(<TaiwanPricingTable />);
    
    expect(screen.getByText('NT$899')).toBeInTheDocument();
    expect(screen.getByText('專業方案')).toBeInTheDocument();
    expect(screen.getByText('最受歡迎')).toBeInTheDocument();
  });

  test('shows annual savings correctly', () => {
    render(<TaiwanPricingTable />);
    
    // 切換到年繳
    fireEvent.click(screen.getByText('年繳'));
    
    expect(screen.getByText('省 2 個月')).toBeInTheDocument();
    expect(screen.getByText('年繳省 NT$1,789')).toBeInTheDocument();
    expect(screen.getByText('平均每月 NT$750')).toBeInTheDocument();
  });

  test('displays upgrade recommendation', () => {
    render(<TaiwanPricingTable currentPlan="FREE" />);
    
    expect(screen.getByText('為您推薦')).toBeInTheDocument();
    expect(screen.getByText('解鎖無限會談記錄')).toBeInTheDocument();
  });

  test('shows competitor comparison', () => {
    render(<CompetitorComparison />);
    
    expect(screen.getByText('Otter.ai')).toBeInTheDocument();
    expect(screen.getByText('NT$510')).toBeInTheDocument();
    expect(screen.getByText('❌ 有限')).toBeInTheDocument();
  });
});
```

## 📋 Definition of Done
- [ ] All acceptance criteria met
- [ ] Taiwan pricing strategy implemented
- [ ] Annual savings calculation working
- [ ] Plan comparison table complete
- [ ] Upgrade recommendations working
- [ ] Traditional Chinese pricing display
- [ ] Mobile responsive design
- [ ] Competitor comparison shown
- [ ] Value proposition clear
- [ ] One-click upgrade integration

## 🔗 Related Stories
- **Previous**: US-SUB-001, US-SUB-002 (Foundation required)
- **Next**: None (Enhancement story)

## 📝 Notes
- 定價基於台灣市場研究和競爭分析
- 年繳提供 2 個月免費 (相當於 83 折)
- PRO 方案定位為最受歡迎，適合個人教練
- ENTERPRISE 方案針對教練機構和團隊
- 與國際競爭者相比具有價格和功能優勢

## 🚀 Deployment Checklist
- [ ] Taiwan pricing configuration deployed
- [ ] Pricing API endpoints working
- [ ] Currency formatting tested
- [ ] Upgrade recommendations validated
- [ ] Mobile pricing display tested
- [ ] A/B testing setup for pricing optimization
- [ ] Market feedback collection system ready