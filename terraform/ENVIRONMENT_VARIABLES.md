# 環境變數配置指南

## 🎯 標準化的環境變數

基於 Terraform 配置，我們現在使用以下**統一的環境變數**：

### ✅ 推薦使用 (新標準)

```bash
# Google Cloud Platform 配置
GOOGLE_APPLICATION_CREDENTIALS_JSON='{...service account json...}'  
GCP_PROJECT_ID=coachingassistant
GCP_REGION=asia-east1
SPEECH_API_VERSION=v2

# 存儲桶配置 (根據環境選擇)
AUDIO_STORAGE_BUCKET=coaching-audio-{env}      # 音訊檔案儲存桶
TRANSCRIPT_STORAGE_BUCKET=coaching-transcript-{env}  # 文字稿儲存桶

# 環境標識
ENVIRONMENT=dev|prod
```

## 📊 各環境配置

### 開發環境 (dev)
```bash
AUDIO_STORAGE_BUCKET=coaching-audio-dev
TRANSCRIPT_STORAGE_BUCKET=coaching-transcript-dev  
ENVIRONMENT=dev
```

### 生產環境 (prod)  
```bash
AUDIO_STORAGE_BUCKET=coaching-audio-prod
TRANSCRIPT_STORAGE_BUCKET=coaching-transcript-prod
ENVIRONMENT=prod
```

## ⚠️ 已棄用的環境變數

以下環境變數已被新標準取代，但**保留供向後相容**：

```bash
# ❌ 已棄用 - 使用 AUDIO_STORAGE_BUCKET 代替
GOOGLE_STORAGE_BUCKET=coaching-audio-dev

# ❌ 已棄用 - 使用 AUDIO_STORAGE_BUCKET 代替  
STORAGE_BUCKET=coaching-audio-{env}

# ❌ 舊格式 - 已更新為新的命名格式
AUDIO_STORAGE_BUCKET=coachingassistant-audio-storage
TRANSCRIPT_STORAGE_BUCKET=coachingassistant-transcript-storage
```

## 🔄 遷移指南

### 1. 更新應用程式程式碼

如果您的程式碼使用舊的環境變數，請更新：

```python
# ❌ 舊版
bucket = os.getenv('GOOGLE_STORAGE_BUCKET')
bucket = os.getenv('STORAGE_BUCKET')

# ✅ 新版  
audio_bucket = os.getenv('AUDIO_STORAGE_BUCKET')
transcript_bucket = os.getenv('TRANSCRIPT_STORAGE_BUCKET')
```

### 2. 更新環境配置檔案

```bash
# 複製並編輯環境檔案
cp .env.example .env

# 根據環境設定正確的儲存桶名稱
# 開發環境: coaching-audio-dev, coaching-transcript-dev
# 生產環境: coaching-audio-prod, coaching-transcript-prod
```

### 3. 從 Terraform 取得正確配置

```bash
# 開發環境
cd terraform/gcp
terraform workspace select dev
terraform output env_vars_template

# 生產環境
terraform workspace select default  
terraform output env_vars_template
```

## 🛠️ 快速設定

### 開發環境
```bash
# 使用 Terraform dev workspace 配置
cd terraform/gcp
terraform workspace select dev
terraform output env_vars_template > ../../.env.dev
```

### 生產環境
```bash
# 使用 Terraform default workspace 配置
cd terraform/gcp  
terraform workspace select default
terraform output env_vars_template > ../../.env.prod
```

## 📋 完整環境變數模板

```bash
# === 資料庫配置 ===
DATABASE_URL=postgresql://coach_user:coach_pass_dev@localhost:5432/coaching_assistant_dev
REDIS_URL=redis://:redis_pass_dev@localhost:6379/0

# === JWT 配置 ===
SECRET_KEY=your-super-secret-jwt-key-change-in-production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# === Google OAuth 配置 ===
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# === Google Cloud Platform 配置 (從 Terraform 取得) ===
GOOGLE_APPLICATION_CREDENTIALS_JSON='{...service account json...}'
GCP_PROJECT_ID=coachingassistant
GCP_REGION=asia-east1
SPEECH_API_VERSION=v2

# === 存儲桶配置 (根據環境) ===
AUDIO_STORAGE_BUCKET=coaching-audio-dev
TRANSCRIPT_STORAGE_BUCKET=coaching-transcript-dev
ENVIRONMENT=dev

# === 存儲配置 ===
RETENTION_DAYS=1
SIGNED_URL_EXPIRY_MINUTES=30

# === 應用配置 ===
DEBUG=true
API_HOST=localhost
API_PORT=8000
ALLOWED_ORIGINS=http://localhost:3000,https://localhost:3000
MAX_FILE_SIZE=500
MAX_AUDIO_DURATION=3600
```

## ✅ 驗證配置

確認您的應用程式使用正確的環境變數：

```bash
# 檢查環境變數是否正確設定
echo $AUDIO_STORAGE_BUCKET
echo $TRANSCRIPT_STORAGE_BUCKET

# 測試儲存桶是否存在
gsutil ls gs://$AUDIO_STORAGE_BUCKET
gsutil ls gs://$TRANSCRIPT_STORAGE_BUCKET
```