# ECPay Webhook 管理員令牌使用指南

## 🔐 概述

`ADMIN_WEBHOOK_TOKEN` 是用來保護敏感 webhook 管理端點的安全令牌，確保只有授權的管理員能執行關鍵的付款系統操作。

## 🎯 保護的端點

### 1. 手動付款重試
```http
POST /api/webhooks/ecpay-manual-retry
Content-Type: application/x-www-form-urlencoded

payment_id=pay_123456789&admin_token=YOUR_ADMIN_TOKEN
```

**用途**: 當自動重試失敗時，手動觸發特定付款的重試
**使用場景**: 客服處理用戶付款問題

### 2. 訂閱狀態查詢
```http
GET /api/webhooks/subscription-status/{user_id}?admin_token=YOUR_ADMIN_TOKEN
```

**用途**: 查看特定用戶的詳細訂閱和 webhook 處理狀態
**使用場景**: 除錯付款問題，分析用戶付款歷史

### 3. 系統維護觸發
```http
POST /api/webhooks/trigger-maintenance
Content-Type: application/x-www-form-urlencoded

admin_token=YOUR_ADMIN_TOKEN&force=false
```

**用途**: 手動觸發訂閱維護任務（過期處理、重試等）
**使用場景**: 緊急維護，系統故障恢復

## ⚙️ 配置設定

### 開發環境
```bash
# .env 檔案
ADMIN_WEBHOOK_TOKEN=change-me-in-production
```

### 生產環境
```bash
# 使用強密碼（建議 32+ 字元）
ADMIN_WEBHOOK_TOKEN=kR9$xM2@nP5#wL8qF3vH6jB1cE4tY7uZ9sA0mT6
```

### Docker 部署
```yaml
# docker-compose.yml
services:
  api:
    environment:
      - ADMIN_WEBHOOK_TOKEN=${ADMIN_WEBHOOK_TOKEN}
```

### Render.com 部署
```bash
# 在 Render 環境變數中設定
ADMIN_WEBHOOK_TOKEN=YOUR_SECURE_TOKEN_HERE
```

## 🔧 實際使用範例

### 客服支援腳本
```bash
#!/bin/bash
# customer_support.sh

ADMIN_TOKEN="your-production-token"
API_BASE="https://api.coachly.tw"

# 查看用戶訂閱狀態
function check_user_subscription() {
    local user_id=$1
    curl -s "${API_BASE}/api/webhooks/subscription-status/${user_id}?admin_token=${ADMIN_TOKEN}" | jq '.'
}

# 手動重試付款
function retry_payment() {
    local payment_id=$1
    curl -X POST "${API_BASE}/api/webhooks/ecpay-manual-retry" \
         -F "payment_id=${payment_id}" \
         -F "admin_token=${ADMIN_TOKEN}"
}

# 使用範例
check_user_subscription "user_123456"
retry_payment "pay_789012"
```

### Python 管理腳本
```python
import requests
import os

class WebhookAdmin:
    def __init__(self):
        self.admin_token = os.getenv('ADMIN_WEBHOOK_TOKEN')
        self.api_base = 'https://api.coachly.tw'
    
    def check_subscription_status(self, user_id):
        """查看用戶訂閱狀態"""
        url = f"{self.api_base}/api/webhooks/subscription-status/{user_id}"
        params = {'admin_token': self.admin_token}
        
        response = requests.get(url, params=params)
        return response.json()
    
    def retry_payment(self, payment_id):
        """手動重試付款"""
        url = f"{self.api_base}/api/webhooks/ecpay-manual-retry"
        data = {
            'payment_id': payment_id,
            'admin_token': self.admin_token
        }
        
        response = requests.post(url, data=data)
        return response.json()
    
    def trigger_maintenance(self):
        """觸發系統維護"""
        url = f"{self.api_base}/api/webhooks/trigger-maintenance"
        data = {'admin_token': self.admin_token}
        
        response = requests.post(url, data=data)
        return response.json()

# 使用範例
admin = WebhookAdmin()
status = admin.check_subscription_status('user_123456')
print(f"用戶狀態: {status}")
```

## 📊 監控儀表板整合

### Grafana 查詢範例
```bash
# 監控腳本：檢查系統健康狀況
#!/bin/bash

ADMIN_TOKEN="${ADMIN_WEBHOOK_TOKEN}"
API_BASE="https://api.coachly.tw"

# 獲取系統統計
maintenance_stats=$(curl -s -X POST "${API_BASE}/api/webhooks/trigger-maintenance" \
    -F "admin_token=${ADMIN_TOKEN}" | jq '.results')

echo "Current active subscriptions: $(echo $maintenance_stats | jq '.current_active_subscriptions')"
echo "Past due subscriptions: $(echo $maintenance_stats | jq '.current_past_due_subscriptions')"
```

## 🔒 安全最佳實踐

### ✅ 安全的 Token 設定
```bash
# 好的範例 - 32+ 字元，混合字符
ADMIN_WEBHOOK_TOKEN="A7kR$mX9#pL2@vF5wN8qJ3cE6tH1yU4zB0sG9iM"

# 使用密碼生成器
openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
```

### ❌ 避免的設定
```bash
# 太簡單
ADMIN_WEBHOOK_TOKEN="admin123"

# 太短
ADMIN_WEBHOOK_TOKEN="abc123"

# 沒有特殊字符
ADMIN_WEBHOOK_TOKEN="adminpassword123"
```

### 🛡️ 存儲安全
1. **使用環境變數**：不要寫在程式碼中
2. **定期更換**：建議每 3-6 個月更換
3. **限制存取**：只有必要的管理員知道
4. **審計日誌**：記錄所有使用 admin token 的操作

## 🚨 故障排除

### 常見錯誤

#### 401 Unauthorized
```json
{
    "detail": "Unauthorized"
}
```
**解決方案**: 檢查 `ADMIN_WEBHOOK_TOKEN` 環境變數設定

#### 404 Not Found
```bash
# 檢查端點路徑是否正確
curl https://api.coachly.tw/api/webhooks/health  # 測試基本連線
```

#### Token 不匹配
```bash
# 檢查環境變數
echo $ADMIN_WEBHOOK_TOKEN

# 檢查 API 伺服器日誌
docker logs api-server | grep "Unauthorized manual retry"
```

### 除錯工具
```bash
# 測試 token 是否有效
function test_admin_token() {
    local token=$1
    curl -s -X POST "https://api.coachly.tw/api/webhooks/trigger-maintenance" \
         -F "admin_token=${token}" \
         -w "%{http_code}\n" -o /dev/null
}

# 使用
test_admin_token "your-token-here"
# 回傳 200 = 成功, 401 = token 無效
```

## 📝 操作日誌

所有使用 admin token 的操作都會記錄在系統日誌中：

```
🔧 Manual payment retry requested for payment pay_123456
🚨 Unauthorized manual retry attempt from 192.168.1.100
✅ Manual maintenance completed: {"expired_subscriptions_processed": 0, "payment_retries_processed": 2}
```

這些日誌可用於安全審計和故障排除。

## 🔄 Token 更換程序

1. **生成新 Token**
   ```bash
   openssl rand -base64 32 | tr -d "=+/" | cut -c1-32
   ```

2. **更新環境變數**
   - 開發環境：更新 `.env` 檔案
   - 生產環境：更新 Render/Docker 環境變數

3. **重啟服務**
   - 確保新 token 生效

4. **更新管理腳本**
   - 更新所有使用舊 token 的腳本和工具

5. **驗證功能**
   - 測試所有管理端點是否正常工作

通過適當的 token 管理，可以確保 ECPay webhook 系統的安全性和可管理性。