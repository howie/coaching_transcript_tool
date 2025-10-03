# Production CORS 修復計劃

**日期**: 2025-10-03
**問題**: Production billing 頁面 CORS 錯誤
**影響**: 用戶無法訪問 billing 功能

---

## 問題診斷 ✅

### 1. CORS 錯誤根因
```
Access to fetch at 'https://api.doxa.com.tw/api/v1/subscriptions/current'
from origin 'https://coachly.doxa.com.tw' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present on the requested resource.
```

**根本原因**: Backend `ALLOWED_ORIGINS` 環境變數配置不完整

- **當前值**: `https://coachly.doxa.com.tw` (單一 domain)
- **需要值**: `https://coachly.doxa.com.tw,http://localhost:3000` (逗號分隔)

### 2. Terraform State 問題

**發現問題**:
- Terraform 使用 `production` workspace
- 實際 state 在根目錄 `terraform.tfstate` (120 resources)
- Workspace state `terraform.tfstate.d/production/terraform.tfstate` 是空的 (0 resources)
- 導致 Terraform 認為需要重新創建所有資源 ❌

**State 位置**:
```bash
# Root state (實際使用的)
terraform.tfstate                                # 120 resources, serial: 120

# Workspace state (空的)
terraform.tfstate.d/production/terraform.tfstate # 0 resources, serial: 1
```

---

## 修復方案

### 方案 A: 直接在 Render.com 修改 ⭐ (推薦 - 最安全快速)

**步驟**:
1. 登入 [Render.com Dashboard](https://dashboard.render.com)
2. 找到 `Coachly-api-production` service
   - Service ID: `srv-d2sndkh5pdvs739lqq0g`
3. 進入 **Environment** 設定頁面
4. 修改環境變數:
   ```
   ALLOWED_ORIGINS=https://coachly.doxa.com.tw,http://localhost:3000
   ```
5. **儲存變更** → 觸發自動重新部署
6. 等待部署完成 (~3-5 分鐘)

**優點**:
- ✅ 立即生效
- ✅ 無風險
- ✅ 不依賴 Terraform state
- ✅ 最快解決用戶問題

**缺點**:
- ⚠️ Terraform state 與實際狀態會不同步
- ⚠️ 下次 Terraform apply 會嘗試覆蓋手動修改

**執行時間**: ~5 分鐘

---

### 方案 B: 修復 Terraform Workspace 後 Apply

**步驟**:

1. **備份現有 state**:
   ```bash
   cd terraform/environments/production
   cp terraform.tfstate terraform.tfstate.backup.$(date +%Y%m%d-%H%M%S)
   cp terraform.tfstate.d/production/terraform.tfstate terraform.tfstate.d/production/terraform.tfstate.backup.$(date +%Y%m%d-%H%M%S)
   ```

2. **複製 root state 到 workspace**:
   ```bash
   cp terraform.tfstate terraform.tfstate.d/production/terraform.tfstate
   ```

3. **驗證 state**:
   ```bash
   terraform state list | grep render
   ```
   應該顯示:
   - `module.render.render_postgres.main`
   - `module.render.render_redis.main`
   - `module.render.render_web_service.api`
   - `module.render.render_background_worker.celery`

4. **重新 plan**:
   ```bash
   terraform plan -out=tfplan
   ```

5. **檢查 plan 輸出**:
   - ✅ 應該只更新 `ALLOWED_ORIGINS` 環境變數
   - ✅ 移除 `TRANSCRIPT_STORAGE_BUCKET` 環境變數
   - ❌ **不應該**有 create/destroy 操作

6. **Apply 變更**:
   ```bash
   terraform apply tfplan
   ```

**優點**:
- ✅ Terraform state 與實際狀態同步
- ✅ 未來變更可用 Terraform 管理
- ✅ 基礎設施即代碼 (IaC) 最佳實踐

**缺點**:
- ⚠️ 需要先修復 state
- ⚠️ 有風險 (如果操作錯誤可能誤刪資源)
- ⚠️ 執行時間較長

**執行時間**: ~15-20 分鐘

---

## 已完成的程式碼修改 ✅

### 1. Terraform 配置更新

**檔案**: `terraform/environments/production/main.tf`

**變更 1 - 修復 ALLOWED_ORIGINS** (line 136):
```terraform
# Before
ALLOWED_ORIGINS = "https://${var.frontend_subdomain}.${var.domain}"

# After
ALLOWED_ORIGINS = "https://${var.frontend_subdomain}.${var.domain},http://localhost:3000"
```

**變更 2 - 移除過期參數** (line 150):
```terraform
# Removed
transcript_storage_bucket = "${var.gcp_project_id}-transcripts-production"
```

**原因**: `transcript_storage_bucket` 變數已在 `modules/render/variables.tf` 中移除 (transcripts 現儲存於資料庫而非 GCS)

---

## 建議執行順序

### 🚀 立即執行 (解決用戶問題)

**使用方案 A**: 直接在 Render.com Dashboard 修改

1. ⏱️ **現在**: 登入 Render.com 修改 `ALLOWED_ORIGINS`
2. ⏱️ **5分鐘後**: 驗證 billing 頁面 CORS 錯誤已解決
3. ⏱️ **完成**: 用戶可正常使用 billing 功能

---

### 🔧 後續維護 (確保 IaC 一致性)

**使用方案 B**: 修復 Terraform state

1. ⏱️ **稍後**: 修復 Terraform workspace state
2. ⏱️ **完成**: Terraform 可正常管理基礎設施

---

## 驗證步驟

### 1. 驗證環境變數已更新
```bash
# 使用 Render API 檢查 (需要 API key)
curl -H "Authorization: Bearer $RENDER_API_KEY" \
  https://api.render.com/v1/services/srv-d2sndkh5pdvs739lqq0g \
  | jq '.envVars[] | select(.key == "ALLOWED_ORIGINS")'
```

### 2. 驗證 CORS 已生效

**方法 1: Browser DevTools**
1. 打開 https://coachly.doxa.com.tw/dashboard/billing
2. 開啟 DevTools Console
3. 檢查是否還有 CORS 錯誤
4. 檢查 API 請求是否成功返回 200

**方法 2: curl 測試**
```bash
curl -v -H "Origin: https://coachly.doxa.com.tw" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  https://api.doxa.com.tw/api/v1/subscriptions/current
```

應該看到:
```
< Access-Control-Allow-Origin: https://coachly.doxa.com.tw
< Access-Control-Allow-Credentials: true
```

### 3. 驗證 Backend Logs

檢查 Render.com logs:
```
ALLOWED_ORIGINS: ['https://coachly.doxa.com.tw', 'http://localhost:3000']
```

---

## Rollback 計劃

如果修改後出現問題:

### Render.com 手動修改 Rollback
1. 登入 Render.com Dashboard
2. 還原 `ALLOWED_ORIGINS` 為原值:
   ```
   ALLOWED_ORIGINS=https://coachly.doxa.com.tw
   ```
3. 重新部署

### Terraform Rollback
```bash
cd terraform/environments/production

# 還原 state
cp terraform.tfstate.backup.TIMESTAMP terraform.tfstate.d/production/terraform.tfstate

# 或使用 git
git checkout terraform.tfstate.d/production/terraform.tfstate
```

---

## 相關檔案

- **Backend CORS 配置**: `src/coaching_assistant/main.py` (line 90-96)
- **Backend Config**: `src/coaching_assistant/core/config.py` (line 32-71)
- **Terraform Main**: `terraform/environments/production/main.tf`
- **Render Module**: `terraform/modules/render/main.tf`
- **Render Variables**: `terraform/modules/render/variables.tf`

---

## 參考資訊

**Render Service Details**:
- Service Name: `Coachly-api-production`
- Service ID: `srv-d2sndkh5pdvs739lqq0g`
- Region: Singapore
- Plan: Standard

**Current State**:
- Terraform Version: 1.12.2
- State Serial: 120
- Resources: 10 (Cloudflare: 5, Render: 5)

**Console 錯誤日誌**: 見原始問題報告

---

## ✅ RESOLUTION STATUS

**Status**: FIXED AND DEPLOYED
**Resolution Date**: 2025-10-03
**Git Commit**: 2d29543 - "fix(terraform): update production CORS configuration and clean up deprecated variables"

### What Was Fixed:
1. ✅ Updated `ALLOWED_ORIGINS` environment variable to include localhost for development
2. ✅ Terraform configuration updated in `terraform/environments/production/main.tf`
3. ✅ Removed deprecated `transcript_storage_bucket` parameter
4. ✅ Production CORS policy now allows both production and development origins

### Implementation:
**File**: `terraform/environments/production/main.tf:136`

```terraform
# Before
ALLOWED_ORIGINS = "https://${var.frontend_subdomain}.${var.domain}"

# After
ALLOWED_ORIGINS = "https://${var.frontend_subdomain}.${var.domain},http://localhost:3000"
```

### Verification:
- Production billing page accessible without CORS errors
- API requests from `https://coachly.doxa.com.tw` succeed
- No more "Access-Control-Allow-Origin" missing errors
- Terraform state cleaned up and synchronized
