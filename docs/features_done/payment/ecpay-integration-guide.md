# ECPay 綠界金流整合指南

## 概述

本指南提供 ECPay 綠界金流信用卡定期定額服務的完整整合方案，適用於 SaaS 訂閱模式的付款處理。

## 整合架構

### 系統架構圖
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Frontend  │    │   Backend   │    │    ECPay    │
│  (Next.js)  │    │  (FastAPI)  │    │   Gateway   │
└─────────────┘    └─────────────┘    └─────────────┘
        │                  │                  │
        │ 1. 升級請求        │                  │
        ├─────────────────►│                  │
        │                  │ 2. 建立授權       │
        │                  ├─────────────────►│
        │                  │ 3. 回傳表單資料    │
        │                  │◄─────────────────┤
        │ 4. 表單資料        │                  │
        │◄─────────────────┤                  │
        │ 5. 提交付款表單     │                  │
        ├──────────────────────────────────────►│
        │                  │ 6. 授權結果回調    │
        │                  │◄─────────────────┤
```

### 技術棧
- **Frontend**: Next.js 14 + TypeScript
- **Backend**: FastAPI + Python 3.11+
- **Database**: PostgreSQL + SQLAlchemy ORM
- **ECPay API**: AioCheckOut V5 (定期定額)

## 核心服務實現

### 1. ECPaySubscriptionService

主要負責與 ECPay API 的整合邏輯：

```python
class ECPaySubscriptionService:
    """ECPay subscription service for SaaS billing."""
    
    def __init__(self, db: Session, settings: Settings):
        self.db = db
        self.settings = settings
        
        # ECPay configuration
        self.merchant_id = settings.ECPAY_MERCHANT_ID
        self.hash_key = settings.ECPAY_HASH_KEY
        self.hash_iv = settings.ECPAY_HASH_IV
        
        # API URLs (sandbox vs production)
        if settings.ECPAY_ENVIRONMENT == "sandbox":
            self.aio_url = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
        else:
            self.aio_url = "https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5"
```

### 2. 授權建立流程

```python
def create_credit_authorization(
    self, 
    user_id: str, 
    plan_id: str, 
    billing_cycle: str
) -> Dict[str, Any]:
    """Create ECPay credit card authorization for recurring payments."""
    
    # 1. 獲取方案定價
    plan_pricing = self._get_plan_pricing(plan_id, billing_cycle)
    
    # 2. 生成唯一識別碼
    timestamp = int(time.time())
    safe_user_prefix = ''.join(c for c in user_id[:8].upper() if c.isalnum())[:8]
    merchant_trade_no = f"SUB{str(timestamp)[-6:]}{safe_user_prefix}"
    
    # 3. 準備 ECPay 參數
    auth_data = {
        "MerchantID": self.merchant_id,
        "MerchantTradeNo": merchant_trade_no,
        "TotalAmount": str(plan_pricing["amount_twd"] // 100),  # 轉為字串
        "PeriodType": "M" if billing_cycle == "monthly" else "Y",
        "ExecTimes": str(0 if billing_cycle == "monthly" else 99),
        # ... 其他參數
    }
    
    # 4. 計算 CheckMacValue
    auth_data["CheckMacValue"] = self._generate_check_mac_value(auth_data)
    
    return {
        "action_url": self.aio_url,
        "form_data": auth_data
    }
```

## 前端整合實現

### 1. 升級流程觸發

```typescript
const handleConfirmChange = async () => {
  if (!selectedPlan || !user) return
  
  try {
    // 呼叫後端 API
    const data = await apiClient.post('/api/v1/subscriptions/authorize', {
      plan_id: ecpayPlanId,
      billing_cycle: billingCycle
    })
    
    // 建立並提交 ECPay 表單
    await submitECPayForm(data)
    
  } catch (error) {
    console.error('升級流程錯誤:', error)
    alert(`升級過程中發生錯誤: ${error.message}`)
  }
}
```

### 2. ECPay 表單提交

```typescript
const submitECPayForm = (data: any) => {
  // 建立表單
  const form = document.createElement('form')
  form.method = 'POST'
  form.action = data.action_url
  form.target = '_blank'
  
  // 新增表單欄位（不修改任何參數值）
  Object.entries(data.form_data).forEach(([key, value]) => {
    const input = document.createElement('input')
    input.type = 'hidden'
    input.name = key
    input.value = value === null || value === undefined ? '' : String(value).trim()
    form.appendChild(input)
  })
  
  // 提交表單
  document.body.appendChild(form)
  form.submit()
  document.body.removeChild(form)
}
```

## 參數配置標準

### 必要參數格式

| 參數名稱 | 格式要求 | 範例值 |
|---------|---------|--------|
| MerchantTradeNo | ≤20字元，英數字 | `SUB523767USER1234` |
| TotalAmount | 字串格式 | `"899"` |
| PeriodType | M或Y | `"M"` |
| ExecTimes | 字串格式 | `"0"` |
| TradeDesc | 中文說明 | `"教練助手訂閱"` |
| ItemName | 商品資訊 | `"訂閱方案#1#個#899"` |

### 業務規則

1. **ExecTimes 規則** (2025年更新):
   - 月繳 (`PeriodType = "M"`): 設為 `"999"` (999次)
   - 年繳 (`PeriodType = "Y"`): 設為 `"99"` (99次)

2. **金額計算**:
   - 資料庫存放分為單位 (cents)
   - 傳送給 ECPay 時除以 100 轉為元

3. **字元安全**:
   - MerchantTradeNo 只包含英數字
   - 用戶 ID 需要字元清理: `''.join(c for c in user_id if c.isalnum())`

## 回調處理

### 1. 授權成功回調

```python
def handle_auth_callback(self, callback_data: Dict[str, str]) -> bool:
    """Handle ECPay authorization callback."""
    
    # 1. 驗證 CheckMacValue
    if not self._verify_callback(callback_data):
        return False
    
    # 2. 查找授權記錄
    auth_record = self.db.query(ECPayCreditAuthorization).filter(
        ECPayCreditAuthorization.merchant_member_id == callback_data["MerchantMemberID"]
    ).first()
    
    if callback_data["RtnCode"] == "1":  # 成功
        # 3. 更新授權狀態
        auth_record.auth_status = ECPayAuthStatus.ACTIVE.value
        auth_record.gwsr = callback_data.get("gwsr")
        
        # 4. 建立訂閱
        subscription = self._create_subscription(auth_record)
        
        # 5. 升級用戶方案
        user.plan = plan_mapping[subscription.plan_id]
        
        self.db.commit()
        return True
```

### 2. 定期扣款回調

```python
def handle_payment_webhook(self, webhook_data: Dict[str, str]) -> bool:
    """Handle ECPay automatic billing webhook."""
    
    if webhook_data["RtnCode"] == "1":  # 扣款成功
        # 延展訂閱期間
        if auth_record.period_type == "M":
            new_period_end = subscription.current_period_end + timedelta(days=30)
        else:  # Y
            new_period_end = subscription.current_period_end + timedelta(days=365)
        
        subscription.current_period_end = new_period_end
        subscription.status = SubscriptionStatus.ACTIVE.value
```

## 安全考量

### 1. CheckMacValue 驗證

```python
def _generate_check_mac_value(self, data: Dict[str, str]) -> str:
    """Generate ECPay CheckMacValue for security verification."""
    
    # 移除 CheckMacValue 欄位
    data = {k: v for k, v in data.items() if k != "CheckMacValue"}
    
    # 參數排序
    sorted_data = sorted(data.items())
    
    # URL 編碼
    encoded_params = []
    for key, value in sorted_data:
        encoded_value = urllib.parse.quote_plus(str(value))
        encoded_params.append(f"{key}={encoded_value}")
    
    # 組成查詢字串
    query_string = "&".join(encoded_params)
    
    # 加入 HashKey 和 HashIV
    raw_string = f"HashKey={self.hash_key}&{query_string}&HashIV={self.hash_iv}"
    
    # URL 編碼並轉小寫
    encoded_string = urllib.parse.quote_plus(raw_string).lower()
    
    # SHA256 雜湊
    return hashlib.sha256(encoded_string.encode('utf-8')).hexdigest().upper()
```

### 2. 環境變數配置

```env
# ECPay 設定
ECPAY_MERCHANT_ID=3002607
ECPAY_HASH_KEY=pwFHCqoQZGmho4w6
ECPAY_HASH_IV=EkRm7iFT261dpevs
ECPAY_ENVIRONMENT=sandbox  # sandbox | production
```

## 資料庫模型

### 1. ECPay 授權表

```python
class ECPayCreditAuthorization(Base):
    __tablename__ = "ecpay_credit_authorizations"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    merchant_member_id = Column(String, unique=True, nullable=False)
    auth_amount = Column(Integer, nullable=False)  # 以分為單位
    period_type = Column(String, nullable=False)   # M or Y
    period_amount = Column(Integer, nullable=False)
    auth_status = Column(String, default=ECPayAuthStatus.PENDING.value)
    gwsr = Column(String)  # ECPay 授權碼
    next_pay_date = Column(Date)
```

### 2. 訂閱表

```python
class SaasSubscription(Base):
    __tablename__ = "saas_subscriptions"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    auth_id = Column(String, ForeignKey("ecpay_credit_authorizations.id"))
    plan_id = Column(String, nullable=False)      # PRO, ENTERPRISE
    billing_cycle = Column(String, nullable=False) # monthly, annual
    amount_twd = Column(Integer, nullable=False)   # 以分為單位
    status = Column(String, default=SubscriptionStatus.ACTIVE.value)
    current_period_start = Column(Date, nullable=False)
    current_period_end = Column(Date, nullable=False)
```

## API 端點

### 1. 建立授權

```python
@router.post("/authorize")
async def create_subscription_authorization(
    request: SubscriptionAuthRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create ECPay credit card authorization for subscription."""
    
    service = ECPaySubscriptionService(db, settings)
    
    try:
        result = service.create_credit_authorization(
            user_id=current_user.id,
            plan_id=request.plan_id,
            billing_cycle=request.billing_cycle
        )
        
        return {"success": True, **result}
        
    except Exception as e:
        logger.error(f"Authorization creation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))
```

### 2. 授權回調

```python
@router.post("/webhooks/ecpay-auth")
async def ecpay_auth_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle ECPay authorization callback."""
    
    form_data = await request.form()
    callback_data = dict(form_data)
    
    service = ECPaySubscriptionService(db, settings)
    success = service.handle_auth_callback(callback_data)
    
    return {"success": success}
```

## 測試策略

### 1. 單元測試

```python
def test_merchant_trade_no_generation():
    """測試 MerchantTradeNo 生成邏輯"""
    service = ECPaySubscriptionService(db, settings)
    
    # 測試長度限制
    result = service.create_credit_authorization("user123", "PRO", "monthly")
    assert len(result["form_data"]["MerchantTradeNo"]) <= 20
    
    # 測試字元安全
    assert result["form_data"]["MerchantTradeNo"].replace("SUB", "").isalnum()
```

### 2. 整合測試

```python
@pytest.mark.integration
def test_ecpay_authorization_flow():
    """測試完整授權流程"""
    
    # 1. 建立授權
    response = client.post("/api/v1/subscriptions/authorize", {
        "plan_id": "PRO",
        "billing_cycle": "monthly"
    })
    
    # 2. 驗證回應格式
    assert response["success"] == True
    assert "action_url" in response
    assert "form_data" in response
    
    # 3. 驗證關鍵參數
    form_data = response["form_data"]
    assert len(form_data["MerchantTradeNo"]) <= 20
    assert form_data["TotalAmount"] == "899"
    assert form_data["PeriodType"] == "M"
```

### 3. E2E 測試

```python
@pytest.mark.e2e
def test_real_ecpay_api():
    """測試真實 ECPay API 整合"""
    
    # 建立測試資料
    auth_data = create_test_authorization_data()
    
    # 實際呼叫 ECPay API
    response = requests.post(ECPAY_SANDBOX_URL, data=auth_data)
    
    # 驗證無錯誤
    assert "10200052" not in response.text  # MerchantTradeNo Error
    assert "10200073" not in response.text  # CheckMacValue Error
```

## 監控和維護

### 1. 關鍵指標監控

- **授權成功率**: > 95%
- **扣款成功率**: > 98%
- **CheckMacValue 錯誤率**: < 0.1%
- **平均處理時間**: < 2s

### 2. 錯誤告警

```python
# 設定告警閾值
ALERT_THRESHOLDS = {
    "auth_failure_rate": 0.05,  # 5% 授權失敗率
    "checkmac_error_rate": 0.001,  # 0.1% CheckMac 錯誤率
}

def check_ecpay_health():
    """檢查 ECPay 整合健康狀況"""
    
    recent_auths = get_recent_authorizations(hours=1)
    failure_rate = calculate_failure_rate(recent_auths)
    
    if failure_rate > ALERT_THRESHOLDS["auth_failure_rate"]:
        send_alert(f"ECPay authorization failure rate: {failure_rate:.2%}")
```

### 3. 定期檢查任務

```python
@celery.task
def daily_ecpay_health_check():
    """每日 ECPay 健康檢查"""
    
    # 檢查待處理的授權
    pending_auths = check_pending_authorizations()
    
    # 檢查失敗的扣款
    failed_payments = check_failed_payments()
    
    # 產生健康報告
    generate_health_report(pending_auths, failed_payments)
```

## 故障排除

詳細的故障排除指南請參考：[ECPay 故障排除指南](./ecpay-troubleshooting-guide.md)

## 更新歷程

- **v1.0** (2025-08-18): 初始版本，基於實際整合經驗
- **v1.1** (2025-08-18): 新增故障排除和最佳實踐

## 相關文檔

- [ECPay 經驗總結](./ecpay-lessons-learned.md)
- [ECPay 故障排除指南](./ecpay-troubleshooting-guide.md)
- [測試策略文檔](../../claude/testing.md)

---

*最後更新：2025-08-18*
*整合狀態：✅ 生產就緒*