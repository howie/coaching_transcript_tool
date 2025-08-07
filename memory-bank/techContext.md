# 技術堆疊 (Tech Context)

**更新時間：** 2025-08-07 14:30  
**技術版本：** v3.2 (Coach Assistant MVP - Dark Mode & Accessibility Enhanced)

## 🎯 MVP 核心技術架構

### 混合雲模式
- **前端平台**：Cloudflare Workers + Next.js 14
- **後端平台**：Render.com + FastAPI + PostgreSQL
- **AI 服務**：Google Cloud Speech-to-Text v2
- **檔案儲存**：Google Cloud Storage
- **背景任務**：Celery + Redis

## 🔧 前端技術棧

### 核心框架
- **Next.js 14.0.4** - React 全端框架 (App Router)
- **TypeScript 5.0+** - 類型安全開發
- **Tailwind CSS 3.3+** - 實用優先 CSS 框架 (class-based dark mode)

### 狀態管理與 UI
- **Zustand 4.0+** - 輕量級狀態管理
- **React Hook Form 7.0+** - 高效能表單處理
- **SWR 2.0+** - 資料獲取與快取
- **Headless UI** - 無樣式可存取元件

### 主題與無障礙系統
- **Dark Mode Support** - 完整暗黑模式實現 (class-based)
- **WCAG 2.1 AA Compliant** - 無障礙網頁標準合規
- **CSS Variables** - 語意化顏色系統
- **Theme Context** - React 主題狀態管理
- **Semantic Tokens** - Tailwind 自訂設計代幣

### 認證與安全
- **Google OAuth 2.0** - 用戶認證
- **JWT Tokens** - 無狀態認證
- **HTTPS Only** - 安全傳輸層

### 部署平台
- **Cloudflare Workers** - 全球邊緣運算
- **OpenNext** - Next.js on Workers 適配器
- **Chunk Loading 優化** - 一致性 build ID 與快取策略

## 🖥️ 後端技術棧

### 核心框架
- **FastAPI 0.104+** - 現代 Python Web 框架
- **Python 3.11+** - 程式語言
- **Pydantic 2.0+** - 資料驗證和序列化

### 資料庫層
- **PostgreSQL 15+** - 主要資料庫
- **SQLAlchemy 2.0+** - Python ORM
- **Alembic** - 資料庫遷移工具
- **asyncpg** - 異步 PostgreSQL 驅動

### 背景任務處理
- **Celery 5.3+** - 分散式任務佇列
- **Redis 7.0+** - 訊息代理與結果後端
- **Celery Beat** - 任務排程器

### Google Cloud 整合
```python
# 核心 Google Cloud 服務
"google-cloud-speech==2.21.0"      # Speech-to-Text API
"google-cloud-storage==2.10.0"     # Cloud Storage
"google-auth==2.23.4"               # 認證庫
"google-auth-oauthlib==1.1.0"      # OAuth 2.0 流程
```

### Speech-to-Text 配置
```python
# STT 最佳化設定
config = speech.RecognitionConfig(
    encoding=speech.RecognitionConfig.AudioEncoding.MP3,
    sample_rate_hertz=44100,
    language_code='zh-TW',  # 中文繁體
    enable_speaker_diarization=True,
    diarization_speaker_count=2,
    enable_automatic_punctuation=True,
    model='latest_long'  # 長音檔最佳化
)
```

### WebSocket 支援
- **FastAPI WebSocket** - 即時進度推播
- **asyncio** - 異步編程模型

### 部署平台
- **Render.com** - PaaS 平台
  - Web Service (FastAPI)
  - PostgreSQL Database
  - Redis Instance
- **GitHub Integration** - 自動部署

## � 資料模型與 ORM

### SQLAlchemy 模型
```python
# 核心實體
class User(Base):
    # Google OAuth 用戶
    google_id = Column(String, unique=True)
    email = Column(String, unique=True)
    plan = Column(Enum(UserPlan))  # FREE, PRO, ENTERPRISE
    usage_minutes = Column(Integer, default=0)

class Session(Base):
    # 教練對話會議
    user_id = Column(UUID, ForeignKey("users.id"))
    status = Column(Enum(SessionStatus))  # UPLOADING, PROCESSING, COMPLETED
    gcs_audio_path = Column(String)
    transcription_job_id = Column(String)

class TranscriptSegment(Base):
    # 轉錄片段
    session_id = Column(UUID, ForeignKey("sessions.id"))
    speaker_id = Column(Integer)  # STT diarization
    content = Column(Text)
    confidence = Column(Float)    # STT 信心分數
```

### Repository Pattern
```python
# 資料存取抽象化
class SessionRepository(BaseRepository):
    def get_user_sessions(self, user_id: UUID) -> List[Session]
    def update_status(self, session_id: UUID, status: SessionStatus)
    def create_segments(self, segments: List[TranscriptSegment])
```

## 🔄 背景任務架構

### Celery 任務佇列
```python
# 主要異步任務
@celery_app.task(bind=True, max_retries=3)
def process_audio_transcription(self, session_id: str, gcs_path: str):
    # 1. 調用 Google Speech-to-Text
    # 2. 處理 speaker diarization
    # 3. 儲存轉錄結果到 PostgreSQL
    # 4. 更新 WebSocket 進度
    # 5. 清理暫存檔案
```

### Redis 配置
```python
# Celery Broker 設定
celery_app = Celery(
    'coaching_assistant',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['tasks.transcription']
)
```

## 🛠️ 開發工具與流程

### 專案管理
- **Makefile** - 統一開發指令介面
- **Monorepo** - apps/ + packages/ 架構
- **Git Hooks** - 代碼品質檢查

### 測試策略
```bash
# 後端測試
pytest packages/core-logic/tests/ -v
pytest --cov=coaching_assistant tests/

# 前端測試  
cd apps/web && npm test
cd apps/web && npm run test:e2e

# API 整合測試 (已建立完整測試套件)
scripts/api-tests/run_all_tests.sh    # 執行所有 API 測試
scripts/api-tests/test_auth.sh        # 認證流程測試
scripts/api-tests/test_clients.sh     # 客戶管理測試
scripts/api-tests/test_sessions.sh    # 教練會談測試
scripts/api-tests/test_dashboard.sh   # Dashboard 統計測試

# 客戶管理功能測試覆蓋
# - 客戶編輯頁面錯誤處理測試
# - 教練會談客戶篩選器測試
# - 客戶數據加載測試
# - API 錯誤處理和後備機制測試
```

### API 測試基礎設施
```bash
# 完整 curl 測試套件位於 scripts/api-tests/
├── README.md                 # API 測試文檔與使用指南
├── run_all_tests.sh         # 主要測試執行器
├── test_auth.sh            # 用戶認證與 JWT token 測試
├── test_clients.sh         # 客戶管理 CRUD 操作測試
├── test_sessions.sh        # 教練會談管理測試
└── test_dashboard.sh       # Dashboard 統計與摘要測試

# 測試環境變數
export API_BASE_URL="http://localhost:8000"
export AUTH_TOKEN="your_jwt_token_here"

# 執行方式
chmod +x scripts/api-tests/run_all_tests.sh
./scripts/api-tests/run_all_tests.sh
```

### 代碼品質
- **Black** - Python 代碼格式化
- **isort** - Import 排序
- **ESLint + Prettier** - TypeScript/React 檢查
- **MyPy** - Python 靜態類型檢查

## 🚀 部署配置

### Render.com Blueprint
```yaml
# render.yaml
services:
  - type: web
    name: coach-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: DATABASE_URL
        fromDatabase: { name: coach-db, property: connectionString }
      - key: REDIS_URL  
        fromService: { name: coach-redis, type: redis }
      - key: GOOGLE_APPLICATION_CREDENTIALS_JSON
        fromGroup: google-cloud

databases:
  - name: coach-db
    databaseName: coaching_assistant
    user: coach_user
```

### Cloudflare Workers
```toml
# apps/web/wrangler.toml
name = "coachly-doxa-com-tw"
main = ".open-next/worker.js"
compatibility_date = "2024-09-23"
compatibility_flags = ["nodejs_compat"]

# Chunk loading 效能最佳化
[assets]
directory = ".open-next/assets"

[vars]
ENVIRONMENT = "production"
NODE_ENV = "production"

[observability.logs]
enabled = true
```

### Next.js Build 配置 (Chunk Loading 修復)
```javascript
// next.config.js - 解決 chunk loading 404 錯誤
const nextConfig = {
  // 一致性 build ID 生成防止 chunk hash 不匹配
  generateBuildId: async () => {
    if (process.env.VERCEL_GIT_COMMIT_SHA) {
      return process.env.VERCEL_GIT_COMMIT_SHA
    }
    if (process.env.CF_PAGES_COMMIT_SHA) {
      return process.env.CF_PAGES_COMMIT_SHA
    }
    return `v${require('./package.json').version}-${Date.now()}`
  },
  output: 'standalone',
}
```

### Cloudflare 快取策略
```text
# public/_headers - 靜態資源快取配置
/_next/static/*
  Cache-Control: public, max-age=31536000, immutable

/images/*
  Cache-Control: public, max-age=86400

/*
  Cache-Control: no-cache, no-store, must-revalidate
```

## 🔐 安全與合規

### 資料保護
- **24小時音檔自毀** - GCS Lifecycle Rules
- **GDPR 刪除權** - 完整資料清除 API
- **加密傳輸** - 全程 HTTPS/TLS 1.3
- **最小權限原則** - Google SA 權限管控

### 認證機制
```python
# JWT Token 管理
class JWTService:
    def create_access_token(self, user_id: UUID) -> str
    def verify_token(self, token: str) -> Optional[dict]
    def refresh_token(self, refresh_token: str) -> str
```

## 📊 監控與可觀測性

### 應用監控
- **Render Metrics** - 系統效能監控
- **Custom Metrics** - 業務指標追蹤
- **Structured Logging** - 結構化日誌記錄

### 關鍵指標
```python
# 業務監控指標
metrics = {
    "transcript_latency_sec": "轉錄處理延遲",
    "stt_cost_usd": "語音轉文字成本", 
    "active_users": "活躍用戶數",
    "error_rate": "錯誤率",
    "conversion_rate": "轉換率"
}  
```

## 💰 成本優化技術

### Google Cloud 成本控制
```python
# STT 成本最佳化
stt_config = {
    "model": "latest_long",           # 長音檔專用模型
    "use_enhanced": False,            # 暫不使用增強模型  
    "enable_word_time_offsets": True, # 精確時間戳
    "profanity_filter": False         # 節省成本
}
```

### 資源管理
- **音檔自動清理** - 1天生命週期
- **資料庫索引優化** - 查詢效能提升
- **Redis 記憶體管理** - LRU 策略

## 🔄 技術演進路線

### Phase 1 (當前 MVP)
- ✅ Render + PostgreSQL + GCS 基礎架構
- ✅ Google Speech-to-Text 整合
- 🔄 基礎 CRUD 和認證系統

### Phase 2 (Q2 2025)  
- 📋 AI 評分系統 (PCC Markers)
- 📋 進階用戶管理 (Team accounts)
- 📋 支付整合 (Stripe/NewebPay)

### Phase 3 (Q3 2025)
- 📋 遷移到 Google Cloud Run
- 📋 Kubernetes 容器編排
- 📋 Multi-region 部署

## 📋 依賴管理

### 後端核心依賴
```python
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
alembic==1.13.1
asyncpg==0.29.0
celery[redis]==5.3.4
google-cloud-speech==2.21.0
google-cloud-storage==2.10.0
pydantic==2.5.0
jose[cryptography]==1.0.0
```

### 前端核心依賴
```json
{
  "next": "14.0.4",
  "react": "^18.2.0", 
  "typescript": "^5.0.0",
  "tailwindcss": "^3.3.0",
  "zustand": "^4.4.0",
  "react-hook-form": "^7.47.0",
  "swr": "^2.2.4"
}
```

---

**文件用途：** 為 Cline 提供 Coach Assistant MVP 完整技術環境  
**更新頻率：** 技術選型變更或版本升級時更新  
**相關文件：** systemPatterns.md, activeContext.md, mvp-v1.md
