# US-SUB-003: Automatic Billing

## 📋 User Story
**As a** Taiwan coaching professional with an active subscription  
**I want** my credit card to be automatically charged each billing cycle  
**So that** I can enjoy uninterrupted service without manual payments

## 🎯 Epic
SaaS Subscription Management

## 📊 Story Details
- **Story ID**: US-SUB-003
- **Priority**: P0 (Critical)
- **Story Points**: 8
- **Sprint**: Week 2 (Days 6-8)

## 📋 Dependencies
- **Depends On**: 
  - US-SUB-001 (Credit Card Authorization) - Active authorizations to bill
- **Blocks**: 
  - US-SUB-004 (Plan Upgrades) - Need billing infrastructure

## ✅ Acceptance Criteria
- [ ] ECPay automatic billing webhook processing
- [ ] Successful payment extends subscription period
- [ ] Failed payment retry mechanism (3 attempts)
- [ ] Past due subscription handling
- [ ] Automatic downgrade to FREE plan after repeated failures
- [ ] Payment success/failure notifications in Traditional Chinese
- [ ] Billing history tracking for all automatic charges
- [ ] Grace period for failed payments (7 days)
- [ ] Subscription status updates in real-time

## 🏗️ Technical Implementation

### Backend Tasks
- [ ] ECPay billing webhook endpoint
- [ ] Automatic payment processing logic
- [ ] Failed payment retry mechanism
- [ ] Subscription period extension
- [ ] Past due subscription handling
- [ ] Automatic plan downgrade logic
- [ ] Billing notification service
- [ ] Payment reconciliation system

### Frontend Tasks
- [ ] Payment status indicators
- [ ] Failed payment notifications
- [ ] Billing history display
- [ ] Subscription status dashboard
- [ ] Payment retry manual trigger

### ECPay Automatic Billing Webhook
```python
# src/coaching_assistant/api/webhooks/ecpay_billing.py
from fastapi import APIRouter, Form, HTTPException
import logging

router = APIRouter(prefix="/api/webhooks", tags=["ECPay Webhooks"])
logger = logging.getLogger(__name__)

@router.post("/ecpay-billing")
async def handle_automatic_billing(
    MerchantID: str = Form(...),
    MerchantMemberID: str = Form(...),
    gwsr: str = Form(...),                    # ECPay 交易單號
    amount: str = Form(...),                  # 扣款金額
    process_date: str = Form(...),            # 處理日期
    auth_code: str = Form(...),               # 授權碼
    RtnCode: str = Form(...),                 # 回應代碼
    RtnMsg: str = Form(...),                  # 回應訊息
    CheckMacValue: str = Form(...),           # 檢查碼
    billing_service: AutomaticBillingService = Depends(get_billing_service)
):
    """處理 ECPay 自動扣款回調"""
    
    try:
        # 準備回調數據
        callback_data = {
            "MerchantID": MerchantID,
            "MerchantMemberID": MerchantMemberID,
            "gwsr": gwsr,
            "amount": amount,
            "process_date": process_date,
            "auth_code": auth_code,
            "RtnCode": RtnCode,
            "RtnMsg": RtnMsg,
            "CheckMacValue": CheckMacValue
        }
        
        # 驗證 CheckMacValue
        if not billing_service.verify_callback(callback_data):
            logger.error(f"ECPay 自動扣款 CheckMacValue 驗證失敗: {gwsr}")
            return "0|CheckMacValue verification failed"
        
        # 處理自動扣款結果
        success = await billing_service.process_automatic_payment(callback_data)
        
        if success:
            logger.info(f"ECPay 自動扣款處理成功: {gwsr}")
            return "1|OK"
        else:
            logger.error(f"ECPay 自動扣款處理失敗: {gwsr}")
            return "0|Processing failed"
            
    except Exception as e:
        logger.error(f"ECPay 自動扣款 Webhook 錯誤: {e}")
        return "0|Internal error"

class AutomaticBillingService:
    """自動扣款服務"""
    
    async def process_automatic_payment(self, callback_data: dict) -> bool:
        """處理自動扣款回調"""
        
        try:
            merchant_member_id = callback_data["MerchantMemberID"]
            gwsr = callback_data["gwsr"]
            rtn_code = callback_data["RtnCode"]
            amount = int(callback_data["amount"]) * 100  # 轉換為 cents
            
            # 找到對應的授權記錄
            auth_record = db.query(ECPayCreditAuthorization).filter(
                ECPayCreditAuthorization.merchant_member_id == merchant_member_id
            ).first()
            
            if not auth_record:
                logger.error(f"找不到授權記錄: {merchant_member_id}")
                return False
            
            # 找到對應的訂閱
            subscription = db.query(SaasSubscription).filter(
                SaasSubscription.auth_id == auth_record.id,
                SaasSubscription.status.in_(["active", "past_due"])
            ).first()
            
            if not subscription:
                logger.error(f"找不到有效訂閱: {auth_record.id}")
                return False
            
            # 創建付款記錄
            payment_record = SubscriptionPayment(
                subscription_id=subscription.id,
                auth_id=auth_record.id,
                gwsr=gwsr,
                amount=amount,
                currency="TWD",
                period_start=subscription.current_period_start,
                period_end=subscription.current_period_end,
                ecpay_response=callback_data,
                processed_at=datetime.now()
            )
            
            if rtn_code == "1":  # 扣款成功
                await self._handle_successful_payment(
                    auth_record, subscription, payment_record
                )
            else:  # 扣款失敗
                await self._handle_failed_payment(
                    auth_record, subscription, payment_record, callback_data["RtnMsg"]
                )
            
            db.add(payment_record)
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"自動扣款處理錯誤: {e}")
            db.rollback()
            return False
    
    async def _handle_successful_payment(
        self, 
        auth_record: ECPayCreditAuthorization,
        subscription: SaasSubscription,
        payment_record: SubscriptionPayment
    ):
        """處理成功的自動扣款"""
        
        payment_record.status = "success"
        
        # 延長訂閱期間
        if auth_record.period_type == "Month":
            new_period_start = subscription.current_period_end + timedelta(days=1)
            new_period_end = new_period_start + timedelta(days=30)
        else:  # Year
            new_period_start = subscription.current_period_end + timedelta(days=1)
            new_period_end = new_period_start + timedelta(days=365)
        
        subscription.current_period_start = new_period_start
        subscription.current_period_end = new_period_end
        subscription.status = "active"  # 確保狀態為活躍
        
        # 更新下次扣款日期
        auth_record.next_pay_date = new_period_end
        auth_record.exec_times += 1
        
        # 重置重試次數
        payment_record.retry_count = 0
        
        # 發送成功通知
        await self._send_payment_success_notification(subscription.user_id, payment_record)
        
        logger.info(f"訂閱延長成功: {subscription.id}, 新期間: {new_period_start} - {new_period_end}")
    
    async def _handle_failed_payment(
        self,
        auth_record: ECPayCreditAuthorization,
        subscription: SaasSubscription,
        payment_record: SubscriptionPayment,
        failure_reason: str
    ):
        """處理失敗的自動扣款"""
        
        payment_record.status = "failed"
        payment_record.failure_reason = failure_reason
        
        # 增加重試次數
        last_payment = db.query(SubscriptionPayment).filter(
            SubscriptionPayment.subscription_id == subscription.id,
            SubscriptionPayment.status == "failed"
        ).order_by(SubscriptionPayment.created_at.desc()).first()
        
        if last_payment:
            payment_record.retry_count = last_payment.retry_count + 1
        else:
            payment_record.retry_count = 1
        
        # 檢查重試次數
        if payment_record.retry_count >= 3:
            # 標記為逾期
            subscription.status = "past_due"
            
            # 設定寬限期 (7天)
            grace_period_end = datetime.now() + timedelta(days=7)
            
            # 發送最終警告通知
            await self._send_final_payment_warning(subscription.user_id, grace_period_end)
            
            # 排程寬限期結束後的處理
            await self._schedule_grace_period_end_processing(subscription.id, grace_period_end)
            
        else:
            # 發送付款失敗通知
            await self._send_payment_failed_notification(
                subscription.user_id, payment_record, payment_record.retry_count
            )
            
            # 排程下次重試 (24小時後)
            await self._schedule_payment_retry(subscription.id, datetime.now() + timedelta(hours=24))
        
        logger.warning(f"扣款失敗: {subscription.id}, 重試次數: {payment_record.retry_count}")
    
    async def _handle_grace_period_expiry(self, subscription_id: str):
        """處理寬限期到期"""
        
        subscription = db.query(SaasSubscription).get(subscription_id)
        if not subscription or subscription.status != "past_due":
            return
        
        # 檢查寬限期內是否有成功付款
        recent_success = db.query(SubscriptionPayment).filter(
            SubscriptionPayment.subscription_id == subscription.id,
            SubscriptionPayment.status == "success",
            SubscriptionPayment.processed_at >= datetime.now() - timedelta(days=7)
        ).first()
        
        if not recent_success:
            # 取消訂閱並降級到免費方案
            subscription.status = "cancelled"
            subscription.cancelled_at = datetime.now()
            subscription.cancellation_reason = "Payment failure after grace period"
            
            # 取消 ECPay 授權
            auth_record = subscription.auth_record
            if auth_record:
                await self._cancel_ecpay_authorization(auth_record.merchant_member_id)
                auth_record.auth_status = "cancelled"
            
            # 降級用戶到免費方案
            await self._downgrade_user_to_free(subscription.user_id)
            
            # 發送取消通知
            await self._send_subscription_cancelled_notification(subscription.user_id)
            
            db.commit()
            
            logger.info(f"訂閱因付款失敗取消: {subscription.id}")
    
    async def _send_payment_success_notification(self, user_id: str, payment: SubscriptionPayment):
        """發送付款成功通知"""
        
        user = db.query(User).get(user_id)
        if not user:
            return
        
        # Email 通知
        await send_email(
            to=user.email,
            subject="付款成功確認",
            template="payment_success_tw.html",
            context={
                "user_name": user.name,
                "amount": payment.amount // 100,
                "period_start": payment.period_start.strftime("%Y-%m-%d"),
                "period_end": payment.period_end.strftime("%Y-%m-%d"),
                "next_payment_date": payment.period_end.strftime("%Y-%m-%d")
            }
        )
    
    async def _send_payment_failed_notification(
        self, 
        user_id: str, 
        payment: SubscriptionPayment,
        retry_count: int
    ):
        """發送付款失敗通知"""
        
        user = db.query(User).get(user_id)
        if not user:
            return
        
        await send_email(
            to=user.email,
            subject=f"付款失敗通知 (第 {retry_count} 次)",
            template="payment_failed_tw.html",
            context={
                "user_name": user.name,
                "amount": payment.amount // 100,
                "failure_reason": payment.failure_reason,
                "retry_count": retry_count,
                "max_retries": 3,
                "next_retry_date": (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d %H:%M")
            }
        )
    
    async def _send_final_payment_warning(self, user_id: str, grace_period_end: datetime):
        """發送最終付款警告"""
        
        user = db.query(User).get(user_id)
        if not user:
            return
        
        await send_email(
            to=user.email,
            subject="訂閱即將取消 - 最終通知",
            template="final_payment_warning_tw.html",
            context={
                "user_name": user.name,
                "grace_period_end": grace_period_end.strftime("%Y-%m-%d"),
                "update_payment_url": f"{settings.FRONTEND_URL}/billing/payment-methods"
            }
        )
```

### Database Enhancements
```sql
-- 付款重試記錄
CREATE TABLE payment_retry_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES saas_subscriptions(id),
    payment_id UUID REFERENCES subscription_payments(id),
    
    -- 重試資訊
    retry_attempt INTEGER NOT NULL,
    scheduled_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    
    -- 結果
    success BOOLEAN,
    failure_reason TEXT,
    
    created_at TIMESTAMP DEFAULT NOW()
);

-- 寬限期記錄
CREATE TABLE grace_periods (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID NOT NULL REFERENCES saas_subscriptions(id),
    
    -- 寬限期設定
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    reason VARCHAR(100) NOT NULL, -- 'payment_failure', 'card_expired'
    
    -- 狀態
    status VARCHAR(20) DEFAULT 'active', -- active, resolved, expired
    resolved_at TIMESTAMP,
    resolution_type VARCHAR(50), -- 'payment_success', 'manual_intervention', 'cancelled'
    
    created_at TIMESTAMP DEFAULT NOW()
);
```

## 🧪 Test Plan

### Unit Tests
```python
def test_successful_automatic_payment():
    """測試成功的自動扣款"""
    service = AutomaticBillingService()
    
    # 建立測試訂閱
    subscription = create_test_subscription()
    original_end_date = subscription.current_period_end
    
    # 模擬成功的扣款回調
    callback_data = {
        "MerchantMemberID": subscription.auth_record.merchant_member_id,
        "gwsr": "test-gwsr-123",
        "amount": "899",
        "RtnCode": "1",
        "RtnMsg": "Success"
    }
    
    # 處理扣款
    result = await service.process_automatic_payment(callback_data)
    
    assert result == True
    
    # 驗證訂閱期間延長
    updated_subscription = db.query(SaasSubscription).get(subscription.id)
    assert updated_subscription.current_period_end > original_end_date
    assert updated_subscription.status == "active"

def test_failed_automatic_payment():
    """測試失敗的自動扣款"""
    service = AutomaticBillingService()
    
    subscription = create_test_subscription()
    
    # 模擬失敗的扣款回調
    callback_data = {
        "MerchantMemberID": subscription.auth_record.merchant_member_id,
        "gwsr": "test-gwsr-failed",
        "amount": "899",
        "RtnCode": "0",
        "RtnMsg": "Insufficient funds"
    }
    
    # 處理扣款
    result = await service.process_automatic_payment(callback_data)
    
    assert result == True
    
    # 驗證付款記錄
    payment = db.query(SubscriptionPayment).filter(
        SubscriptionPayment.gwsr == "test-gwsr-failed"
    ).first()
    
    assert payment.status == "failed"
    assert payment.retry_count == 1
    assert payment.failure_reason == "Insufficient funds"

def test_grace_period_handling():
    """測試寬限期處理"""
    service = AutomaticBillingService()
    
    subscription = create_test_subscription()
    
    # 模擬 3 次連續失敗
    for i in range(3):
        callback_data = {
            "MerchantMemberID": subscription.auth_record.merchant_member_id,
            "gwsr": f"test-gwsr-failed-{i}",
            "amount": "899",
            "RtnCode": "0",
            "RtnMsg": "Card declined"
        }
        
        await service.process_automatic_payment(callback_data)
    
    # 驗證訂閱狀態變為 past_due
    updated_subscription = db.query(SaasSubscription).get(subscription.id)
    assert updated_subscription.status == "past_due"
    
    # 驗證寬限期記錄
    grace_period = db.query(GracePeriod).filter(
        GracePeriod.subscription_id == subscription.id
    ).first()
    
    assert grace_period is not None
    assert grace_period.status == "active"

def test_subscription_cancellation_after_grace_period():
    """測試寬限期後的訂閱取消"""
    service = AutomaticBillingService()
    
    subscription = create_test_subscription()
    subscription.status = "past_due"
    db.commit()
    
    # 模擬寬限期到期
    await service._handle_grace_period_expiry(str(subscription.id))
    
    # 驗證訂閱已取消
    updated_subscription = db.query(SaasSubscription).get(subscription.id)
    assert updated_subscription.status == "cancelled"
    assert updated_subscription.cancelled_at is not None
    
    # 驗證授權已取消
    auth_record = updated_subscription.auth_record
    assert auth_record.auth_status == "cancelled"
```

### Integration Tests
```python
@pytest.mark.integration
async def test_automatic_billing_webhook():
    """測試自動扣款 Webhook 端點"""
    
    # 建立測試訂閱
    subscription = await create_test_subscription_with_auth()
    
    # 發送成功扣款回調
    response = await client.post("/api/webhooks/ecpay-billing", data={
        "MerchantID": settings.ECPAY_MERCHANT_ID,
        "MerchantMemberID": subscription.auth_record.merchant_member_id,
        "gwsr": "test-gwsr-integration",
        "amount": "899",
        "process_date": "2024/01/01 12:00:00",
        "auth_code": "123456",
        "RtnCode": "1",
        "RtnMsg": "Success",
        "CheckMacValue": generate_valid_mac()
    })
    
    assert response.status_code == 200
    assert response.text == "1|OK"
    
    # 驗證訂閱已延長
    updated_subscription = await get_subscription(subscription.id)
    assert updated_subscription.current_period_end > subscription.current_period_end

@pytest.mark.integration 
async def test_notification_system():
    """測試通知系統"""
    
    # 測試付款成功通知
    await send_payment_success_notification("test-user-id", test_payment)
    
    # 驗證 email 已發送
    sent_emails = await get_sent_emails()
    assert len(sent_emails) == 1
    assert "付款成功確認" in sent_emails[0]["subject"]
    assert "感謝您的付款" in sent_emails[0]["body"]
```

### Frontend Tests
```typescript
describe('Automatic Billing Status', () => {
  test('displays successful payment in billing history', () => {
    const mockPayments = [
      {
        id: "payment-1",
        amount: 89900,
        status: "success",
        processed_at: "2024-01-01T12:00:00Z",
        period_start: "2024-01-01",
        period_end: "2024-01-31"
      }
    ];
    
    render(<BillingHistory payments={mockPayments} />);
    
    expect(screen.getByText('NT$899')).toBeInTheDocument();
    expect(screen.getByText('成功')).toBeInTheDocument();
    expect(screen.getByText('2024-01-01 ~ 2024-01-31')).toBeInTheDocument();
  });

  test('shows failed payment with retry information', () => {
    const mockPayment = {
      id: "payment-failed",
      amount: 89900,
      status: "failed",
      failure_reason: "餘額不足",
      retry_count: 2,
      next_retry_date: "2024-01-02T12:00:00Z"
    };
    
    render(<FailedPaymentAlert payment={mockPayment} />);
    
    expect(screen.getByText('付款失敗')).toBeInTheDocument();
    expect(screen.getByText('餘額不足')).toBeInTheDocument();
    expect(screen.getByText('重試次數: 2/3')).toBeInTheDocument();
    expect(screen.getByText('下次重試: 2024-01-02')).toBeInTheDocument();
  });

  test('displays grace period warning', () => {
    const mockGracePeriod = {
      end_date: "2024-01-08",
      days_remaining: 3
    };
    
    render(<GracePeriodWarning gracePeriod={mockGracePeriod} />);
    
    expect(screen.getByText('付款問題需要處理')).toBeInTheDocument();
    expect(screen.getByText('剩餘 3 天')).toBeInTheDocument();
    expect(screen.getByText('更新付款方式')).toBeInTheDocument();
  });
});
```

## 📋 Definition of Done
- [ ] All acceptance criteria met
- [ ] ECPay automatic billing webhook working
- [ ] Payment success/failure handling complete
- [ ] Retry mechanism implemented (3 attempts)
- [ ] Grace period handling working
- [ ] Automatic subscription cancellation working
- [ ] Notification system complete (success/failure/warning)
- [ ] Traditional Chinese notifications
- [ ] Payment reconciliation system working
- [ ] Error monitoring and alerting setup

## 🔗 Related Stories
- **Previous**: US-SUB-001 (Credit Card Authorization)
- **Next**: US-SUB-004 (Plan Upgrades & Pricing)

## 📝 Notes
- ECPay 自動扣款使用 Webhook 方式通知結果
- 失敗付款有 3 次重試機會，每次間隔 24 小時
- 寬限期 7 天給用戶時間更新付款方式
- 最終取消後自動降級到免費方案
- 所有通知都使用繁體中文，符合台灣用戶習慣

## 🚀 Deployment Checklist
- [ ] ECPay automatic billing webhook endpoint configured
- [ ] Webhook URL registered with ECPay
- [ ] SSL certificate for webhook endpoint
- [ ] Payment retry job scheduler setup
- [ ] Grace period cleanup job setup
- [ ] Email notification templates ready
- [ ] Monitoring for failed payments setup
- [ ] Customer support trained on billing issues