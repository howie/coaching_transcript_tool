# 技術堆疊 (Tech Context)

**更新時間：** 2025-08-01 22:02  
**技術版本：** v2.2 (Serverless 優先 + CF Workers 整合)

## 🔧 前端技術棧

### 核心框架
- **Next.js 14.0.4** - React 全端框架
  - App Router (最新路由系統)
  - Server-Side Rendering (SSR)
  - Static Site Generation (SSG)
  - API Routes

### 開發語言
- **TypeScript 5.0+** - 類型安全的 JavaScript
- **JavaScript ES2022** - 現代 JavaScript 標準

### UI/UX 工具
- **Tailwind CSS 3.3+** - 實用優先的 CSS 框架
- **Tailwind UI** - 預建元件庫
- **Headless UI** - 無樣式可存取元件
- **Lucide React** - 現代圖標庫

### 狀態管理
- **Zustand 4.0+** - 輕量級狀態管理
- **React Context** - 主題、語言等全域狀態

### 表單處理
- **React Hook Form 7.0+** - 高效能表單庫
- **Zod 3.0+** - TypeScript 優先的驗證庫

### 認證系統
- **NextAuth.js 4.0+** - Next.js 認證解決方案
- **Google Provider** - Google OAuth 2.0 整合

### 測試工具
- **Jest 29.0+** - JavaScript 測試框架
- **Testing Library** - React 元件測試
- **Playwright** - E2E 測試 (規劃中)

## 🖥️ 後端技術棧

### 核心框架
- **FastAPI 0.104+** - 現代 Python Web 框架
- **Python 3.11+** - 程式語言
- **Pydantic 2.0+** - 資料驗證和設定管理

### 資料處理
- **pandas 2.0+** - 資料分析和處理
- **openpyxl 3.1+** - Excel 檔案處理
- **python-multipart** - 檔案上傳處理

### 中文處理
- **opencc-python-reimplemented** - 簡繁轉換
- **jieba** - 中文分詞 (規劃中)

### HTTP 客戶端
- **httpx 0.25+** - 異步 HTTP 客戶端
- **requests 2.31+** - 同步 HTTP 客戶端

### 資料庫 (規劃中)
- **SQLAlchemy 2.0+** - Python ORM
- **asyncpg** - PostgreSQL 異步驅動
- **Alembic** - 資料庫遷移工具

### 測試工具
- **pytest 7.0+** - Python 測試框架
- **pytest-asyncio** - 異步測試支援
- **pytest-cov** - 覆蓋率測試

## 🌐 Cloudflare Workers 全棧技術棧 (新架構)

### 執行環境
- **Cloudflare Workers** - 全球邊緣運算平台
- **Python Runtime** - 直接執行 FastAPI 應用
- **V8 JavaScript Engine** - 前端靜態資源託管
- **Wrangler CLI** - 開發和部署工具

### 後端整合
- **FastAPI 完整支援** - 直接在 Workers 運行
- **Python 標準庫** - 完整 Python 生態系統
- **Async/Await** - 原生異步處理支援
- **Request/Response** - Web 標準 API

### 前端整合
- **Next.js Static Export** - 靜態檔案產生
- **Static Asset Serving** - 直接從 Workers 託管
- **Client-Side Routing** - SPA 路由支援
- **API Proxy** - 無縫前後端整合

### 儲存與快取服務
- **Cloudflare KV** - 全球分散式鍵值儲存
- **Cloudflare R2** - 物件儲存 (檔案處理)
- **Workers Cache API** - 邊緣快取
- **Durable Objects** - 狀態持久化 (進階功能)

### 開發工具
- **wrangler dev** - 本地開發服務器
- **wrangler deploy** - 一鍵部署
- **Workers Dashboard** - 監控和日誌
- **Edge-side Analytics** - 即時效能分析

## 📦 共用套件 (packages/)

### shared-types/
```json
{
  "name": "@coaching-tool/shared-types",
  "version": "1.0.0",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "dependencies": {
    "typescript": "^5.0.0"
  }
}
```

### eslint-config/
```json
{
  "name": "@coaching-tool/eslint-config",
  "version": "1.0.0",
  "main": "index.js",
  "dependencies": {
    "@typescript-eslint/eslint-plugin": "^6.0.0",
    "@typescript-eslint/parser": "^6.0.0",
    "eslint": "^8.0.0"
  }
}
```

## 🛠️ 開發工具

### 建置工具
- **Turborepo 1.10+** - Monorepo 建置系統
- **Vite** - 快速建置工具 (部分使用)
- **esbuild** - 快速 JavaScript 打包器

### 代碼品質
- **ESLint 8.0+** - JavaScript/TypeScript 檢查器
- **Prettier 3.0+** - 代碼格式化工具
- **Husky** - Git hooks 管理
- **lint-staged** - 暫存檔案檢查

### 類型檢查
- **TypeScript Compiler** - 類型檢查
- **tsc-alias** - 路徑別名解析

## 🚀 部署技術

### 容器化
- **Docker 24.0+** - 容器平台
- **Docker Compose** - 多容器應用管理

### CI/CD
- **GitHub Actions** - 持續整合/部署
- **Changesets** - 版本管理和發布

### 雲端服務
- **Cloudflare Pages** - 前端部署
- **Cloudflare Workers** - 邊緣運算
- **GCP Cloud Run** - 後端容器部署
- **GCP Cloud SQL** - 託管資料庫

## 📊 監控工具

### 錯誤追蹤
- **Sentry** - 錯誤監控和效能追蹤
- **Sentry JavaScript SDK** - 前端錯誤追蹤
- **Sentry Python SDK** - 後端錯誤追蹤

### 日誌管理
- **Structlog** - Python 結構化日誌
- **Winston** - Node.js 日誌庫 (如需要)

### 分析工具
- **Google Analytics 4** - 用戶行為分析
- **Cloudflare Analytics** - 網站效能分析

## 🔧 開發環境設定

### 必要軟體
```bash
# Node.js 環境
node >= 18.17.0
npm >= 9.6.7

# Python 環境  
python >= 3.11.0
pip >= 23.0.0

# 容器環境
docker >= 24.0.0
docker-compose >= 2.0.0
```

### VS Code 擴充套件
- **TypeScript Importer** - 自動 import
- **Tailwind CSS IntelliSense** - CSS 類別提示
- **Python** - Python 開發支援
- **Prettier** - 代碼格式化
- **ESLint** - 代碼檢查

## 📋 套件版本管理

### Frontend Dependencies
```json
{
  "next": "14.0.4",
  "react": "^18.2.0",
  "typescript": "^5.0.0",
  "tailwindcss": "^3.3.0",
  "next-auth": "^4.24.0",
  "zustand": "^4.4.0",
  "react-hook-form": "^7.47.0",
  "zod": "^3.22.0"
}
```

### Backend Dependencies
```python
fastapi==0.104.1
uvicorn[standard]==0.24.0
pandas==2.1.3
openpyxl==3.1.2
python-multipart==0.0.6
opencc-python-reimplemented==1.1.7
httpx==0.25.2
pydantic==2.5.0
pydantic-settings==2.1.0
```

## 🔄 技術升級計劃

### 短期 (Q1 2025)
- **Next.js 15** - 升級到最新版本
- **React 19** - 新功能採用
- **FastAPI 0.105** - 效能改善

### 中期 (Q2-Q3 2025)
- **PostgreSQL 16** - 資料庫升級
- **Python 3.12** - 語言版本升級
- **Cloudflare Workers v2** - 新版 API

### 長期 (Q4 2025)
- **Rust** - 高效能核心模組
- **WebAssembly** - 瀏覽器端處理
- **GraphQL** - API 查詢語言

---

**文件用途：** 提供 Cline 完整的技術環境資訊  
**更新頻率：** 每次套件升級或技術選型變更時更新  
**相關文件：** systemPatterns.md, activeContext.md
