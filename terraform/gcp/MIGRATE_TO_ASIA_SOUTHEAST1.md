# 遷移 Buckets 到 asia-southeast1 (新加坡)

## 背景
為了優化亞洲地區的延遲，我們將 GCS buckets 從 `us-central1` 遷移到 `asia-southeast1`。

## 重要注意事項
⚠️ **警告**：這將創建新的 buckets，現有的 buckets 不會自動遷移資料！

## 遷移步驟

### 1. 備份現有資料（如果需要）
```bash
# 備份現有 bucket 資料
gsutil -m cp -r gs://coaching-audio-dev/* ./backup-audio/
gsutil -m cp -r gs://coaching-transcript-dev/* ./backup-transcript/
```

### 2. 切換到 dev workspace
```bash
cd terraform/gcp
terraform workspace select dev
# 或創建新的 workspace
terraform workspace new dev
```

### 3. 初始化 Terraform
```bash
terraform init
```

### 4. 規劃變更
```bash
# 使用 dev 環境變數
terraform plan -var-file="terraform.tfvars.dev"
```

### 5. 應用變更

由於 bucket location 不能直接更改，Terraform 會嘗試重新創建 buckets。

**選項 A：創建新的 buckets（推薦）**
```bash
# 修改 bucket 名稱以避免衝突
# 編輯 main.tf，將 bucket 名稱改為：
# coaching-audio-dev-asia
# coaching-transcript-dev-asia

# 然後應用
terraform apply -var-file="terraform.tfvars.dev"
```

**選項 B：刪除並重建（危險 - 會刪除所有資料）**
```bash
# 只在確認資料已備份的情況下執行
terraform destroy -target=google_storage_bucket.audio_storage -var-file="terraform.tfvars.dev"
terraform destroy -target=google_storage_bucket.transcript_storage -var-file="terraform.tfvars.dev"

# 然後重新創建
terraform apply -var-file="terraform.tfvars.dev"
```

### 6. 更新環境變數

更新你的 `.env` 檔案：
```bash
# GCP 設定
GCP_REGION=asia-southeast1
AUDIO_STORAGE_BUCKET=coaching-audio-dev  # 或新的 bucket 名稱
TRANSCRIPT_STORAGE_BUCKET=coaching-transcript-dev  # 或新的 bucket 名稱

# STT 設定
GOOGLE_STT_LOCATION=asia-southeast1
```

### 7. 驗證新配置
```bash
# 檢查新 buckets
gsutil ls -L -b gs://coaching-audio-dev | grep -i location
# 應該顯示：Location constraint: ASIA-SOUTHEAST1

# 測試 STT 連接
cd ../../../packages/core-logic
python scripts/check_gcs_upload.py
```

### 8. 恢復資料（如果需要）
```bash
# 將備份資料上傳到新 buckets
gsutil -m cp -r ./backup-audio/* gs://coaching-audio-dev/
gsutil -m cp -r ./backup-transcript/* gs://coaching-transcript-dev/
```

## 注意事項

1. **STT Location 必須與 Bucket Location 一致**
   - Google Speech-to-Text v2 要求 audio file 和 recognizer 在同一個 location

2. **成本考量**
   - asia-southeast1 的價格可能與 us-central1 不同
   - 跨區域資料傳輸會產生額外費用

3. **延遲優化**
   - asia-southeast1 (新加坡) 對亞洲用戶有更低的延遲
   - 特別適合台灣、香港、東南亞用戶

4. **兼容性**
   - 確保所有服務都支援 asia-southeast1
   - Speech-to-Text v2 在 asia-southeast1 支援所有主要語言

## 回滾計劃

如果需要回滾到原始配置：
```bash
# 修改 terraform.tfvars.dev
gcp_region = "us-central1"

# 重新應用
terraform apply -var-file="terraform.tfvars.dev"

# 更新 .env
GOOGLE_STT_LOCATION=us-central1
```

## 問題排查

### 錯誤：Expected resource location to be global
- 確保 STT location 與 bucket location 一致
- 檢查 `GOOGLE_STT_LOCATION` 環境變數

### 錯誤：Bucket name already exists
- Bucket 名稱全球唯一，需要使用新名稱
- 建議加上 region suffix，如 `coaching-audio-dev-asia`

### 錯誤：Permission denied
- 確保服務帳號有足夠權限
- 執行 `terraform apply` 更新 IAM 權限