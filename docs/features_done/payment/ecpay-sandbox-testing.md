# ECPay 測試環境整合指南

## 🧪 ECPay Sandbox Environment

ECPay 提供完整的測試環境 (Sandbox) 供開發者進行整合測試，無需真實交易即可驗證付款流程。

## 🔑 測試環境參數

### 測試商店資訊
```bash
# ECPay 測試環境設定
ECPAY_ENVIRONMENT=sandbox
ECPAY_MERCHANT_ID=3002607
ECPAY_HASH_KEY=pwFHCqoQZGmho4w6
ECPAY_HASH_IV=EkRm7iFT261dpevs

# 測試環境 URLs
ECPAY_API_URL=https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5
ECPAY_CREDIT_DETAIL_URL=https://payment-stage.ecpay.com.tw/CreditDetail/DoAction
ECPAY_VENDOR_URL=https://vendor-stage.ecpay.com.tw/
```

### 測試後台登入
```
登入網址: https://vendor-stage.ecpay.com.tw/
帳號: stagetest3
密碼: test1234
```

## 💳 測試信用卡資料

### 標準測試卡號
```bash
# 一般信用卡
VISA: 4311-9511-1111-1111
MASTERCARD: 4311-9522-2222-2222

# 海外信用卡
OVERSEAS: 4000-2011-1111-1111

# 通用設定
到期日: 任何未來日期 (如: 12/2025)
安全碼: 任何3位數字 (如: 123)
持卡人姓名: 任何英文名稱
```

### 3D 驗證設定
```bash
# 測試環境固定 SMS 驗證碼
SMS_CODE: 1234

# 所有 3D 驗證都使用此固定驗證碼
# 無需真實手機號碼或 SMS 接收
```

## 🔧 SaaS 訂閱測試配置

### Python 環境設定
```python
# src/coaching_assistant/config/ecpay_sandbox.py
import os

class ECPaySandboxConfig:
    """ECPay 測試環境配置"""
    
    # 測試環境基本設定
    ENVIRONMENT = "sandbox"
    MERCHANT_ID = "3002607"
    HASH_KEY = "pwFHCqoQZGmho4w6"
    HASH_IV = "EkRm7iFT261dpevs"
    
    # API URLs (測試環境)
    AIO_URL = "https://payment-stage.ecpay.com.tw/Cashier/AioCheckOut/V5"
    CREDIT_DETAIL_URL = "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction"
    QUERY_URL = "https://payment-stage.ecpay.com.tw/Cashier/QueryTradeInfo/V5"
    
    # 定期定額相關 (SaaS 訂閱)
    PERIOD_URL = "https://payment-stage.ecpay.com.tw/CreditDetail/DoAction"
    
    # Webhook URLs (需要公開可訪問的 URL)
    RETURN_URL = f"{os.getenv('API_BASE_URL', 'http://localhost:8000')}/api/webhooks/ecpay-auth"
    ORDER_RESULT_URL = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/subscription/result"
    CLIENT_BACK_URL = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/billing"
    
    @classmethod
    def get_config(cls) -> dict:
        """取得測試環境完整配置"""
        return {
            "environment": cls.ENVIRONMENT,
            "merchant_id": cls.MERCHANT_ID,
            "hash_key": cls.HASH_KEY,
            "hash_iv": cls.HASH_IV,
            "api_urls": {
                "aio": cls.AIO_URL,
                "credit_detail": cls.CREDIT_DETAIL_URL,
                "query": cls.QUERY_URL,
                "period": cls.PERIOD_URL
            },
            "callback_urls": {
                "return_url": cls.RETURN_URL,
                "order_result_url": cls.ORDER_RESULT_URL,
                "client_back_url": cls.CLIENT_BACK_URL
            }
        }
```

### 環境變數設定
```bash
# .env.development
ECPAY_ENVIRONMENT=sandbox
ECPAY_MERCHANT_ID=3002607
ECPAY_HASH_KEY=pwFHCqoQZGmho4w6
ECPAY_HASH_IV=EkRm7iFT261dpevs

# 本地開發 URLs
API_BASE_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000

# 或使用 ngrok 產生的公開 URL 用於 webhook 測試
# API_BASE_URL=https://abc123.ngrok.io
# FRONTEND_URL=https://def456.ngrok.io
```

## 🧪 測試流程指南

### 1. 信用卡授權測試
```python
# 測試信用卡定期定額授權
async def test_credit_authorization():
    """測試信用卡授權流程"""
    
    # 使用測試環境配置
    config = ECPaySandboxConfig.get_config()
    
    # 建立授權請求
    auth_data = {
        "MerchantID": config["merchant_id"],
        "MerchantMemberID": "TEST_USER_001",
        "ActionType": "CreateAuth",
        "TotalAmount": 899,  # NT$899 測試金額
        "ProductDesc": "測試專業方案訂閱",
        "PeriodType": "Month",
        "Frequency": 1,
        "PeriodAmount": 899,
        "ExecTimes": 0,  # 不限制次數
        "PaymentType": "aio",
        "ChoosePayment": "Credit"
    }
    
    # 生成 CheckMacValue 並提交
    return auth_data
```

### 2. 測試用信用卡資料
```javascript
// 前端測試表單預設值
const TEST_CARD_DATA = {
  cardNumber: "4311-9511-1111-1111",
  expiryMonth: "12",
  expiryYear: "2025",
  cvv: "123",
  holderName: "TEST USER"
};

// 3D 驗證測試
const SMS_VERIFICATION_CODE = "1234"; // 固定測試驗證碼
```

### 3. Webhook 測試設定
```bash
# 使用 ngrok 建立公開 URL 用於 webhook 測試
ngrok http 8000

# 將產生的 URL 設定為環境變數
export API_BASE_URL=https://abc123.ngrok.io
export FRONTEND_URL=http://localhost:3000
```

## 🔍 測試檢查清單

### 信用卡授權測試
- [ ] 使用測試卡號建立授權
- [ ] 3D 驗證使用固定碼 "1234"
- [ ] 授權成功後收到 webhook 回調
- [ ] 授權資料正確儲存到資料庫
- [ ] 用戶方案成功升級

### 定期扣款測試
- [ ] 首次授權成功
- [ ] 模擬定期扣款 webhook
- [ ] 扣款成功延長訂閱期間
- [ ] 扣款失敗觸發重試機制
- [ ] 通知信件正確發送

### 訂閱管理測試
- [ ] 方案升級功能
- [ ] 方案降級功能
- [ ] 訂閱取消功能
- [ ] 重新啟用功能
- [ ] 按比例計費正確

## ⚠️ 測試注意事項

### 重要提醒
1. **僅限測試環境**: 測試參數只能用於 sandbox，不可用於正式環境
2. **測試卡號**: 使用提供的測試卡號，不要使用真實信用卡
3. **固定驗證碼**: 3D 驗證永遠使用 "1234"
4. **到期日設定**: 信用卡到期日必須是未來日期
5. **Webhook URL**: 必須是公開可訪問的 HTTPS URL

### 常見問題
- **Webhook 收不到**: 檢查 URL 是否公開可訪問
- **CheckMacValue 錯誤**: 確認參數排序和編碼正確
- **授權失敗**: 檢查測試卡號和到期日設定
- **3D 驗證**: 永遠輸入 "1234" 作為驗證碼

## 🚀 上線前檢查

### 切換到正式環境
```python
# 正式環境配置 (需要申請真實商店參數)
class ECPayProductionConfig:
    ENVIRONMENT = "production"
    MERCHANT_ID = "your_real_merchant_id"
    HASH_KEY = "your_real_hash_key"
    HASH_IV = "your_real_hash_iv"
    
    # 正式環境 URLs
    AIO_URL = "https://payment.ecpay.com.tw/Cashier/AioCheckOut/V5"
    CREDIT_DETAIL_URL = "https://payment.ecpay.com.tw/CreditDetail/DoAction"
```

### 上線檢查清單
- [ ] 替換為正式環境參數
- [ ] 移除所有測試相關程式碼
- [ ] 確認 webhook URL 使用 HTTPS
- [ ] 驗證真實信用卡交易
- [ ] 監控系統正常運作

---

**建議**: 在開發階段充分使用測試環境驗證所有功能，確保 SaaS 訂閱流程完全正確後再切換到正式環境。