# US-SUB-001: ECPay Credit Card Authorization

## 📋 User Story
**As a** Taiwan coaching professional  
**I want** to authorize my credit card for automatic subscription billing  
**So that** I can enjoy uninterrupted premium features without manual payments

## 🎯 Epic
SaaS Subscription Foundation

## 📊 Story Details
- **Story ID**: US-SUB-001
- **Priority**: P0 (Critical)
- **Story Points**: 13
- **Sprint**: Week 1 (Days 1-5)

## 📋 Dependencies
- **Depends On**: None (Foundation story)
- **Blocks**: 
  - US-SUB-002 (Subscription Management)
  - US-SUB-003 (Automatic Billing)
  - US-SUB-004 (Plan Upgrades)

## ✅ Acceptance Criteria
- [ ] ECPay merchant configured for 定期定額 (recurring payments)
- [ ] Credit card authorization flow working end-to-end
- [ ] Support Visa, Mastercard, JCB cards
- [ ] Secure card data handling with PCI compliance
- [ ] Authorization success creates active subscription
- [ ] Failed authorization shows clear error messages
- [ ] User can see authorized card details (masked)
- [ ] Authorization can be cancelled by user
- [ ] Traditional Chinese interface

## 🏗️ Technical Implementation

### Backend Tasks
- [ ] Configure ECPay 定期定額 API integration
- [ ] Implement ECPaySubscriptionService
- [ ] Create credit authorization database models
- [ ] Build authorization callback handling
- [ ] Implement subscription creation logic
- [ ] Add user plan upgrade after authorization
- [ ] Create authorization cancellation endpoint

### Frontend Tasks
- [ ] Credit card authorization form
- [ ] Authorization progress tracking
- [ ] Success/failure feedback UI
- [ ] Authorized card display component
- [ ] Authorization cancellation interface

### ECPay 定期定額 Integration
```python
# ECPay Credit Authorization Parameters
ECPAY_AUTH_PARAMS = {
    "ActionType": "CreateAuth",           # 建立授權
    "PaymentType": "aio",                 # All-in-one
    "ChoosePayment": "Credit",            # 信用卡付款
    "PeriodType": "Month",                # 月繳週期
    "Frequency": 1,                       # 每月扣款
    "ExecTimes": 0,                       # 不限制次數
    "PeriodAmount": 899,                  # 每月金額 NT$899
    "TotalAmount": 899                    # 首次授權金額
}

# 建立授權流程
def create_credit_authorization(user_id: str, plan_id: str, billing_cycle: str):
    """建立 ECPay 信用卡定期定額授權"""
    
    # 1. 生成唯一的商店會員編號
    merchant_member_id = f"USER{user_id[:8]}{int(time.time())}"
    
    # 2. 準備授權參數
    auth_params = {
        "MerchantID": settings.ECPAY_MERCHANT_ID,
        "MerchantMemberID": merchant_member_id,
        "ActionType": "CreateAuth",
        "TotalAmount": get_plan_amount(plan_id, billing_cycle),
        "ProductDesc": f"{get_plan_name(plan_id)}方案訂閱",
        "PeriodType": "Month" if billing_cycle == "monthly" else "Year",
        "Frequency": 1,
        "PeriodAmount": get_plan_amount(plan_id, billing_cycle),
        "ExecTimes": 0,  # 持續扣款
        "ReturnURL": f"{API_BASE_URL}/api/webhooks/ecpay-auth",
        "OrderResultURL": f"{FRONTEND_URL}/subscription/result"
    }
    
    # 3. 生成 CheckMacValue
    auth_params["CheckMacValue"] = generate_check_mac_value(auth_params)
    
    # 4. 儲存授權記錄到資料庫
    auth_record = ECPayCreditAuthorization(
        user_id=user_id,
        merchant_member_id=merchant_member_id,
        auth_amount=get_plan_amount(plan_id, billing_cycle),
        period_type=auth_params["PeriodType"],
        period_amount=auth_params["PeriodAmount"],
        auth_status="pending"
    )
    db.add(auth_record)
    db.commit()
    
    return {
        "action_url": "https://payment.ecpay.com.tw/CreditDetail/DoAction",
        "form_data": auth_params,
        "auth_id": str(auth_record.id)
    }
```

### Database Schema
```sql
-- ECPay 信用卡授權記錄
CREATE TABLE ecpay_credit_authorizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES "user"(id),
    
    -- ECPay 識別
    merchant_member_id VARCHAR(30) UNIQUE NOT NULL,
    gwsr VARCHAR(100), -- ECPay 交易單號
    auth_code VARCHAR(20), -- 授權碼
    
    -- 授權設定
    auth_amount INTEGER NOT NULL, -- 授權金額 (TWD cents)
    period_type VARCHAR(10) NOT NULL, -- 'Month', 'Year'
    frequency INTEGER DEFAULT 1,
    period_amount INTEGER NOT NULL, -- 每期金額
    exec_times INTEGER DEFAULT 0, -- 已執行次數
    
    -- 信用卡資訊
    card_last4 VARCHAR(4),
    card_brand VARCHAR(20), -- VISA, MASTERCARD, JCB
    card_type VARCHAR(20),
    
    -- 狀態管理
    auth_status VARCHAR(20) DEFAULT 'pending', -- pending, active, cancelled, failed
    auth_date TIMESTAMP,
    next_pay_date DATE,
    
    -- 元數據
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- 索引優化
CREATE INDEX idx_auth_user_id ON ecpay_credit_authorizations(user_id);
CREATE INDEX idx_auth_merchant_member_id ON ecpay_credit_authorizations(merchant_member_id);
CREATE INDEX idx_auth_status ON ecpay_credit_authorizations(auth_status);
```

## 🧪 Test Plan

### Unit Tests
```python
def test_create_credit_authorization():
    """測試信用卡授權建立"""
    service = ECPaySubscriptionService()
    auth_data = service.create_credit_authorization(
        user_id="test-user-123",
        plan_id="PRO",
        billing_cycle="monthly"
    )
    
    assert auth_data["action_url"] == "https://payment.ecpay.com.tw/CreditDetail/DoAction"
    assert auth_data["form_data"]["ActionType"] == "CreateAuth"
    assert auth_data["form_data"]["ChoosePayment"] == "Credit"
    assert auth_data["form_data"]["PeriodType"] == "Month"
    assert auth_data["form_data"]["PeriodAmount"] == 899

def test_authorization_callback_success():
    """測試授權成功回調"""
    callback_data = {
        "RtnCode": "1",
        "RtnMsg": "授權成功",
        "MerchantMemberID": "USER12345678901234567",
        "gwsr": "240101123456789",
        "AuthCode": "123456",
        "card4no": "1234",
        "card6no": "VISA",
        "CheckMacValue": "valid_mac_value"
    }
    
    service = ECPaySubscriptionService()
    result = service.handle_auth_callback(callback_data)
    
    assert result == True
    
    # 驗證授權記錄已更新
    auth_record = db.query(ECPayCreditAuthorization).filter(
        ECPayCreditAuthorization.merchant_member_id == "USER12345678901234567"
    ).first()
    
    assert auth_record.auth_status == "active"
    assert auth_record.gwsr == "240101123456789"
    assert auth_record.card_last4 == "1234"
    assert auth_record.card_brand == "VISA"

def test_authorization_callback_failure():
    """測試授權失敗回調"""
    callback_data = {
        "RtnCode": "0",
        "RtnMsg": "信用卡授權失敗",
        "MerchantMemberID": "USER12345678901234567",
        "CheckMacValue": "valid_mac_value"
    }
    
    service = ECPaySubscriptionService()
    result = service.handle_auth_callback(callback_data)
    
    assert result == False
    
    # 驗證授權記錄標記為失敗
    auth_record = db.query(ECPayCreditAuthorization).filter(
        ECPayCreditAuthorization.merchant_member_id == "USER12345678901234567"
    ).first()
    
    assert auth_record.auth_status == "failed"

def test_cancel_authorization():
    """測試取消授權"""
    # 建立測試授權
    auth_record = create_test_authorization()
    
    service = ECPaySubscriptionService()
    result = service.cancel_authorization(str(auth_record.id))
    
    assert result == True
    
    # 驗證授權已取消
    updated_record = db.query(ECPayCreditAuthorization).get(auth_record.id)
    assert updated_record.auth_status == "cancelled"
```

### Integration Tests
```python
@pytest.mark.integration
async def test_complete_authorization_flow():
    """測試完整的授權流程"""
    # 1. 建立授權請求
    response = await client.post("/api/v1/subscriptions/authorize", json={
        "plan_id": "PRO",
        "billing_cycle": "monthly"
    })
    
    assert response.status_code == 200
    auth_data = response.json()
    
    # 2. 模擬 ECPay 授權成功回調
    callback_response = await client.post("/api/webhooks/ecpay-auth", data={
        "RtnCode": "1",
        "RtnMsg": "授權成功",
        "MerchantMemberID": auth_data["merchant_member_id"],
        "gwsr": "test-gwsr-123",
        "AuthCode": "123456",
        "card4no": "1234",
        "card6no": "VISA"
    })
    
    assert callback_response.status_code == 200
    
    # 3. 驗證用戶方案已升級
    user_response = await client.get("/api/v1/user/profile")
    user_data = user_response.json()
    
    assert user_data["current_plan"] == "PRO"
    assert user_data["subscription_status"] == "active"

@pytest.mark.integration
async def test_authorization_security():
    """測試授權安全性"""
    # 測試無效的 CheckMacValue
    invalid_callback = await client.post("/api/webhooks/ecpay-auth", data={
        "RtnCode": "1",
        "MerchantMemberID": "TEST123",
        "CheckMacValue": "invalid_mac"
    })
    
    assert invalid_callback.status_code == 400
```

### Frontend Tests
```typescript
describe('Credit Card Authorization', () => {
  test('renders authorization form correctly', () => {
    render(<CreditAuthorizationForm planId="PRO" billingCycle="monthly" />);
    
    expect(screen.getByText('信用卡自動扣款授權')).toBeInTheDocument();
    expect(screen.getByText('NT$899/月')).toBeInTheDocument();
    expect(screen.getByText('確認授權')).toBeInTheDocument();
  });

  test('shows authorization progress', () => {
    render(<AuthorizationProgress status="processing" />);
    
    expect(screen.getByText('正在處理授權...')).toBeInTheDocument();
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
  });

  test('displays authorized card information', () => {
    const cardInfo = {
      card_last4: "1234",
      card_brand: "VISA",
      auth_date: "2024-01-01"
    };
    
    render(<AuthorizedCardDisplay cardInfo={cardInfo} />);
    
    expect(screen.getByText('VISA ****1234')).toBeInTheDocument();
    expect(screen.getByText('授權日期: 2024-01-01')).toBeInTheDocument();
  });

  test('handles authorization cancellation', () => {
    const mockCancel = jest.fn();
    render(<AuthorizedCardDisplay onCancel={mockCancel} />);
    
    fireEvent.click(screen.getByText('取消授權'));
    
    expect(screen.getByText('確定要取消自動扣款授權嗎？')).toBeInTheDocument();
    
    fireEvent.click(screen.getByText('確認取消'));
    expect(mockCancel).toHaveBeenCalled();
  });
});
```

### End-to-End Tests
```typescript
test('complete credit card authorization flow', async ({ page }) => {
  // 1. 登入並前往方案選擇
  await page.goto('/login');
  await page.fill('[data-testid="email"]', 'test@example.com');
  await page.fill('[data-testid="password"]', 'password');
  await page.click('[data-testid="login-button"]');

  // 2. 選擇 PRO 方案
  await page.goto('/billing');
  await page.click('[data-testid="select-pro-monthly"]');

  // 3. 確認授權
  await expect(page.locator('[data-testid="auth-form"]')).toBeVisible();
  await expect(page.locator('text=NT$899/月')).toBeVisible();
  await page.click('[data-testid="confirm-authorization"]');

  // 4. 重定向到 ECPay (模擬)
  await page.waitForURL('**/ecpay/**');
  
  // 模擬 ECPay 授權成功並返回
  await page.goto('/subscription/result?status=success');

  // 5. 驗證授權成功
  await expect(page.locator('text=授權成功')).toBeVisible();
  await expect(page.locator('text=PRO 方案已啟用')).toBeVisible();

  // 6. 檢查授權的信用卡
  await page.goto('/billing/payment-methods');
  await expect(page.locator('text=VISA ****1234')).toBeVisible();
  await expect(page.locator('text=自動扣款')).toBeVisible();
});
```

## 📋 Definition of Done
- [ ] All acceptance criteria met
- [ ] ECPay 定期定額 integration working
- [ ] Credit card authorization flow complete
- [ ] Authorization callback handling working
- [ ] Subscription creation after authorization
- [ ] User plan upgrade working
- [ ] Authorization cancellation working
- [ ] Traditional Chinese interface
- [ ] Security review passed
- [ ] Performance testing completed

## 🔗 Related Stories
- **Next**: US-SUB-002 (Subscription Management)
- **Enables**: All subscription functionality

## 📝 Notes
- ECPay 定期定額是台灣信用卡自動扣款的標準做法
- 首次授權金額等於每期扣款金額
- 授權成功後立即創建訂閱並升級用戶方案
- 用戶可隨時取消授權，但會在當期結束後生效
- 支援月繳和年繳兩種週期

## 🚀 Deployment Checklist
- [ ] ECPay merchant 定期定額功能已開通
- [ ] Production webhook URL 已設定
- [ ] SSL certificate 已配置
- [ ] Authorization flow 在 production 環境測試
- [ ] 信用卡資料安全性驗證
- [ ] PCI compliance 確認
- [ ] Customer support 訓練完成