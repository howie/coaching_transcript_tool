# 系統架構模式 (System Patterns)

**更新時間：** 2025-08-01 22:01  
**架構版本：** v2.2 (Serverless 優先 + CF Workers 整合)

## 🏗️ 總體架構模式

### 全棧 Serverless 架構 (Single Service Architecture)
```
┌─────────────────────────────────────────────────────────────┐
│              Cloudflare Workers                             │
│  ┌─────────────────┐    ┌─────────────────────────────────┐ │
│  │   Frontend      │    │         Backend                 │ │
│  │  (Static Sites) │    │       (FastAPI)                 │ │
│  │                 │    │                                 │ │
│  │ • Next.js Build │    │ • Python Runtime                │ │
│  │ • Static Assets │    │ • FastAPI Routes                │ │
│  │ • Client Routes │    │ • File Processing               │ │
│  └─────────────────┘    │ • Data Transformation           │ │
│                         └─────────────────────────────────┘ │
│                                                             │
│  Built-in Features:                                         │
│  • Global Edge Network • Rate Limiting • CORS              │
│  • Auto-scaling • Caching • SSL/TLS                        │
└─────────────────────────────────────────────────────────────┘
```

### 簡化 Monorepo 模式
```
coaching_transcript_tool/
├── frontend/               # Next.js 應用 (建置為靜態檔案)
├── backend/                # FastAPI 服務 (本地開發用)
├── gateway/                # CF Workers 整合服務 (生產部署)
│   ├── wrangler.toml       # CF Workers 配置
│   ├── main.py             # FastAPI 應用複本
│   ├── src/                # 業務邏輯複本
│   └── static/             # 前端建置輸出
├── packages/               # 共用套件
│   ├── shared-types/       # TypeScript 型別定義
│   └── eslint-config/      # ESLint 共用配置
├── docs/                   # 正式專案文檔
├── memory-bank/            # Cline 工作記憶
└── legacy/                 # 舊版代碼保存
```

**Serverless 優先設計優勢：**
- **零基礎設施成本**：CF Workers 免費額度充足
- **全球邊緣部署**：自動全球加速和容錯
- **無運維負擔**：完全託管，自動擴展
- **極簡部署**：單一指令部署整個應用
- **開發生產一致**：相同的執行環境

## 📁 詳細專案結構

### 前端架構 (frontend/)
```
frontend/
├── app/                    # Next.js App Router
│   ├── globals.css         # 全域樣式定義
│   ├── layout.tsx          # 根布局組件
│   ├── page.tsx           # 首頁 (/) 
│   └── dashboard/          # Dashboard 功能區
│       ├── layout.tsx      # Dashboard 布局
│       ├── page.tsx       # Dashboard 首頁
│       └── transcript-converter/  # 轉換器功能
│           └── page.tsx    # 轉換器頁面
├── components/             # React 組件庫
│   ├── ui/                # 基礎 UI 組件
│   ├── forms/             # 表單組件
│   ├── layout/            # 布局組件 (Header, Sidebar)
│   └── sections/          # 頁面區塊組件
├── contexts/              # React Context 提供者
│   ├── theme-context.tsx  # 主題狀態管理
│   ├── i18n-context.tsx   # 國際化管理
│   └── sidebar-context.tsx # 側邊欄狀態
├── hooks/                 # 自定義 React Hooks
├── lib/                   # 工具函式和配置
│   └── api.ts            # API 客戶端配置
├── public/               # 靜態資源
│   └── images/           # 圖片資源 (Logo 等)
├── package.json          # 依賴和腳本配置
├── tailwind.config.ts    # Tailwind CSS 配置
├── tsconfig.json         # TypeScript 配置
└── next.config.js        # Next.js 配置
```

### 後端架構 (backend/)
```
backend/
├── src/
│   └── coaching_assistant/           # 主要應用程式
│       ├── __init__.py
│       ├── main.py                   # FastAPI 應用入口
│       ├── cli.py                    # CLI 指令接口
│       ├── parser.py                 # VTT 檔案解析器
│       ├── api/                      # API 路由模組
│       │   ├── __init__.py
│       │   ├── format_routes.py      # 檔案轉換 API
│       │   ├── health.py            # 健康檢查端點
│       │   └── user.py              # 用戶管理 API
│       ├── core/                     # 核心業務邏輯
│       │   ├── __init__.py
│       │   ├── config.py            # 應用配置管理
│       │   └── processor.py         # 檔案處理核心
│       ├── middleware/               # 中間件模組
│       │   ├── __init__.py
│       │   ├── error_handler.py     # 錯誤處理中間件
│       │   └── logging.py           # 日誌記錄中間件
│       ├── exporters/               # 輸出格式處理器
│       │   ├── excel.py             # Excel 格式輸出
│       │   └── markdown.py          # Markdown 格式輸出
│       ├── utils/                   # 工具函式
│       │   ├── chinese_converter.py # 簡繁轉換工具
│       │   └── s3_uploader.py       # 檔案上傳工具
│       └── static/                  # 靜態資源
│           └── openai.json          # OpenAI GPTs 配置
├── tests/                           # 測試檔案
│   ├── conftest.py                  # pytest 配置
│   ├── test_processor.py            # 處理器測試
│   └── data/                        # 測試資料
│       ├── sample_1.vtt
│       └── sample_2.vtt
├── requirements.txt                 # Python 依賴
└── Dockerfile                       # 容器化配置
```

### 共用套件架構 (packages/)
```
packages/
├── shared-types/          # TypeScript 型別定義
│   ├── package.json       # 套件配置
│   ├── tsconfig.json      # TypeScript 配置
│   └── src/
│       └── index.ts       # 共用型別匯出
└── eslint-config/         # ESLint 共用配置
    ├── package.json       # 套件配置
    └── index.js           # ESLint 規則配置
```

## 🔄 資料流模式

### 檔案處理流程
```
用戶上傳 → 前端驗證 → Gateway轉發 → 後端處理 → 結果返回
    ↓         ↓           ↓           ↓         ↓
  .vtt      格式檢查     認證驗證    VTT解析   .xlsx/.md
  檔案      大小限制     權限控制    格式轉換   檔案下載
```

### 認證流程模式
```
Google OAuth → NextAuth.js → JWT Token → API Gateway → FastAPI
      ↓            ↓           ↓            ↓           ↓
   用戶授權      會話管理    Token生成    Token驗證   受保護資源
```

## 🧩 設計模式應用

### 1. Repository Pattern (後端)
```python
# 資料存取抽象化
class UserRepository:
    def get_by_email(self, email: str) -> User
    def create(self, user_data: dict) -> User
    def update_usage(self, user_id: str) -> bool

class TranscriptRepository:
    def create_record(self, data: dict) -> TranscriptRecord
    def get_user_history(self, user_id: str) -> List[TranscriptRecord]
```

### 2. Middleware Pattern (Gateway)
```typescript
// 可組合的中間件鏈
app.use('*', corsMiddleware)
app.use('*', loggingMiddleware)
app.use('/api/*', authMiddleware)
app.use('/api/*', rateLimitMiddleware)
app.use('/api/v1/format', cacheMiddleware)
```

### 3. Factory Pattern (檔案處理)
```python
class ProcessorFactory:
    @staticmethod
    def create_processor(output_format: str) -> BaseProcessor:
        if output_format == "excel":
            return ExcelProcessor()
        elif output_format == "markdown":
            return MarkdownProcessor()
```

## 📦 元件化模式

### 前端元件架構
```
components/
├── ui/                    # 基礎 UI 元件
│   ├── Button.tsx
│   ├── Input.tsx
│   └── Modal.tsx
├── forms/                 # 表單元件
│   ├── FileUpload.tsx
│   └── ProcessingOptions.tsx
├── layout/                # 佈局元件
│   ├── Header.tsx
│   └── Sidebar.tsx
└── sections/              # 頁面區塊
    ├── Dashboard.tsx
    └── TranscriptConverter.tsx
```

### 狀態管理模式 (Zustand)
```typescript
// 全域狀態管理
interface AppState {
  user: User | null
  theme: 'light' | 'dark'
  language: 'zh-TW' | 'en'
  setUser: (user: User) => void
  toggleTheme: () => void
  setLanguage: (lang: string) => void
}
```

## 🔒 安全模式

### 認證與授權
```
用戶請求 → JWT驗證 → 權限檢查 → 資源存取
    ↓         ↓         ↓         ↓
  Bearer    Token解析  Role/Plan  API回應
  Token     用戶資訊   權限驗證   或拒絕
```

### 資料保護
- **傳輸加密**：HTTPS/TLS 1.3
- **儲存加密**：資料庫加密，敏感欄位加密
- **存取控制**：RBAC (Role-Based Access Control)
- **資料清理**：定期清理暫存檔案

## 📊 監控與可觀測性

### 日誌模式
```python
# 結構化日誌
logger.info("File processed", extra={
    "user_id": user.id,
    "file_size": file.size,
    "processing_time": duration,
    "output_format": format_type
})
```

### 錯誤處理模式
```typescript
// 統一錯誤處理
class APIError extends Error {
  constructor(
    public statusCode: number,
    public message: string,
    public details?: any
  ) {}
}
```

## 🚀 部署模式

### 混合雲部署
- **前端**：Cloudflare Pages (靜態資源 + SSR)
- **Gateway**：Cloudflare Workers (邊緣運算)
- **後端**：GCP Cloud Run (容器化服務)
- **資料庫**：GCP Cloud SQL (託管 PostgreSQL)

### CI/CD 流程
```
Git Push → Tests → Build → Deploy → Health Check
   ↓        ↓       ↓       ↓         ↓
 GitHub   Jest   Docker  CF Pages   監控系統
Actions   pytest  Image   Cloud Run  自動回滾
```

## 🔄 快取策略

### 多層快取
```
Browser Cache → CF Cache → Gateway Cache → Backend Cache
     ↓             ↓            ↓             ↓
  靜態資源      邊緣快取      API回應      資料庫查詢
  (24h)        (1h)         (15min)      (5min)
```

## 📈 擴展模式

### 水平擴展
- **無狀態服務**：所有服務都設計為無狀態
- **負載均衡**：Cloud Run 自動負載分散
- **資料庫讀寫分離**：讀寫複本分離

### 垂直擴展
- **資源彈性**：基於 CPU/Memory 使用率自動擴展
- **效能調優**：定期分析瓶頸並優化

---

**文件用途：** 幫助 Cline 理解系統架構和設計決策  
**更新頻率：** 架構變更時更新  
**相關文件：** techContext.md, architecture-decisions.md
