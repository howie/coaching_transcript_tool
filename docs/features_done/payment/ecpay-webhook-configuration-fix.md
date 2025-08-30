# ECPay Webhook Configuration Fix

## 問題診斷

通過分析數據庫，發現 ECPay 訂閱功能的根本問題：**webhook 無法從 ECPay 伺服器訪問**

### 症狀
- ✅ ECPay 付款成功 (OrderResultURL 回調正常)
- ❌ 訂閱狀態未更新 (ReturnURL webhook 失敗)
- 🗄️ 資料庫狀態：10 筆 `pending` 授權，0 筆訂閱記錄，0 筆 webhook 日誌

### 根本原因
**API_BASE_URL 配置問題**:
```bash
# 目前配置 (.env 第 115 行)
# API_BASE_URL=https://abc123.ngrok.io  # 被註解掉

# ECPay 嘗試呼叫的 webhook URL
ReturnURL: http://localhost:8000/api/webhooks/ecpay-auth
# ❌ ECPay 無法從外部訪問 localhost
```

## 解決方案

### 方案一：開發環境 - 使用 ngrok (推薦)

1. **安裝 ngrok**:
```bash
# macOS
brew install ngrok

# 其他平台
# 到 https://ngrok.com/ 下載
```

2. **啟動 ngrok 隧道**:
```bash
# 開啟新終端，在後端服務運行時執行
ngrok http 8000
```

3. **獲取公開 URL**:
```bash
# ngrok 會顯示類似這樣的 URL
https://abc123.ngrok-free.app -> http://localhost:8000
```

4. **更新 .env 配置**:
```bash
# 取消註解並更新為 ngrok URL
API_BASE_URL=https://abc123.ngrok-free.app
FRONTEND_URL=http://localhost:3000  # 保持前端為 localhost
```

5. **重啟後端服務**:
```bash
# 停止現有服務 (Ctrl+C)
# 重新啟動
make run-api
```

### 方案二：生產環境 - 使用實際域名

```bash
# 生產環境配置
API_BASE_URL=https://api.yourdomain.com
FRONTEND_URL=https://app.yourdomain.com
ECPAY_ENVIRONMENT=production
```

## 驗證修復

### 1. 檢查 ECPay 服務配置
運行以下腳本確認 URL 配置正確：

```python
from coaching_assistant.core.services.ecpay_service import ECPaySubscriptionService
from coaching_assistant.core.config import Settings

settings = Settings()
service = ECPaySubscriptionService(None, settings)

print("🔍 ECPay URL 配置檢查:")
print(f"API_BASE_URL: {settings.API_BASE_URL}")
print(f"FRONTEND_URL: {settings.FRONTEND_URL}")
print(f"ReturnURL: {settings.API_BASE_URL}/api/webhooks/ecpay-auth")
print(f"OrderResultURL: {settings.FRONTEND_URL}/api/subscription/result")
```

### 2. 測試 webhook 連通性
```bash
# 測試 ngrok URL 是否可訪問
curl https://your-ngrok-url.ngrok-free.app/api/webhooks/health

# 應該返回類似這樣的回應：
# {"status": "healthy", "service": "ecpay-webhooks", ...}
```

### 3. 建立新的測試訂閱
- 配置正確後，建立新的 ECPay 授權
- 檢查 webhook_logs 表是否收到回調
- 確認授權狀態從 `pending` 變為 `active`
- 驗證 saas_subscriptions 表是否創建記錄

### 4. 資料庫驗證查詢
```sql
-- 檢查 webhook 日誌
SELECT * FROM webhook_logs 
WHERE webhook_type = 'auth_callback' 
ORDER BY received_at DESC LIMIT 5;

-- 檢查授權狀態
SELECT merchant_member_id, auth_status, created_at, auth_date 
FROM ecpay_credit_authorizations 
ORDER BY created_at DESC LIMIT 5;

-- 檢查訂閱記錄
SELECT plan_id, status, created_at, start_date 
FROM saas_subscriptions 
ORDER BY created_at DESC LIMIT 5;
```

## 重要提醒

### ngrok 使用注意事項
1. **每次重啟 ngrok，URL 會改變** (免費版)
2. **需要更新 .env 中的 API_BASE_URL**
3. **重啟後端服務以載入新配置**
4. **付費版 ngrok 可以使用固定子域名**

### 安全考量
1. **僅在開發環境使用 ngrok**
2. **生產環境必須使用正式域名和 HTTPS**
3. **不要將 ngrok URL 提交到版本控制**

### 後續步驟
1. ✅ 修復 webhook URL 配置
2. 🧪 測試新的訂閱流程
3. 📋 處理現有的 `pending` 授權記錄
4. 🎯 驗證完整的訂閱→付款→升級流程

---

**修復完成後，ECPay 訂閱功能應該可以正常工作，用戶付款成功後會自動升級方案。**