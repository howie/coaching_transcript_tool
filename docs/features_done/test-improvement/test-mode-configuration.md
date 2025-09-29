# Test Mode Configuration Guide

## 環境變數配置 (Environment Variable Configuration)

### TEST_MODE

**類型**: Boolean
**預設值**: `false`
**必須**: 否
**說明**: 啟用測試模式，跳過所有 API 認證檢查

```bash
# 啟用測試模式
TEST_MODE=true

# 禁用測試模式 (預設)
TEST_MODE=false
```

## 配置方法 (Configuration Methods)

### 1. 環境變數設定 (Environment Variables)

#### Linux/macOS
```bash
export TEST_MODE=true
export ENVIRONMENT=development
```

#### Windows (PowerShell)
```powershell
$env:TEST_MODE = "true"
$env:ENVIRONMENT = "development"
```

#### Windows (Command Prompt)
```cmd
set TEST_MODE=true
set ENVIRONMENT=development
```

### 2. .env 檔案配置

在專案根目錄創建或編輯 `.env` 檔案：

```env
# 測試模式配置
TEST_MODE=true
ENVIRONMENT=development

# 其他必要配置
DATABASE_URL=postgresql://user:pass@localhost:5432/coaching_dev
STT_PROVIDER=google
SECRET_KEY=your-secret-key-here
```

### 3. Docker 環境配置

#### docker-compose.yml
```yaml
version: '3.8'
services:
  api:
    build: .
    environment:
      - TEST_MODE=true
      - ENVIRONMENT=development
      - DATABASE_URL=postgresql://user:pass@db:5432/coaching_dev
    ports:
      - "8000:8000"
```

#### Dockerfile
```dockerfile
ENV TEST_MODE=true
ENV ENVIRONMENT=development
```

## 配置驗證 (Configuration Validation)

### 自動驗證機制

系統會在啟動時自動驗證配置：

1. **生產環境保護**: 如果 `ENVIRONMENT=production` 且 `TEST_MODE=true`，系統會拋出錯誤
2. **配置檢查**: 系統會記錄當前配置狀態到日誌
3. **測試用戶創建**: 自動創建或查找測試用戶

### 驗證配置是否生效

#### 檢查系統日誌
```bash
# 啟動服務並檢查日誌
TEST_MODE=true uv run python apps/api-server/main.py

# 應該看到類似日誌：
# WARNING - 🚨 TEST_MODE 已啟用 - 跳過認證檢查，使用測試用戶
```

#### API 測試驗證
```bash
# 測試無認證訪問
curl http://localhost:8000/api/v1/auth/me

# 成功回應表示測試模式已啟用：
{
  "id": "...",
  "email": "test@example.com",
  "name": "Test User",
  "plan": "PRO"
}
```

## 不同環境的配置 (Configuration for Different Environments)

### 開發環境 (Development)
```env
ENVIRONMENT=development
TEST_MODE=true
DEBUG=true
DATABASE_URL=postgresql://user:pass@localhost:5432/coaching_dev
```

### 測試環境 (Testing)
```env
ENVIRONMENT=testing
TEST_MODE=true
DEBUG=false
DATABASE_URL=postgresql://user:pass@localhost:5432/coaching_test
```

### 預發布環境 (Staging)
```env
ENVIRONMENT=staging
TEST_MODE=false  # 建議在預發布環境測試完整認證流程
DEBUG=false
DATABASE_URL=postgresql://user:pass@staging-db:5432/coaching_staging
```

### 生產環境 (Production)
```env
ENVIRONMENT=production
TEST_MODE=false  # 強制禁用，系統會自動驗證
DEBUG=false
DATABASE_URL=postgresql://user:pass@prod-db:5432/coaching_prod
```

## CI/CD 配置範例 (CI/CD Configuration Examples)

### GitHub Actions
```yaml
name: API Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    env:
      TEST_MODE: true
      ENVIRONMENT: testing
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db

    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          pip install uv
          uv sync

      - name: Run API tests
        run: |
          TEST_MODE=true uv run pytest tests/api/
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    environment {
        TEST_MODE = 'true'
        ENVIRONMENT = 'testing'
        DATABASE_URL = 'postgresql://user:pass@localhost:5432/test_db'
    }

    stages {
        stage('Test APIs') {
            steps {
                sh 'TEST_MODE=true uv run pytest tests/api/'
            }
        }
    }
}
```

## 故障排除 (Troubleshooting)

### 常見問題

#### 1. 測試模式未啟用
**問題**: API 仍然要求認證
**解決方案**:
```bash
# 檢查環境變數
echo $TEST_MODE

# 確認配置載入
grep TEST_MODE .env

# 重啟服務
TEST_MODE=true uv run python apps/api-server/main.py
```

#### 2. 生產環境錯誤
**問題**: `ValueError: TEST_MODE 不可在生產環境中啟用！`
**解決方案**:
```bash
# 檢查環境設定
echo $ENVIRONMENT

# 確保在非生產環境
export ENVIRONMENT=development
export TEST_MODE=true
```

#### 3. 測試用戶創建失敗
**問題**: 無法創建測試用戶
**解決方案**:
```bash
# 檢查資料庫連線
psql $DATABASE_URL -c "SELECT 1;"

# 檢查資料庫權限
# 確保應用程式可以創建用戶記錄
```

#### 4. 日誌未顯示測試模式警告
**問題**: 沒有看到測試模式啟用的日誌
**解決方案**:
```bash
# 檢查日誌級別
export LOG_LEVEL=DEBUG

# 重啟並檢查完整日誌
TEST_MODE=true uv run python apps/api-server/main.py 2>&1 | grep TEST_MODE
```

## 最佳實踐 (Best Practices)

### 1. 環境隔離
- 為每個環境使用獨立的資料庫
- 使用不同的配置檔案
- 避免在預發布環境啟用測試模式

### 2. 安全性
- 定期檢查生產環境配置
- 使用配置管理工具
- 實施配置變更審核流程

### 3. 測試策略
- 在測試環境同時測試認證和非認證模式
- 使用測試模式進行快速迭代
- 在 CI/CD 中自動驗證配置

### 4. 監控
- 監控測試模式的使用情況
- 設定警報檢測意外啟用
- 記錄配置變更歷史

## 相關配置參數 (Related Configuration Parameters)

測試模式可能與以下配置參數相關：

```env
# 認證相關
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 資料庫相關
DATABASE_URL=postgresql://...

# 日誌相關
LOG_LEVEL=INFO
LOG_FORMAT=json

# 環境相關
ENVIRONMENT=development
DEBUG=true
```