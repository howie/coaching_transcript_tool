# API Testing Guide with Test Mode

## 簡介 (Introduction)

本指南詳細說明如何使用測試模式來測試 Coaching Assistant Platform 的各種 API 端點。測試模式消除了認證的複雜性，讓您可以專注於測試 API 的核心功能。

This guide provides detailed instructions on how to use Test Mode to test various API endpoints of the Coaching Assistant Platform. Test Mode eliminates authentication complexity, allowing you to focus on testing core API functionality.

## 前置準備 (Prerequisites)

### 1. 啟動測試模式
```bash
export TEST_MODE=true
export ENVIRONMENT=development
```

### 2. 啟動 API 伺服器
```bash
TEST_MODE=true uv run python apps/api-server/main.py
```

### 3. 驗證測試模式已啟用
```bash
curl http://localhost:8000/api/v1/auth/me

# 應該回傳測試用戶資訊，無需認證
```

## API 端點測試 (API Endpoint Testing)

### 認證相關 API (Authentication APIs)

#### GET /api/v1/auth/me
獲取當前用戶資訊
```bash
curl -X GET http://localhost:8000/api/v1/auth/me

# 預期回應
{
  "id": "test-user-uuid",
  "email": "test@example.com",
  "name": "Test User",
  "plan": "PRO",
  "auth_provider": null,
  "google_connected": null,
  "preferences": null
}
```

### 會話管理 API (Session Management APIs)

#### POST /api/v1/sessions
創建新的轉錄會話
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "audio_language": "zh-TW",
    "stt_provider": "google",
    "title": "測試會話",
    "description": "API 測試用會話"
  }'

# 預期回應
{
  "id": "session-uuid",
  "title": "測試會話",
  "description": "API 測試用會話",
  "status": "created",
  "audio_language": "zh-TW",
  "stt_provider": "google",
  "created_at": "2025-01-17T10:00:00Z"
}
```

#### GET /api/v1/sessions
獲取用戶的會話列表
```bash
curl -X GET http://localhost:8000/api/v1/sessions

# 預期回應
{
  "sessions": [
    {
      "id": "session-uuid",
      "title": "測試會話",
      "status": "created",
      "created_at": "2025-01-17T10:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "size": 20
}
```

#### GET /api/v1/sessions/{session_id}
獲取特定會話詳情
```bash
SESSION_ID="your-session-id"
curl -X GET "http://localhost:8000/api/v1/sessions/${SESSION_ID}"

# 預期回應
{
  "id": "session-uuid",
  "title": "測試會話",
  "description": "API 測試用會話",
  "status": "created",
  "audio_language": "zh-TW",
  "stt_provider": "google",
  "transcript_segments": [],
  "speaker_roles": {},
  "created_at": "2025-01-17T10:00:00Z"
}
```

#### POST /api/v1/sessions/{session_id}/upload-url
獲取音檔上傳 URL
```bash
SESSION_ID="your-session-id"
curl -X POST "http://localhost:8000/api/v1/sessions/${SESSION_ID}/upload-url" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test-audio.mp3",
    "content_type": "audio/mpeg"
  }'

# 預期回應
{
  "upload_url": "https://storage.googleapis.com/...",
  "expires_at": "2025-01-17T11:00:00Z"
}
```

### 方案管理 API (Plan Management APIs)

#### GET /api/v1/plans/current
獲取當前用戶方案
```bash
curl -X GET http://localhost:8000/api/v1/plans/current

# 預期回應
{
  "currentPlan": {
    "id": "PRO",
    "display_name": "專業方案",
    "monthly_price": 990,
    "annual_price": 9900,
    "features": {
      "max_file_size_mb": 200,
      "max_session_duration_minutes": 180,
      "monthly_usage_limit": 1000
    }
  },
  "usageStatus": {
    "plan": "PRO",
    "currentUsage": 0,
    "planLimits": {
      "maxFileSizeMB": 200,
      "maxSessionDurationMinutes": 180,
      "monthlyUsageLimit": 1000
    }
  }
}
```

### 客戶管理 API (Client Management APIs)

#### GET /api/v1/clients/options/sources
獲取客戶來源選項
```bash
curl -X GET http://localhost:8000/api/v1/clients/options/sources

# 預期回應
[
  {"value":"referral","labelKey":"clients.sourceReferral"},
  {"value":"organic","labelKey":"clients.sourceOrganic"},
  {"value":"friend","labelKey":"clients.sourceFriend"},
  {"value":"social_media","labelKey":"clients.sourceSocialMedia"}
]
```

#### GET /api/v1/clients/options/types
獲取客戶類型選項
```bash
curl -X GET http://localhost:8000/api/v1/clients/options/types

# 預期回應
[
  {"value":"paid","labelKey":"clients.typePaid"},
  {"value":"pro_bono","labelKey":"clients.typeProBono"},
  {"value":"free_practice","labelKey":"clients.typeFreePractice"},
  {"value":"other","labelKey":"clients.typeOther"}
]
```

#### GET /api/v1/clients/options/statuses
獲取客戶狀態選項
```bash
curl -X GET http://localhost:8000/api/v1/clients/options/statuses

# 預期回應
[
  {"value":"first_session","label":"首次會談"},
  {"value":"in_progress","label":"進行中"},
  {"value":"paused","label":"暫停"},
  {"value":"completed","label":"結案"}
]
```

#### GET /api/v1/clients
獲取客戶列表 (需要認證，在 TEST_MODE 下自動通過)
```bash
curl -X GET http://localhost:8000/api/v1/clients

# 預期回應
{
  "items": [
    {
      "id": "client-uuid",
      "name": "客戶姓名",
      "email": "client@example.com",
      "source": "referral",
      "client_type": "paid",
      "status": "in_progress",
      "session_count": 0,
      "created_at": "2025-09-21T08:58:38.614545"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

#### POST /api/v1/clients
創建新客戶 (需要認證，在 TEST_MODE 下自動通過)
```bash
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "新客戶",
    "email": "new@example.com",
    "source": "referral",
    "client_type": "paid",
    "status": "first_session"
  }'

# 預期回應
{
  "id": "new-client-uuid",
  "name": "新客戶",
  "email": "new@example.com",
  "source": "referral",
  "client_type": "paid",
  "status": "first_session",
  "session_count": 0,
  "created_at": "2025-09-21T08:58:38.614545"
}
```

### 使用統計 API (Usage Analytics APIs)

#### GET /api/v1/usage
獲取用戶使用統計
```bash
curl -X GET http://localhost:8000/api/v1/usage

# 預期回應
{
  "current_month": {
    "sessions_count": 5,
    "total_duration_minutes": 120,
    "total_file_size_mb": 45.6
  },
  "limits": {
    "max_file_size_mb": 200,
    "monthly_usage_limit": 1000
  },
  "usage_percentage": 12.0
}
```

#### GET /api/v1/usage/history
獲取使用歷史記錄
```bash
curl -X GET "http://localhost:8000/api/v1/usage/history?period=monthly&limit=6"

# 預期回應
{
  "history": [
    {
      "period": "2025-01",
      "sessions_count": 5,
      "total_duration_minutes": 120,
      "total_file_size_mb": 45.6
    }
  ]
}
```

### 說話者角色管理 API (Speaker Role APIs)

#### PATCH /api/v1/sessions/{session_id}/speaker-roles
更新會話中的說話者角色
```bash
SESSION_ID="your-session-id"
curl -X PATCH "http://localhost:8000/api/v1/sessions/${SESSION_ID}/speaker-roles" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker_roles": {
      "speaker_1": "教練",
      "speaker_2": "客戶"
    }
  }'

# 預期回應
{
  "message": "Speaker roles updated successfully",
  "speaker_roles": {
    "speaker_1": "教練",
    "speaker_2": "客戶"
  }
}
```

## 進階測試場景 (Advanced Testing Scenarios)

### 1. 完整會話工作流程測試
```bash
#!/bin/bash
# 測試完整的會話工作流程

echo "1. 創建會話..."
SESSION_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "audio_language": "zh-TW",
    "stt_provider": "google",
    "title": "工作流程測試"
  }')

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.id')
echo "會話 ID: $SESSION_ID"

echo "2. 獲取上傳 URL..."
curl -s -X POST "http://localhost:8000/api/v1/sessions/${SESSION_ID}/upload-url" \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "test.mp3",
    "content_type": "audio/mpeg"
  }'

echo "3. 檢查會話狀態..."
curl -s -X GET "http://localhost:8000/api/v1/sessions/${SESSION_ID}"

echo "4. 更新說話者角色..."
curl -s -X PATCH "http://localhost:8000/api/v1/sessions/${SESSION_ID}/speaker-roles" \
  -H "Content-Type: application/json" \
  -d '{
    "speaker_roles": {
      "speaker_1": "教練",
      "speaker_2": "客戶"
    }
  }'
```

### 2. 批量測試腳本
```bash
#!/bin/bash
# 批量測試所有 API 端點

# 定義測試端點
ENDPOINTS=(
  "GET /api/v1/auth/me"
  "GET /api/v1/sessions"
  "GET /api/v1/plans/current"
  "GET /api/v1/usage"
  "GET /api/v1/usage/history"
)

BASE_URL="http://localhost:8000"

for endpoint in "${ENDPOINTS[@]}"; do
  method=$(echo $endpoint | cut -d' ' -f1)
  path=$(echo $endpoint | cut -d' ' -f2)

  echo "測試: $method $path"
  response=$(curl -s -X $method "$BASE_URL$path")
  status=$?

  if [ $status -eq 0 ]; then
    echo "✅ 成功"
  else
    echo "❌ 失敗"
  fi
  echo "---"
done
```

### 3. 錯誤處理測試
```bash
# 測試不存在的會話
curl -X GET http://localhost:8000/api/v1/sessions/non-existent-id

# 測試無效的資料格式
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# 測試大檔案上傳限制
curl -X POST http://localhost:8000/api/v1/sessions/test-id/upload-url \
  -H "Content-Type: application/json" \
  -d '{
    "filename": "huge-file.mp3",
    "content_type": "audio/mpeg",
    "file_size": 1000000000
  }'
```

## 自動化測試整合 (Automated Testing Integration)

### Python 測試腳本範例
```python
import requests
import pytest

BASE_URL = "http://localhost:8000"

class TestAPIWithTestMode:
    def setup_method(self):
        """每個測試方法前的設置"""
        # 驗證測試模式已啟用
        response = requests.get(f"{BASE_URL}/api/v1/auth/me")
        assert response.status_code == 200
        assert response.json()["email"] == "test@example.com"

    def test_get_current_user(self):
        """測試獲取當前用戶"""
        response = requests.get(f"{BASE_URL}/api/v1/auth/me")
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["plan"] == "PRO"

    def test_create_session(self):
        """測試創建會話"""
        payload = {
            "audio_language": "zh-TW",
            "stt_provider": "google",
            "title": "自動化測試會話"
        }

        response = requests.post(f"{BASE_URL}/api/v1/sessions", json=payload)
        assert response.status_code == 201

        data = response.json()
        assert data["title"] == "自動化測試會話"
        assert data["audio_language"] == "zh-TW"

    def test_get_current_plan(self):
        """測試獲取當前方案"""
        response = requests.get(f"{BASE_URL}/api/v1/plans/current")
        assert response.status_code == 200

        data = response.json()
        assert "currentPlan" in data
        assert "usageStatus" in data
```

### JavaScript/Node.js 測試範例
```javascript
const axios = require('axios');

const BASE_URL = 'http://localhost:8000';

describe('API Tests with Test Mode', () => {
  beforeEach(async () => {
    // 驗證測試模式已啟用
    const response = await axios.get(`${BASE_URL}/api/v1/auth/me`);
    expect(response.status).toBe(200);
    expect(response.data.email).toBe('test@example.com');
  });

  test('should get current user', async () => {
    const response = await axios.get(`${BASE_URL}/api/v1/auth/me`);

    expect(response.status).toBe(200);
    expect(response.data.email).toBe('test@example.com');
    expect(response.data.plan).toBe('PRO');
  });

  test('should create session', async () => {
    const payload = {
      audio_language: 'zh-TW',
      stt_provider: 'google',
      title: 'JS 自動化測試會話'
    };

    const response = await axios.post(`${BASE_URL}/api/v1/sessions`, payload);

    expect(response.status).toBe(201);
    expect(response.data.title).toBe('JS 自動化測試會話');
  });
});
```

## 效能測試 (Performance Testing)

### 使用 Apache Bench (ab)
```bash
# 測試單一端點效能
ab -n 100 -c 10 http://localhost:8000/api/v1/auth/me

# 測試會話列表端點
ab -n 50 -c 5 http://localhost:8000/api/v1/sessions
```

### 使用 wrk
```bash
# 基本效能測試
wrk -t12 -c400 -d30s http://localhost:8000/api/v1/auth/me

# 帶 JSON payload 的 POST 測試
wrk -t12 -c400 -d30s -s post-session.lua http://localhost:8000/api/v1/sessions
```

## Clean Architecture 遷移驗證 (Clean Architecture Migration Verification)

### 遷移測試標準流程

當完成任何模組的 Clean Architecture 遷移後，必須按照以下標準流程驗證遷移成功：

#### 1. 環境設置驗證
```bash
# 確認 .env 配置正確
grep -E "(TEST_MODE|RECAPTCHA_ENABLED)" .env

# 應顯示：
# TEST_MODE=true
# RECAPTCHA_ENABLED=false
```

#### 2. 伺服器啟動驗證
```bash
# 啟動測試伺服器
uv run python apps/api-server/main.py

# 確認看到以下訊息：
# - ✅ All environment variables validated successfully!
# - INFO: Uvicorn running on http://0.0.0.0:8000
# - INFO: Application startup complete.
```

#### 3. TEST_MODE 功能驗證
```bash
# 測試需要認證的端點，確認 TEST_MODE 生效
curl -X GET http://localhost:8000/api/v1/clients

# 檢查伺服器日誌，應看到：
# [WARNING] 🚨 TEST_MODE 已啟用 - 跳過認證檢查，使用測試用戶
```

#### 4. 遷移後端點測試

##### 4.1 靜態端點測試 (不需認證)
```bash
# 測試所有 options 端點
curl -X GET http://localhost:8000/api/v1/clients/options/sources
curl -X GET http://localhost:8000/api/v1/clients/options/types
curl -X GET http://localhost:8000/api/v1/clients/options/statuses

# 驗證：
# - 所有端點返回 200 OK
# - 回應格式正確 (JSON array)
# - 內容符合預期
```

##### 4.2 動態端點測試 (需認證，TEST_MODE 下自動通過)
```bash
# 測試讀取操作
curl -X GET http://localhost:8000/api/v1/clients

# 測試寫入操作
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Clean Architecture Test Client",
    "email": "clean@example.com",
    "source": "referral",
    "client_type": "paid",
    "status": "first_session"
  }'

# 驗證：
# - GET 請求返回 200 OK 和正確資料格式
# - POST 請求返回 201 Created 和新創建的記錄
# - 伺服器日誌顯示 TEST_MODE 警告訊息
# - 資料庫操作正常執行 (可從 SQL 日誌確認)
```

#### 5. 資料庫操作驗證
```bash
# 檢查伺服器日誌中的 SQL 執行記錄
# 應看到類似以下內容：
# - SELECT 查詢用於讀取操作
# - INSERT 查詢用於創建操作
# - 操作成功完成 (無 ERROR 訊息)
```

#### 6. 錯誤處理驗證
```bash
# 測試無效資料處理
curl -X POST http://localhost:8000/api/v1/clients \
  -H "Content-Type: application/json" \
  -d '{"invalid": "data"}'

# 驗證：
# - 返回適當的錯誤狀態碼 (400 或 422)
# - 錯誤訊息清楚明確
# - 不會導致伺服器崩潰
```

### 遷移驗證檢查清單

#### ✅ 必須驗證項目

- [ ] **環境配置**: TEST_MODE=true, RECAPTCHA_ENABLED=false
- [ ] **伺服器啟動**: 無錯誤訊息，正常監聽 8000 端口
- [ ] **TEST_MODE 生效**: 認證端點顯示跳過認證警告
- [ ] **靜態端點**: 所有 options 端點返回正確資料
- [ ] **動態端點**: 讀取和寫入操作正常工作
- [ ] **資料庫操作**: SQL 查詢正常執行
- [ ] **錯誤處理**: 無效請求得到適當處理
- [ ] **日誌品質**: 無 ERROR 或 EXCEPTION 訊息

#### 🔍 Clean Architecture 特有檢查

- [ ] **依賴注入**: 使用正確的 Factory 模式創建 use case
- [ ] **Repository 模式**: 資料存取通過 repository 介面
- [ ] **Use Case 執行**: 業務邏輯在 use case 層執行
- [ ] **錯誤處理**: 異常正確向上傳播並處理
- [ ] **測試用戶**: TEST_MODE 下創建和使用測試用戶

### 常見遷移問題與解決方案

#### 問題 1: 認證失敗 (401 錯誤)
```bash
# 症狀: API 返回 401 Unauthorized
# 原因: TEST_MODE 未生效或配置錯誤

# 解決方案:
# 1. 檢查 .env 檔案
cat .env | grep TEST_MODE
# 2. 重新啟動伺服器
# 3. 確認日誌中有 TEST_MODE 警告
```

#### 問題 2: 資料庫連線錯誤
```bash
# 症狀: 500 Internal Server Error, 資料庫相關錯誤
# 原因: 資料庫連線配置或 repository 注入問題

# 解決方案:
# 1. 檢查 DATABASE_URL 配置
# 2. 確認 SQLAlchemy 依賴注入正確
# 3. 檢查 repository factory 設置
```

#### 問題 3: 依賴注入錯誤
```bash
# 症狀: ImportError 或 dependency injection 相關錯誤
# 原因: Factory 或 dependency 配置錯誤

# 解決方案:
# 1. 檢查 factories.py 中的依賴創建
# 2. 確認 dependencies.py 中的注入配置
# 3. 驗證 use case 構造函數參數
```

### 自動化遷移驗證腳本

```bash
#!/bin/bash
# clean-architecture-migration-test.sh
# Clean Architecture 遷移驗證自動化腳本

echo "🚀 開始 Clean Architecture 遷移驗證"

# 1. 檢查環境配置
echo "📋 檢查環境配置..."
if grep -q "TEST_MODE=true" .env && grep -q "RECAPTCHA_ENABLED=false" .env; then
    echo "✅ 環境配置正確"
else
    echo "❌ 環境配置錯誤，請檢查 .env 檔案"
    exit 1
fi

# 2. 啟動伺服器 (背景執行)
echo "🖥️  啟動測試伺服器..."
uv run python apps/api-server/main.py &
SERVER_PID=$!
sleep 5

# 3. 等待伺服器啟動
echo "⏳ 等待伺服器啟動..."
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health >/dev/null 2>&1; then
        echo "✅ 伺服器已啟動"
        break
    fi
    sleep 1
done

# 4. 測試靜態端點
echo "🔍 測試靜態端點..."
STATIC_ENDPOINTS=(
    "/api/v1/clients/options/sources"
    "/api/v1/clients/options/types"
    "/api/v1/clients/options/statuses"
)

for endpoint in "${STATIC_ENDPOINTS[@]}"; do
    response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000${endpoint}")
    if [ "$response" = "200" ]; then
        echo "✅ $endpoint"
    else
        echo "❌ $endpoint (HTTP $response)"
    fi
done

# 5. 測試動態端點
echo "📊 測試動態端點..."

# 測試讀取
echo "Testing GET /api/v1/clients..."
response=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/v1/clients")
if [ "$response" = "200" ]; then
    echo "✅ GET /api/v1/clients"
else
    echo "❌ GET /api/v1/clients (HTTP $response)"
fi

# 測試創建
echo "Testing POST /api/v1/clients..."
response=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "http://localhost:8000/api/v1/clients" \
    -H "Content-Type: application/json" \
    -d '{
        "name": "Migration Test Client",
        "email": "migration@example.com",
        "source": "referral",
        "client_type": "paid",
        "status": "first_session"
    }')

if [ "$response" = "200" ] || [ "$response" = "201" ]; then
    echo "✅ POST /api/v1/clients"
else
    echo "❌ POST /api/v1/clients (HTTP $response)"
fi

# 6. 清理
echo "🧹 清理資源..."
kill $SERVER_PID
wait $SERVER_PID 2>/dev/null

echo "🎉 Clean Architecture 遷移驗證完成"
```

## 最佳實踐 (Best Practices)

### 1. 測試數據管理
- 每次測試前清理測試數據
- 使用獨立的測試資料庫
- 實施測試數據隔離

### 2. 測試覆蓋率
- 測試所有 HTTP 方法 (GET, POST, PUT, PATCH, DELETE)
- 包含正常和異常情況
- 驗證回應格式和狀態碼

### 3. 並行測試
- 避免測試間的數據競爭
- 使用唯一的測試標識符
- 實施適當的測試順序

### 4. 持續整合
- 在 CI/CD 管道中自動執行 API 測試
- 設定測試失敗時的通知機制
- 生成測試報告和覆蓋率統計

## 故障排除 (Troubleshooting)

### 常見問題解決

#### 1. 測試模式未生效
```bash
# 檢查環境變數
echo $TEST_MODE

# 重新啟動服務
TEST_MODE=true uv run python apps/api-server/main.py
```

#### 2. API 回應 401 錯誤
```bash
# 確認測試模式日誌
grep "TEST_MODE" logs/app.log

# 檢查服務狀態
curl -I http://localhost:8000/health
```

#### 3. 資料庫連線問題
```bash
# 檢查資料庫連線
psql $DATABASE_URL -c "SELECT 1;"

# 檢查測試用戶是否存在
psql $DATABASE_URL -c "SELECT * FROM users WHERE email = 'test@example.com';"
```