# Terraform Plan Analysis

## 🎯 Dry Run 結果總覽

✅ **成功**: Terraform plan 執行成功，無語法錯誤
✅ **驗證**: 配置檔案通過 validation
⚠️ **衝突**: 發現 1 個重要衝突需處理

## 📊 將要建立的資源 (20 個)

### APIs (6 個)
- ✅ `speech.googleapis.com` - 已啟用，會被管理
- ✅ `iam.googleapis.com` - 已啟用，會被管理  
- ✅ `serviceusage.googleapis.com` - 已啟用，會被管理
- 🆕 `cloudresourcemanager.googleapis.com` - 新增 (需要)
- 🆕 `storage-api.googleapis.com` - 新增 (需要)
- 🆕 `storage-component.googleapis.com` - 新增 (需要)

### 監控 APIs (3 個)
- 🆕 `logging.googleapis.com` - 新增
- 🆕 `monitoring.googleapis.com` - 新增  
- 🆕 `clouderrorreporting.googleapis.com` - 新增

### 服務帳戶 (2 個)
- ⚠️ `google_service_account.coaching_storage` - **衝突！已存在**
- 🆕 `google_service_account_key.coaching_storage_key` - 新增金鑰

### IAM 權限 (3 個)
- 🆕 `roles/speech.user` - **關鍵！解決 403 錯誤**
- 🆕 `roles/storage.objectAdmin` - **關鍵！儲存權限**
- 🆕 `roles/storage.legacyBucketWriter` - **關鍵！簽署 URL**

### 儲存桶 (2 個)
- 🆕 `coachingassistant-audio-storage` - 音訊檔案 (24小時生命週期)
- 🆕 `coachingassistant-transcript-storage` - 文字稿檔案 (90天轉冷儲存)

### 儲存桶 IAM (3 個)
- 🆕 音訊桶物件管理權限
- 🆕 音訊桶 Legacy Writer 權限
- 🆕 文字稿桶物件管理權限

### 自訂角色 (1 個)
- 🆕 `speechV2User` - Speech-to-Text v2 最小權限角色

## ⚠️ 重要衝突：服務帳戶已存在

**問題**: `coaching-storage` 服務帳戶已存在於 GCP，但不在 Terraform 狀態中

**當前服務帳戶資訊**:
- Email: `coaching-storage@coachingassistant.iam.gserviceaccount.com`
- Display Name: "Coaching Assistant Storage Account"
- Description: "Service account for audio file storage operations"

**Terraform 預期**:
- Display Name: "Coaching Assistant Storage Service Account"
- Description: "Service account for Coaching Assistant application storage and processing"

### 解決方案選項

#### 選項 1: Import 現有服務帳戶 (推薦)
```bash
terraform import google_service_account.coaching_storage projects/coachingassistant/serviceAccounts/coaching-storage@coachingassistant.iam.gserviceaccount.com
```

#### 選項 2: 更新 Terraform 配置以符合現有資源
```hcl
resource "google_service_account" "coaching_storage" {
  account_id   = "coaching-storage"
  display_name = "Coaching Assistant Storage Account"  # 符合現有
  description  = "Service account for audio file storage operations"  # 符合現有
  project      = var.gcp_project_id
}
```

#### 選項 3: 刪除現有服務帳戶，讓 Terraform 重新建立
⚠️ **不推薦** - 會中斷現有服務

## 🔧 關鍵修復

### 1. 權限問題 (即將解決!)
目前缺少的權限將會被添加：
- `roles/speech.user` → 解決 Speech-to-Text v2 API 403 錯誤
- `roles/storage.objectAdmin` → 啟用檔案上傳/下載
- `roles/storage.legacyBucketWriter` → 啟用簽署 URL 生成

### 2. API 啟用
新啟用的關鍵 APIs：
- Cloud Resource Manager - Terraform 專案管理
- Storage APIs - 檔案儲存功能
- 監控相關 APIs - 錯誤追蹤和日誌

### 3. 儲存基礎設施
將建立完整的儲存解決方案：
- GDPR 合規的音訊檔案自動刪除
- 成本優化的文字稿冷儲存
- 正確的 CORS 配置

## 📈 預期影響

### ✅ 正面影響
- **解決 403 權限錯誤** - Speech-to-Text API 將正常工作
- **啟用檔案上傳** - 前端可以上傳音訊檔案
- **完整監控** - 錯誤追蹤和日誌記錄
- **成本優化** - 自動生命週期管理
- **安全強化** - 最小權限原則

### ⚠️ 潛在風險
- **服務帳戶衝突** - 需要 import 或調整配置
- **新金鑰生成** - 需要更新應用程式配置
- **API 配額** - 新啟用的 APIs 可能有配額限制

## 🚀 建議執行順序

1. **處理服務帳戶衝突**
   ```bash
   # 選項 1: Import 現有服務帳戶
   terraform import google_service_account.coaching_storage projects/coachingassistant/serviceAccounts/coaching-storage@coachingassistant.iam.gserviceaccount.com
   ```

2. **再次執行 plan 確認**
   ```bash
   terraform plan
   ```

3. **執行 apply**
   ```bash
   terraform apply
   ```

4. **更新應用程式環境變數**
   ```bash
   terraform output env_vars_template
   ```

## 🔄 下一步行動

1. 決定服務帳戶處理策略
2. 執行 import 或調整配置
3. 進行最終 apply
4. 驗證所有功能
5. 更新應用程式配置

這個 plan 將完全解決文件中提到的 Speech-to-Text v2 API 權限問題！