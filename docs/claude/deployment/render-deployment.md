# Render 部署指南

## 環境變數設定

在 Render Web Service 的 Environment 設定中，需要新增以下環境變數：

### 1. 資料庫配置
```
DATABASE_URL=[YOUR_RENDER_POSTGRESQL_INTERNAL_URL]
```
**注意：** 請使用 Render PostgreSQL 的內部連線 URL (Internal Database URL)，不要使用外部 URL。

### 2. 安全配置
```
SECRET_KEY=[GENERATE_A_STRONG_SECRET_KEY]
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```
**生成密鑰指令：** `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`

### 3. 應用配置
```
ENVIRONMENT=production
DEBUG=false
API_HOST=0.0.0.0
API_PORT=10000
```

### 4. CORS 配置
```
ALLOWED_ORIGINS=https://coachly.doxa.com.tw,https://coachly-doxa-com-tw.howie-yu.workers.dev
```

### 5. 檔案上傳限制
```
MAX_FILE_SIZE=500
MAX_AUDIO_DURATION=3600
```

### 6. 日誌配置
```
LOG_LEVEL=INFO
LOG_FORMAT=json
```

## 待完成項目

### Google OAuth 配置 (待設定)
- GOOGLE_CLIENT_ID
- GOOGLE_CLIENT_SECRET

### Google Cloud 配置 (待設定)
- GOOGLE_APPLICATION_CREDENTIALS_JSON
- GOOGLE_STORAGE_BUCKET

### Redis 配置 (待設定)
- REDIS_URL (Render Redis 或外部 Redis 服務)
- CELERY_BROKER_URL
- CELERY_RESULT_BACKEND

## 部署步驟

1. 在 Render Dashboard 中建立新的 Web Service
2. 連接 GitHub repository: `howie/coaching_transcript_tool`
3. 設定 Build Command: `cd apps/api-server && pip install -r requirements.txt`
4. 設定 Start Command: `cd apps/api-server && uvicorn main:app --host 0.0.0.0 --port $PORT`
5. 設定上述環境變數
6. 部署應用

## 資料庫資訊 (參考格式)
- Hostname: [YOUR_DB_HOSTNAME]
- Port: 5432
- Database: [YOUR_DB_NAME]
- Username: [YOUR_DB_USERNAME]
- Internal URL: postgresql://[USERNAME]:[PASSWORD]@[HOSTNAME]/[DATABASE]
- External URL: postgresql://[USERNAME]:[PASSWORD]@[HOSTNAME].[REGION]-postgres.render.com/[DATABASE]

**重要提醒：** 
- 請勿將實際的資料庫連線資訊提交到版本控制系統
- 使用環境變數或秘密管理服務來存儲敏感資訊
- 內部 URL 用於 Render 內部服務間通訊，外部 URL 用於外部連線
