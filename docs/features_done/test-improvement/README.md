# Test Mode Configuration

## 概述 (Overview)

測試模式 (Test Mode) 允許開發者在不需要 JWT 認證的情況下測試所有 API 端點。這個功能專為開發和測試環境設計，極大簡化了 API 測試流程。

Test Mode allows developers to test all API endpoints without requiring JWT authentication. This feature is specifically designed for development and testing environments to greatly simplify the API testing process.

## ⚠️ 重要安全警告 (Critical Security Warning)

**🚨 測試模式絕不可在生產環境中啟用！**

- 測試模式會完全跳過認證檢查
- 任何人都可以訪問所有 API 端點
- 系統已內建保護機制，防止在生產環境中啟用
- 如果在生產環境中嘗試啟用，系統會拋出錯誤

**🚨 Test Mode MUST NEVER be enabled in production environments!**

- Test mode completely bypasses authentication checks
- Anyone can access all API endpoints
- Built-in protection prevents enabling in production
- System will throw an error if attempted in production

## 快速開始 (Quick Start)

### 1. 啟用測試模式 (Enable Test Mode)

設定環境變數：
```bash
export TEST_MODE=true
```

或在 `.env` 檔案中：
```
TEST_MODE=true
```

### 2. 啟動開發伺服器 (Start Development Server)

```bash
# 使用測試模式啟動 API 伺服器
TEST_MODE=true uv run python apps/api-server/main.py

# 或使用 uvicorn
TEST_MODE=true uvicorn apps.api-server.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 測試 API (Test APIs)

現在您可以直接呼叫任何 API 端點，無需提供 Authorization header：

```bash
# 測試用戶資訊 API
curl http://localhost:8000/api/v1/auth/me

# 測試會話列表 API
curl http://localhost:8000/api/v1/sessions

# 測試方案資訊 API
curl http://localhost:8000/api/v1/plans/current
```

## 功能特性 (Features)

### ✅ 自動測試用戶創建
- 系統會自動創建 `test@example.com` 測試用戶
- 測試用戶擁有 PRO 方案權限，可測試所有功能
- 無需手動設定用戶資料

### ✅ 完整 API 覆蓋
- 所有需要認證的端點都可直接訪問
- 包括用戶管理、會話管理、計費等功能
- 支援所有 HTTP 方法 (GET, POST, PUT, DELETE)

### ✅ 開發友好
- 無需生成或管理 JWT tokens
- 快速迭代和測試
- 簡化 CI/CD 測試流程

### ✅ 安全保護
- 生產環境自動禁用
- 明確的警告日誌
- 配置驗證機制

## 實用範例 (Practical Examples)

### 測試用戶相關 API
```bash
# 獲取當前用戶資訊
curl http://localhost:8000/api/v1/auth/me

# 回應範例：
{
  "id": "...",
  "email": "test@example.com",
  "name": "Test User",
  "plan": "PRO"
}
```

### 測試會話管理 API
```bash
# 創建新會話
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"audio_language": "zh-TW", "stt_provider": "google"}'

# 獲取會話列表
curl http://localhost:8000/api/v1/sessions
```

### 測試計費相關 API
```bash
# 獲取當前方案
curl http://localhost:8000/api/v1/plans/current

# 獲取使用情況
curl http://localhost:8000/api/v1/usage
```

## 相關文件 (Related Documentation)

- [詳細配置指南 (Configuration Guide)](./test-mode-configuration.md)
- [API 測試指南 (API Testing Guide)](./api-testing-guide.md)
- [安全注意事項 (Security Considerations)](./security-considerations.md)
- [測試腳本範例 (Example Scripts)](./examples/)

## 常見問題 (FAQ)

### Q: 測試模式是否影響資料庫？
A: 是的，測試模式使用相同的資料庫。建議在測試環境中使用獨立的測試資料庫。

### Q: 可以自訂測試用戶嗎？
A: 目前系統會自動創建固定的測試用戶。如需自訂，請修改 `auth.py` 中的測試用戶設定。

### Q: 如何確認測試模式已啟用？
A: 系統日誌會顯示警告訊息："🚨 TEST_MODE 已啟用 - 跳過認證檢查，使用測試用戶"

### Q: 是否可以在 CI/CD 中使用？
A: 可以，但務必確保 CI/CD 環境設定為非生產環境 (`ENVIRONMENT != "production"`)。