# Security Considerations for Test Mode

## ⚠️ 重要安全警告 (Critical Security Warnings)

### 🚨 絕對不可在生產環境中啟用測試模式

測試模式會完全跳過認證機制，這在生產環境中會造成嚴重的安全漏洞：

**Test Mode completely bypasses authentication mechanisms, which creates serious security vulnerabilities in production environments:**

- **資料外洩風險**: 任何人都可以存取所有用戶資料
- **未授權操作**: 攻擊者可以執行任意的 API 操作
- **資料完整性威脅**: 可能遭受資料竄改或刪除
- **合規性問題**: 違反 GDPR、CCPA 等資料保護法規

## 內建安全保護機制 (Built-in Security Protections)

### 1. 環境檢查保護
系統會自動檢查並阻止在生產環境中啟用測試模式：

```python
@field_validator("TEST_MODE")
@classmethod
def validate_test_mode(cls, value: bool, values) -> bool:
    environment = os.getenv("ENVIRONMENT", "development")
    if value is True and environment == "production":
        raise ValueError(
            "TEST_MODE 不可在生產環境中啟用！這會造成嚴重的安全漏洞。"
        )
    return value
```

### 2. 日誌警告機制
當測試模式啟用時，系統會持續記錄警告訊息：

```
WARNING - 🚨 TEST_MODE 已啟用 - 跳過認證檢查，使用測試用戶
```

### 3. 配置驗證
應用程式啟動時會驗證所有安全相關配置。

## 安全最佳實踐 (Security Best Practices)

### 1. 環境隔離

#### 開發環境 (Development)
```env
ENVIRONMENT=development
TEST_MODE=true  # ✅ 安全
DATABASE_URL=postgresql://localhost:5432/coaching_dev
```

#### 測試環境 (Testing)
```env
ENVIRONMENT=testing
TEST_MODE=true  # ✅ 安全
DATABASE_URL=postgresql://localhost:5432/coaching_test
```

#### 預發布環境 (Staging)
```env
ENVIRONMENT=staging
TEST_MODE=false  # ⚠️ 建議禁用，測試完整認證流程
DATABASE_URL=postgresql://staging-db:5432/coaching_staging
```

#### 生產環境 (Production)
```env
ENVIRONMENT=production
TEST_MODE=false  # 🔒 強制禁用
DATABASE_URL=postgresql://prod-db:5432/coaching_prod
```

### 2. 資料庫隔離策略

#### 使用獨立的測試資料庫
```bash
# 開發環境
DATABASE_URL=postgresql://dev_user:dev_pass@localhost:5432/coaching_dev

# 測試環境
DATABASE_URL=postgresql://test_user:test_pass@localhost:5432/coaching_test

# 生產環境
DATABASE_URL=postgresql://prod_user:secure_pass@prod-db:5432/coaching_prod
```

#### 測試資料生命週期管理
```python
# 測試前清理
def setup_test_data():
    """建立乾淨的測試環境"""
    if settings.TEST_MODE:
        # 清理測試資料
        cleanup_test_data()
        # 建立必要的測試資料
        create_test_fixtures()

def cleanup_test_data():
    """清理測試資料"""
    if settings.TEST_MODE and settings.ENVIRONMENT != "production":
        # 安全清理邏輯
        pass
```

### 3. 存取控制與監控

#### 網路層面保護
```nginx
# nginx 配置範例
server {
    listen 80;
    server_name api-dev.example.com;

    # 限制存取來源
    allow 192.168.1.0/24;  # 開發團隊網路
    allow 10.0.0.0/8;      # 內部網路
    deny all;

    location / {
        proxy_pass http://localhost:8000;
    }
}
```

#### 防火牆規則
```bash
# iptables 規則範例
# 只允許特定 IP 存取測試環境
iptables -A INPUT -p tcp --dport 8000 -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j DROP
```

### 4. 環境變數安全管理

#### 使用配置管理工具
```yaml
# Docker Compose 範例
version: '3.8'
services:
  api-dev:
    image: coaching-api:dev
    environment:
      - TEST_MODE=true
      - ENVIRONMENT=development
    networks:
      - dev-network

  api-staging:
    image: coaching-api:staging
    environment:
      - TEST_MODE=false
      - ENVIRONMENT=staging
    networks:
      - staging-network
```

#### Kubernetes 配置
```yaml
# development-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config-dev
data:
  TEST_MODE: "true"
  ENVIRONMENT: "development"

---
# production-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: api-config-prod
data:
  TEST_MODE: "false"
  ENVIRONMENT: "production"
```

## 監控與審計 (Monitoring and Auditing)

### 1. 安全監控指標

#### 關鍵監控點
- 測試模式啟用狀態
- 測試用戶存取頻率
- 異常 API 呼叫模式
- 環境配置變更

#### Prometheus 監控範例
```python
from prometheus_client import Counter, Gauge

# 監控指標
test_mode_access_counter = Counter(
    'test_mode_api_calls_total',
    'Total API calls in test mode',
    ['endpoint', 'method']
)

test_mode_enabled_gauge = Gauge(
    'test_mode_enabled',
    'Whether test mode is currently enabled'
)

# 在認證函數中記錄
if settings.TEST_MODE:
    test_mode_enabled_gauge.set(1)
    test_mode_access_counter.labels(
        endpoint=request.url.path,
        method=request.method
    ).inc()
```

### 2. 日誌審計

#### 結構化日誌記錄
```python
import structlog

logger = structlog.get_logger()

def log_test_mode_access(request, user):
    """記錄測試模式存取"""
    if settings.TEST_MODE:
        logger.warning(
            "test_mode_access",
            user_id=user.id,
            endpoint=request.url.path,
            method=request.method,
            client_ip=request.client.host,
            timestamp=datetime.utcnow().isoformat(),
            environment=settings.ENVIRONMENT
        )
```

#### 安全事件警報
```python
def check_security_violations():
    """檢查安全違規事件"""
    if settings.TEST_MODE and settings.ENVIRONMENT == "production":
        # 這不應該發生，因為有驗證機制
        logger.critical(
            "SECURITY_VIOLATION",
            event="test_mode_in_production",
            action="immediate_investigation_required"
        )
        # 發送緊急警報
        send_security_alert("Test mode enabled in production!")
```

## 合規性考慮 (Compliance Considerations)

### 1. 資料保護法規 (GDPR/CCPA)

#### 資料處理原則
- **目的限制**: 測試模式只能用於開發和測試目的
- **資料最小化**: 使用模擬或匿名化的測試資料
- **儲存期限**: 自動清理測試資料

#### 實施建議
```python
class TestDataManager:
    """測試資料管理器"""

    def create_anonymized_test_data(self):
        """建立匿名化測試資料"""
        if settings.TEST_MODE:
            # 使用假資料而非真實用戶資料
            return {
                "email": "test@example.com",
                "name": "Test User",
                "phone": "+1234567890"  # 非真實電話
            }

    def cleanup_expired_test_data(self):
        """清理過期測試資料"""
        if settings.TEST_MODE:
            # 自動清理超過 24 小時的測試資料
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            # 實施清理邏輯
```

### 2. 稽核要求

#### 存取記錄
```python
class AuditLogger:
    """稽核日誌記錄器"""

    def log_api_access(self, user, action, resource):
        """記錄 API 存取"""
        audit_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user.id if user else "anonymous",
            "action": action,
            "resource": resource,
            "test_mode": settings.TEST_MODE,
            "environment": settings.ENVIRONMENT
        }
        # 儲存到稽核日誌
        self.store_audit_record(audit_record)
```

## 部署安全檢查清單 (Deployment Security Checklist)

### 部署前檢查 (Pre-deployment Checks)

- [ ] **環境配置驗證**
  - [ ] `ENVIRONMENT` 設定正確
  - [ ] 生產環境中 `TEST_MODE=false`
  - [ ] 資料庫 URL 指向正確環境

- [ ] **網路安全**
  - [ ] 防火牆規則已設定
  - [ ] 存取控制清單已更新
  - [ ] SSL/TLS 憑證有效

- [ ] **監控設定**
  - [ ] 安全監控已啟用
  - [ ] 警報機制已設定
  - [ ] 日誌收集正常運作

- [ ] **資料保護**
  - [ ] 資料備份策略已實施
  - [ ] 敏感資料已加密
  - [ ] 存取權限已審查

### 部署後驗證 (Post-deployment Verification)

```bash
#!/bin/bash
# 安全驗證腳本

echo "🔍 檢查生產環境安全設定..."

# 1. 檢查測試模式狀態
response=$(curl -s http://your-api.com/health)
if echo "$response" | grep -q "test_mode.*true"; then
    echo "❌ 危險：生產環境中檢測到測試模式！"
    exit 1
else
    echo "✅ 測試模式已正確禁用"
fi

# 2. 檢查認證要求
auth_response=$(curl -s -o /dev/null -w "%{http_code}" http://your-api.com/api/v1/auth/me)
if [ "$auth_response" = "401" ]; then
    echo "✅ 認證要求正常"
else
    echo "❌ 警告：API 可能不需要認證！"
    exit 1
fi

# 3. 檢查環境標識
env_response=$(curl -s http://your-api.com/health)
if echo "$env_response" | grep -q "environment.*production"; then
    echo "✅ 環境標識正確"
else
    echo "⚠️  環境標識可能不正確"
fi

echo "🔒 安全檢查完成"
```

## 事件回應計畫 (Incident Response Plan)

### 1. 安全事件分類

#### 高危事件 (High Severity)
- 生產環境中檢測到測試模式
- 未授權存取敏感資料
- 資料外洩或竄改

#### 中危事件 (Medium Severity)
- 預發布環境中的異常存取
- 配置錯誤導致的安全風險
- 監控系統異常

#### 低危事件 (Low Severity)
- 開發環境中的異常活動
- 日誌異常但無安全影響
- 效能問題

### 2. 回應程序

#### 立即行動 (Immediate Actions)
1. **隔離受影響系統**
2. **禁用測試模式** (如果誤啟用)
3. **收集事件證據**
4. **通知安全團隊**

#### 調查與修復 (Investigation & Remediation)
1. **根因分析**
2. **影響評估**
3. **修復措施實施**
4. **系統恢復驗證**

#### 事後處理 (Post-incident)
1. **事件報告撰寫**
2. **流程改進建議**
3. **團隊培訓更新**
4. **監控機制優化**

## 團隊培訓與意識 (Team Training & Awareness)

### 1. 開發團隊培訓內容

#### 基本安全意識
- 測試模式的用途和風險
- 環境隔離的重要性
- 安全配置最佳實踐

#### 實務操作訓練
- 正確的測試模式使用方法
- 安全的部署流程
- 事件回應程序

### 2. 定期安全審查

#### 月度檢查項目
- [ ] 環境配置審查
- [ ] 存取日誌分析
- [ ] 安全政策更新
- [ ] 團隊培訓評估

#### 季度深度審查
- [ ] 安全架構評估
- [ ] 威脅模型更新
- [ ] 合規性檢查
- [ ] 災難恢復測試

通過遵循這些安全考慮和最佳實踐，可以確保測試模式在提供開發便利性的同時，不會對系統安全造成威脅。