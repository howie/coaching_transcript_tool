# Render 部署檢查清單

## 部署前準備
- [x] config.py 已更新支援所有必要的環境變數
- [x] main.py 已更新支援 Render 的啟動方式
- [x] requirements.txt 已包含所有必要的依賴

## Render Dashboard 設定

### 1. 建立 Web Service
- Service Name: `coaching-assistant-api`
- Region: Singapore (或選擇最接近的區域)
- Branch: `main` (或您的部署分支)
- Runtime: Python 3

### 2. Build & Start Commands
```
Build Command: cd apps/api-server && pip install -r requirements.txt
Start Command: cd apps/api-server && uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 3. 環境變數設定

複製以下環境變數到 Render Environment 設定：

#### 必要的環境變數（立即設定）
```
# 資料庫設定
DATABASE_URL=[您的 Render PostgreSQL Internal URL]

# 安全設定
SECRET_KEY=[使用下方指令生成您自己的密鑰]
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

**生成 SECRET_KEY 指令：**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# 應用設定
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=10000

# CORS 設定
ALLOWED_ORIGINS=https://coachly.doxa.com.tw,https://coachly-doxa-com-tw.howie-yu.workers.dev

# 檔案上傳限制
MAX_FILE_SIZE=500
MAX_AUDIO_DURATION=3600

# 日誌設定
LOG_LEVEL=INFO
LOG_FORMAT=json
```

#### 稍後設定的環境變數（Google Cloud 整合後）
```
# Google OAuth (待設定)
GOOGLE_CLIENT_ID=[待設定]
GOOGLE_CLIENT_SECRET=[待設定]

# Google Cloud (待設定)
GOOGLE_APPLICATION_CREDENTIALS_JSON=[待設定]
GOOGLE_STORAGE_BUCKET=[待設定]
GOOGLE_PROJECT_ID=[待設定]

# Redis (待設定)
REDIS_URL=[待設定]
CELERY_BROKER_URL=[待設定]
CELERY_RESULT_BACKEND=[待設定]
```

## 部署後驗證

### 1. 健康檢查
部署完成後，訪問以下端點確認服務正常：
```bash
curl https://[your-service-name].onrender.com/health
```

預期回應：
```json
{
  "status": "healthy",
  "environment": "production",
  "timestamp": "2025-08-05T..."
}
```

### 2. API 文檔
訪問 API 文檔確認所有端點正常：
```
https://[your-service-name].onrender.com/docs
```

### 3. 資料庫連線測試
檢查日誌確認資料庫連線成功：
- 在 Render Dashboard 的 Logs 標籤查看
- 應該看到 "Database connection established" 或類似訊息

## 問題排查

### 常見問題
1. **Build 失敗**：檢查 requirements.txt 路徑是否正確
2. **啟動失敗**：確認 PORT 環境變數是否被正確讀取
3. **資料庫連線失敗**：確認使用的是 Internal URL 而非 External URL
4. **CORS 錯誤**：確認 ALLOWED_ORIGINS 設定正確

### 日誌查看
在 Render Dashboard 的 Logs 標籤可以查看：
- Build logs
- Deploy logs
- Service logs

## 下一步
1. 完成 Google Cloud 專案設定
2. 配置 Google OAuth 2.0
3. 設定 Google Cloud Storage
4. 整合 Redis 和 Celery

---
更新時間：2025-08-05
