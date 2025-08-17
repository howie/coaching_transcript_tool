# GCP Terraform 部署指南

## 🎯 快速部署 (推薦)

```bash
# 1. 確保在正確目錄
cd terraform/gcp

# 2. 設定工具版本
echo "terraform 1.12.2" > .tool-versions

# 3. 認證 Google Cloud
make setup

# 4. 初始化 Terraform
make init

# 5. 匯入現有資源
make import-existing

# 6. 檢查計劃
make plan

# 7. 部署！
make apply

# 8. 生成環境變數
make env-file
```

## 📋 詳細步驟

### 步驟 1: 環境準備

```bash
# 確保工具已安裝
make install

# 認證並設定專案
make setup
```

### 步驟 2: Terraform 初始化

```bash
# 初始化 Terraform（下載 providers）
make init

# 驗證配置檔案
make validate
```

### 步驟 3: 處理現有資源

我們分析發現 `coaching-storage` 服務帳戶已存在，需要匯入：

```bash
# 自動匯入所有現有資源
make import-existing

# 或手動匯入（如果自動匯入失敗）
make import-service-account
```

### 步驟 4: 預覽變更

```bash
# 查看將要進行的變更
make plan

# 儲存計劃到檔案
make plan-out
```

### 步驟 5: 執行部署

```bash
# 互動式部署（會提示確認）
make apply

# 或自動化部署（無提示，小心使用）
# make apply-auto
```

### 步驟 6: 生成應用程式配置

```bash
# 生成 .env.terraform 檔案
make env-file

# 查看所有輸出值
make output

# 查看環境變數模板
make output-env

# 查看服務帳戶認證（敏感）
make output-credentials
```

## 🔍 部署後驗證

```bash
# 驗證所有資源
make verify

# 測試 Speech-to-Text API
make test-speech
```

## 📊 預期結果

部署成功後，您將獲得：

### ✅ 已啟用的 APIs
- Speech-to-Text v2 API
- Cloud Storage APIs
- IAM API
- 監控和日誌 APIs

### ✅ 正確的 IAM 權限
- `roles/speech.user` - 解決 403 錯誤
- `roles/storage.objectAdmin` - 檔案操作
- `roles/storage.legacyBucketWriter` - 簽署 URL

### ✅ 儲存基礎設施
- 音訊儲存桶（24小時自動刪除）
- 文字稿儲存桶（90天後轉冷儲存）
- CORS 配置完成

### ✅ 安全設定
- 統一桶級存取控制
- 公共存取防護
- 最小權限原則

## 🚨 故障排除

### 問題 1: 服務帳戶匯入失敗
```bash
# 手動匯入
terraform import google_service_account.coaching_storage projects/coachingassistant/serviceAccounts/coaching-storage@coachingassistant.iam.gserviceaccount.com
```

### 問題 2: API 未啟用錯誤
```bash
# 強制重新建立 API 資源
terraform taint google_project_service.apis["speech.googleapis.com"]
terraform apply
```

### 問題 3: 權限不足錯誤
```bash
# 檢查目前認證
gcloud auth list

# 重新認證
gcloud auth application-default login
```

### 問題 4: 儲存桶已存在錯誤
```bash
# 匯入現有儲存桶
make import-audio-bucket
make import-transcript-bucket
```

### 緊急修復
如果 Terraform 完全失敗，可以手動應用關鍵權限：
```bash
make emergency-permissions
```

## 🔄 更新和維護

### 更新權限
1. 修改 `variables.tf` 中的 `service_account_roles`
2. 執行 `make plan` 檢查變更
3. 執行 `make apply` 應用變更

### 新增 API
1. 修改 `variables.tf` 中的 `required_apis`
2. 執行 `terraform apply`

### 清理資源
⚠️ **危險操作！**
```bash
# 銷毀所有資源（小心！）
make destroy
```

## 📝 應用程式配置

部署完成後，更新您的應用程式環境變數：

```bash
# 從生成的檔案複製環境變數
cat .env.terraform

# 或直接查看輸出
terraform output env_vars_template
```

關鍵環境變數：
- `GOOGLE_APPLICATION_CREDENTIALS_JSON` - 服務帳戶憑證
- `AUDIO_STORAGE_BUCKET` - 音訊檔案桶名
- `TRANSCRIPT_STORAGE_BUCKET` - 文字稿桶名

## 🎉 完成！

部署成功後：
1. Speech-to-Text v2 API 403 錯誤應該解決
2. 檔案上傳功能應該正常工作
3. 所有權限正確配置
4. 儲存基礎設施準備就緒

現在您可以繼續進行應用程式開發和測試！