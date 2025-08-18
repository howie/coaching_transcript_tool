# US-SUB-002: Subscription Management

## 📋 User Story
**As a** Taiwan coaching professional with an active subscription  
**I want** to manage my subscription (view, upgrade, downgrade, cancel)  
**So that** I can control my billing and adapt to changing needs

## 🎯 Epic
SaaS Subscription Management

## 📊 Story Details
- **Story ID**: US-SUB-002
- **Priority**: P0 (Critical)
- **Story Points**: 10
- **Sprint**: Week 1-2 (Days 6-10)

## 📋 Dependencies
- **Depends On**: 
  - US-SUB-001 (Credit Card Authorization) - Active subscriptions to manage
- **Blocks**: 
  - US-SUB-003 (Automatic Billing)
  - US-SUB-004 (Plan Upgrades)

## ✅ Acceptance Criteria
- [ ] View current subscription details (plan, billing cycle, next payment)
- [ ] See payment history and next billing date
- [ ] Upgrade plan immediately with prorated billing
- [ ] Downgrade plan (effective at period end)
- [ ] Cancel subscription with immediate or period-end options
- [ ] Reactivate cancelled subscription
- [ ] Change billing cycle (monthly ↔ annual)
- [ ] Update payment method (re-authorize card)
- [ ] Subscription status indicators (active, cancelled, past_due)
- [ ] Traditional Chinese interface with clear terminology

## 🏗️ Technical Implementation

### Backend Tasks
- [ ] Subscription management API endpoints
- [ ] Plan upgrade/downgrade logic with prorated billing
- [ ] Subscription cancellation handling
- [ ] Payment method update workflow
- [ ] Billing cycle change functionality
- [ ] Subscription reactivation logic
- [ ] Subscription status management

### Frontend Tasks
- [ ] Subscription dashboard component
- [ ] Plan change interface
- [ ] Cancellation flow with confirmation
- [ ] Payment method management
- [ ] Billing history display
- [ ] Status indicators and notifications

### API Endpoints
```python
# src/coaching_assistant/api/v1/subscriptions.py
from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/v1/subscriptions", tags=["Subscriptions"])

@router.get("/current")
async def get_current_subscription(
    current_user: User = Depends(get_current_user)
):
    """取得用戶當前訂閱資訊"""
    subscription = db.query(SaasSubscription).filter(
        SaasSubscription.user_id == current_user.id,
        SaasSubscription.status.in_(["active", "past_due"])
    ).first()
    
    if not subscription:
        return {"status": "no_subscription"}
    
    # 取得授權信用卡資訊
    auth_record = subscription.auth_record
    
    return {
        "subscription": {
            "id": str(subscription.id),
            "plan_id": subscription.plan_id,
            "plan_name": subscription.plan_name,
            "billing_cycle": subscription.billing_cycle,
            "amount": subscription.amount_twd,
            "status": subscription.status,
            "current_period_start": subscription.current_period_start.isoformat(),
            "current_period_end": subscription.current_period_end.isoformat(),
            "cancel_at_period_end": subscription.cancel_at_period_end,
            "next_payment_date": auth_record.next_pay_date.isoformat() if auth_record else None
        },
        "payment_method": {
            "card_last4": auth_record.card_last4 if auth_record else None,
            "card_brand": auth_record.card_brand if auth_record else None,
            "auth_status": auth_record.auth_status if auth_record else None
        } if auth_record else None
    }

@router.post("/upgrade")
async def upgrade_subscription(
    request: SubscriptionUpgradeRequest,
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """升級訂閱方案"""
    try:
        result = await subscription_service.upgrade_subscription(
            user_id=current_user.id,
            new_plan_id=request.plan_id,
            new_billing_cycle=request.billing_cycle
        )
        
        return {
            "success": True,
            "subscription": result["subscription"],
            "prorated_charge": result.get("prorated_charge"),
            "effective_date": result["effective_date"]
        }
        
    except Exception as e:
        logger.error(f"訂閱升級失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/downgrade")
async def downgrade_subscription(
    request: SubscriptionDowngradeRequest,
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """降級訂閱方案"""
    try:
        result = await subscription_service.downgrade_subscription(
            user_id=current_user.id,
            new_plan_id=request.plan_id,
            new_billing_cycle=request.billing_cycle
        )
        
        return {
            "success": True,
            "subscription": result["subscription"],
            "effective_date": result["effective_date"],  # 期末生效
            "credit_amount": result.get("credit_amount")  # 如有退款
        }
        
    except Exception as e:
        logger.error(f"訂閱降級失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/cancel")
async def cancel_subscription(
    request: SubscriptionCancelRequest,
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """取消訂閱"""
    try:
        result = await subscription_service.cancel_subscription(
            user_id=current_user.id,
            immediate=request.immediate,
            cancellation_reason=request.reason
        )
        
        return {
            "success": True,
            "cancelled_at": result["cancelled_at"],
            "effective_date": result["effective_date"],
            "refund_amount": result.get("refund_amount")
        }
        
    except Exception as e:
        logger.error(f"訂閱取消失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/reactivate")
async def reactivate_subscription(
    current_user: User = Depends(get_current_user),
    subscription_service: SubscriptionService = Depends(get_subscription_service)
):
    """重新啟用訂閱"""
    try:
        result = await subscription_service.reactivate_subscription(
            user_id=current_user.id
        )
        
        return {
            "success": True,
            "subscription": result["subscription"],
            "next_payment_date": result["next_payment_date"]
        }
        
    except Exception as e:
        logger.error(f"訂閱重新啟用失敗: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/billing-history")
async def get_billing_history(
    current_user: User = Depends(get_current_user),
    limit: int = 10,
    offset: int = 0
):
    """取得帳單歷史記錄"""
    payments = db.query(SubscriptionPayment).filter(
        SubscriptionPayment.subscription_id.in_(
            db.query(SaasSubscription.id).filter(
                SaasSubscription.user_id == current_user.id
            )
        )
    ).order_by(
        SubscriptionPayment.processed_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "payments": [
            {
                "id": str(payment.id),
                "amount": payment.amount,
                "currency": payment.currency,
                "status": payment.status,
                "period_start": payment.period_start.isoformat(),
                "period_end": payment.period_end.isoformat(),
                "processed_at": payment.processed_at.isoformat() if payment.processed_at else None,
                "failure_reason": payment.failure_reason
            }
            for payment in payments
        ]
    }
```

### Subscription Service Logic
```python
# src/coaching_assistant/core/services/subscription_service.py
from decimal import Decimal
from datetime import datetime, timedelta

class SubscriptionService:
    """訂閱管理服務"""
    
    async def upgrade_subscription(
        self, 
        user_id: str, 
        new_plan_id: str, 
        new_billing_cycle: str
    ) -> dict:
        """升級訂閱方案"""
        
        current_subscription = self._get_active_subscription(user_id)
        if not current_subscription:
            raise ValueError("無有效訂閱")
        
        # 檢查是否為升級
        if not self._is_upgrade(current_subscription.plan_id, new_plan_id):
            raise ValueError("只能升級到更高等級方案")
        
        # 計算按比例費用
        prorated_charge = self._calculate_prorated_charge(
            current_subscription, new_plan_id, new_billing_cycle
        )
        
        # 如果有額外費用，進行扣款
        if prorated_charge > 0:
            charge_result = await self._charge_prorated_amount(
                current_subscription.auth_record, prorated_charge
            )
            if not charge_result["success"]:
                raise ValueError("按比例扣款失敗")
        
        # 立即更新訂閱
        current_subscription.plan_id = new_plan_id
        current_subscription.plan_name = self._get_plan_name(new_plan_id)
        current_subscription.billing_cycle = new_billing_cycle
        current_subscription.amount_twd = self._get_plan_amount(new_plan_id, new_billing_cycle)
        
        # 更新 ECPay 授權金額
        await self._update_ecpay_authorization(
            current_subscription.auth_record.merchant_member_id,
            current_subscription.amount_twd
        )
        
        db.commit()
        
        # 立即升級用戶權限
        await self._upgrade_user_plan(user_id, new_plan_id)
        
        return {
            "subscription": current_subscription,
            "prorated_charge": prorated_charge,
            "effective_date": datetime.now().isoformat()
        }
    
    async def downgrade_subscription(
        self, 
        user_id: str, 
        new_plan_id: str, 
        new_billing_cycle: str
    ) -> dict:
        """降級訂閱方案（期末生效）"""
        
        current_subscription = self._get_active_subscription(user_id)
        if not current_subscription:
            raise ValueError("無有效訂閱")
        
        # 檢查是否為降級
        if not self._is_downgrade(current_subscription.plan_id, new_plan_id):
            raise ValueError("只能降級到較低等級方案")
        
        # 創建待生效的方案變更記錄
        pending_change = SubscriptionPendingChange(
            subscription_id=current_subscription.id,
            new_plan_id=new_plan_id,
            new_billing_cycle=new_billing_cycle,
            new_amount_twd=self._get_plan_amount(new_plan_id, new_billing_cycle),
            effective_date=current_subscription.current_period_end,
            change_type="downgrade"
        )
        
        db.add(pending_change)
        db.commit()
        
        return {
            "subscription": current_subscription,
            "effective_date": current_subscription.current_period_end.isoformat(),
            "pending_change": pending_change
        }
    
    async def cancel_subscription(
        self, 
        user_id: str, 
        immediate: bool = False,
        cancellation_reason: str = None
    ) -> dict:
        """取消訂閱"""
        
        current_subscription = self._get_active_subscription(user_id)
        if not current_subscription:
            raise ValueError("無有效訂閱")
        
        if immediate:
            # 立即取消
            current_subscription.status = "cancelled"
            current_subscription.cancelled_at = datetime.now()
            current_subscription.cancellation_reason = cancellation_reason
            
            # 取消 ECPay 授權
            await self._cancel_ecpay_authorization(
                current_subscription.auth_record.merchant_member_id
            )
            
            # 立即降級到免費方案
            await self._downgrade_user_to_free(user_id)
            
            effective_date = datetime.now()
            
            # 計算退款（如果有）
            refund_amount = self._calculate_refund_amount(current_subscription)
            
        else:
            # 期末取消
            current_subscription.cancel_at_period_end = True
            current_subscription.cancellation_reason = cancellation_reason
            
            effective_date = current_subscription.current_period_end
            refund_amount = 0
        
        db.commit()
        
        return {
            "cancelled_at": datetime.now().isoformat(),
            "effective_date": effective_date.isoformat(),
            "refund_amount": refund_amount
        }
    
    async def reactivate_subscription(self, user_id: str) -> dict:
        """重新啟用已取消的訂閱"""
        
        cancelled_subscription = db.query(SaasSubscription).filter(
            SaasSubscription.user_id == user_id,
            SaasSubscription.cancel_at_period_end == True,
            SaasSubscription.status == "active"
        ).first()
        
        if not cancelled_subscription:
            raise ValueError("無可重新啟用的訂閱")
        
        # 取消期末取消設定
        cancelled_subscription.cancel_at_period_end = False
        cancelled_subscription.cancellation_reason = None
        
        db.commit()
        
        return {
            "subscription": cancelled_subscription,
            "next_payment_date": cancelled_subscription.current_period_end.isoformat()
        }
    
    def _calculate_prorated_charge(
        self, 
        current_subscription: SaasSubscription, 
        new_plan_id: str, 
        new_billing_cycle: str
    ) -> int:
        """計算按比例費用"""
        
        # 當前方案剩餘天數
        today = datetime.now().date()
        remaining_days = (current_subscription.current_period_end - today).days
        total_days = (current_subscription.current_period_end - current_subscription.current_period_start).days
        
        # 當前方案剩餘價值
        current_remaining_value = (current_subscription.amount_twd * remaining_days) // total_days
        
        # 新方案價值
        new_plan_amount = self._get_plan_amount(new_plan_id, new_billing_cycle)
        new_plan_value = (new_plan_amount * remaining_days) // total_days
        
        # 需要額外支付的金額
        prorated_charge = max(0, new_plan_value - current_remaining_value)
        
        return prorated_charge
    
    def _is_upgrade(self, current_plan: str, new_plan: str) -> bool:
        """判斷是否為升級"""
        plan_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
        return plan_hierarchy.get(new_plan, 0) > plan_hierarchy.get(current_plan, 0)
    
    def _is_downgrade(self, current_plan: str, new_plan: str) -> bool:
        """判斷是否為降級"""
        plan_hierarchy = {"FREE": 0, "PRO": 1, "ENTERPRISE": 2}
        return plan_hierarchy.get(new_plan, 0) < plan_hierarchy.get(current_plan, 0)
```

### Frontend Components
```tsx
// apps/web/components/subscription/SubscriptionDashboard.tsx
export const SubscriptionDashboard: React.FC = () => {
  const { t } = useTranslation('subscription');
  const [subscription, setSubscription] = useState<Subscription | null>(null);
  const [paymentHistory, setPaymentHistory] = useState<Payment[]>([]);

  return (
    <div className="subscription-dashboard">
      <div className="dashboard-header">
        <h1>訂閱管理</h1>
        <SubscriptionStatus status={subscription?.status} />
      </div>

      <div className="dashboard-content">
        <CurrentSubscriptionCard 
          subscription={subscription}
          onUpgrade={handleUpgrade}
          onDowngrade={handleDowngrade}
          onCancel={handleCancel}
        />
        
        <PaymentMethodCard 
          paymentMethod={subscription?.payment_method}
          onUpdatePaymentMethod={handleUpdatePaymentMethod}
        />
        
        <BillingHistoryCard 
          payments={paymentHistory}
          onDownloadInvoice={handleDownloadInvoice}
        />
      </div>
    </div>
  );
};

// Current subscription display
const CurrentSubscriptionCard: React.FC<{
  subscription: Subscription;
  onUpgrade: () => void;
  onDowngrade: () => void;
  onCancel: () => void;
}> = ({ subscription, onUpgrade, onDowngrade, onCancel }) => {
  if (!subscription) {
    return <NoSubscriptionCard />;
  }

  return (
    <div className="subscription-card">
      <div className="plan-info">
        <h3>{subscription.plan_name}</h3>
        <div className="plan-price">
          {formatTWD(subscription.amount)}
          <span className="billing-cycle">
            /{subscription.billing_cycle === 'monthly' ? '月' : '年'}
          </span>
        </div>
      </div>

      <div className="subscription-details">
        <DetailRow 
          label="下次付款日期"
          value={formatDate(subscription.next_payment_date)}
        />
        <DetailRow 
          label="訂閱狀態"
          value={<SubscriptionStatusBadge status={subscription.status} />}
        />
        {subscription.cancel_at_period_end && (
          <DetailRow 
            label="取消日期"
            value={formatDate(subscription.current_period_end)}
            warning={true}
          />
        )}
      </div>

      <div className="subscription-actions">
        {!subscription.cancel_at_period_end && (
          <>
            <button className="btn-primary" onClick={onUpgrade}>
              升級方案
            </button>
            <button className="btn-secondary" onClick={onDowngrade}>
              降級方案
            </button>
            <button className="btn-danger" onClick={onCancel}>
              取消訂閱
            </button>
          </>
        )}
        
        {subscription.cancel_at_period_end && (
          <button className="btn-primary" onClick={handleReactivate}>
            重新啟用訂閱
          </button>
        )}
      </div>
    </div>
  );
};

// Plan change modal
const PlanChangeModal: React.FC<{
  currentPlan: string;
  changeType: 'upgrade' | 'downgrade';
  onConfirm: (planId: string, billingCycle: string) => void;
  onClose: () => void;
}> = ({ currentPlan, changeType, onConfirm, onClose }) => {
  const [selectedPlan, setSelectedPlan] = useState('');
  const [selectedCycle, setSelectedCycle] = useState('monthly');

  return (
    <Modal onClose={onClose}>
      <div className="plan-change-modal">
        <h2>{changeType === 'upgrade' ? '升級方案' : '降級方案'}</h2>
        
        <PlanSelector 
          currentPlan={currentPlan}
          changeType={changeType}
          selectedPlan={selectedPlan}
          onPlanSelect={setSelectedPlan}
        />
        
        <BillingCycleSelector 
          selectedCycle={selectedCycle}
          onCycleSelect={setSelectedCycle}
        />
        
        {changeType === 'upgrade' && (
          <ProrationPreview 
            currentPlan={currentPlan}
            newPlan={selectedPlan}
            newCycle={selectedCycle}
          />
        )}
        
        {changeType === 'downgrade' && (
          <div className="downgrade-notice">
            <Warning />
            <p>降級將在當前計費週期結束後生效</p>
          </div>
        )}
        
        <div className="modal-actions">
          <button 
            className="btn-primary"
            onClick={() => onConfirm(selectedPlan, selectedCycle)}
            disabled={!selectedPlan}
          >
            確認{changeType === 'upgrade' ? '升級' : '降級'}
          </button>
          <button className="btn-secondary" onClick={onClose}>
            取消
          </button>
        </div>
      </div>
    </Modal>
  );
};
```

## 🧪 Test Plan

### Unit Tests
```python
def test_subscription_upgrade():
    """測試訂閱升級"""
    service = SubscriptionService()
    
    # 建立測試用戶和訂閱
    user = create_test_user()
    subscription = create_test_subscription(user.id, "PRO", "monthly")
    
    # 執行升級
    result = await service.upgrade_subscription(
        user_id=str(user.id),
        new_plan_id="ENTERPRISE",
        new_billing_cycle="monthly"
    )
    
    assert result["subscription"].plan_id == "ENTERPRISE"
    assert result["prorated_charge"] > 0  # 應該有按比例費用

def test_subscription_downgrade():
    """測試訂閱降級"""
    service = SubscriptionService()
    
    user = create_test_user()
    subscription = create_test_subscription(user.id, "ENTERPRISE", "monthly")
    
    # 執行降級
    result = await service.downgrade_subscription(
        user_id=str(user.id),
        new_plan_id="PRO",
        new_billing_cycle="monthly"
    )
    
    # 降級應該期末生效
    assert result["effective_date"] == subscription.current_period_end.isoformat()

def test_subscription_cancellation():
    """測試訂閱取消"""
    service = SubscriptionService()
    
    user = create_test_user()
    subscription = create_test_subscription(user.id, "PRO", "monthly")
    
    # 期末取消
    result = await service.cancel_subscription(
        user_id=str(user.id),
        immediate=False,
        cancellation_reason="不再需要"
    )
    
    updated_subscription = db.query(SaasSubscription).get(subscription.id)
    assert updated_subscription.cancel_at_period_end == True
    assert updated_subscription.status == "active"  # 仍然活躍到期末

def test_subscription_reactivation():
    """測試訂閱重新啟用"""
    service = SubscriptionService()
    
    user = create_test_user()
    subscription = create_test_subscription(user.id, "PRO", "monthly")
    
    # 先取消
    await service.cancel_subscription(str(user.id), immediate=False)
    
    # 重新啟用
    result = await service.reactivate_subscription(str(user.id))
    
    updated_subscription = db.query(SaasSubscription).get(subscription.id)
    assert updated_subscription.cancel_at_period_end == False
```

### Integration Tests
```python
@pytest.mark.integration
async def test_subscription_management_api():
    """測試訂閱管理 API"""
    # 建立用戶和訂閱
    user = await create_test_user_with_subscription()
    
    # 測試取得當前訂閱
    response = await client.get("/api/v1/subscriptions/current")
    assert response.status_code == 200
    
    data = response.json()
    assert data["subscription"]["plan_id"] == "PRO"
    assert data["payment_method"]["card_last4"] is not None

@pytest.mark.integration
async def test_upgrade_with_prorated_billing():
    """測試按比例計費的升級"""
    # 建立測試訂閱
    user = await create_test_user_with_subscription("PRO", "monthly")
    
    # 執行升級
    response = await client.post("/api/v1/subscriptions/upgrade", json={
        "plan_id": "ENTERPRISE",
        "billing_cycle": "monthly"
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] == True
    assert data["subscription"]["plan_id"] == "ENTERPRISE"
    assert data["prorated_charge"] > 0
```

### Frontend Tests
```typescript
describe('Subscription Management', () => {
  test('displays current subscription correctly', () => {
    const mockSubscription = {
      plan_name: "專業方案",
      amount: 89900,
      billing_cycle: "monthly",
      status: "active",
      next_payment_date: "2024-02-01"
    };
    
    render(<CurrentSubscriptionCard subscription={mockSubscription} />);
    
    expect(screen.getByText('專業方案')).toBeInTheDocument();
    expect(screen.getByText('NT$899/月')).toBeInTheDocument();
    expect(screen.getByText('升級方案')).toBeInTheDocument();
  });

  test('shows cancellation confirmation', () => {
    render(<CancellationModal onConfirm={jest.fn()} onClose={jest.fn()} />);
    
    expect(screen.getByText('確定要取消訂閱嗎？')).toBeInTheDocument();
    expect(screen.getByText('立即取消')).toBeInTheDocument();
    expect(screen.getByText('期末取消')).toBeInTheDocument();
  });

  test('displays plan change options', () => {
    render(
      <PlanChangeModal 
        currentPlan="PRO" 
        changeType="upgrade" 
        onConfirm={jest.fn()}
        onClose={jest.fn()}
      />
    );
    
    expect(screen.getByText('升級方案')).toBeInTheDocument();
    expect(screen.getByText('企業方案')).toBeInTheDocument();
  });
});
```

## 📋 Definition of Done
- [ ] All acceptance criteria met
- [ ] Subscription management API complete
- [ ] Plan upgrade/downgrade working with prorated billing
- [ ] Subscription cancellation and reactivation working
- [ ] Payment method update functionality
- [ ] Traditional Chinese interface complete
- [ ] Billing history display working
- [ ] Error handling for all scenarios
- [ ] Security review passed

## 🔗 Related Stories
- **Previous**: US-SUB-001 (Credit Card Authorization)
- **Next**: US-SUB-003 (Automatic Billing)

## 📝 Notes
- 升級立即生效並按比例計費
- 降級期末生效，避免用戶損失
- 取消可選擇立即或期末生效
- 支援重新啟用已取消的訂閱
- 所有操作都有清楚的確認流程

## 🚀 Deployment Checklist
- [ ] Subscription management API deployed
- [ ] Prorated billing logic tested
- [ ] ECPay authorization update functionality working
- [ ] Cancellation workflow tested
- [ ] Customer support trained on subscription management
- [ ] Billing dispute process documented