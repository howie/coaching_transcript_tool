# 專案快照 (Project Snapshot)

生成時間：2025-07-31 14:15 (UTC+8)

## 專案概覽 (Project Overview)

**專案名稱：** Coaching Transcript Tool  
**版本：** 2.0.0-dev (重構中)  
**GitHub：** https://github.com/howie/coaching_transcript_tool  
**作者：** Howie Yu (howie.yu@gmail.com)  
**授權：** MIT License  

### 專案描述
一個專業的教練對話逐字稿處理工具，支援將 VTT 格式的逐字稿轉換為結構化的 Markdown 或 Excel 文件。專案正在進行大規模重構，從 Flask+FastAPI 混合架構轉型為現代化的前後端分離 SaaS 服務，採用 Next.js + FastAPI + CF Workers 的三層架構設計。

## 技術架構 (Technical Architecture)

### 新架構概覽 (重構中)
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Next.js 14    │    │  CF Workers      │    │   FastAPI       │
│ (CF Pages)      │ -> │  (API Gateway)   │ -> │ (GCP Cloud Run) │
│ - SSR/SSG       │    │ - 認證中間件      │    │ - 核心業務邏輯   │
│ - 響應式 UI     │    │ - Rate Limiting  │    │ - 檔案處理      │
│ - NextAuth      │    │ - 快取層        │    │ - 資料庫存取    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### 核心技術棧 (更新)
- **前端框架：** Next.js 14 + App Router + TypeScript
- **UI 框架：** Tailwind CSS (基於原始金色主題設計)
- **後端框架：** FastAPI (純化，移除 Flask)
- **API Gateway：** Cloudflare Workers + Hono.js
- **程式語言：** TypeScript (前端) + Python 3.11+ (後端)
- **資料處理：** pandas, openpyxl (保持不變)
- **中文處理：** opencc-python-reimplemented (保持不變)
- **認證：** NextAuth.js + Google OAuth 2.0
- **雲端部署：** Cloudflare Pages + GCP Cloud Run
- **容器化：** Docker, Docker Compose
- **CLI框架：** Typer (保持不變)
- **測試框架：** pytest + Jest + Testing Library

### 新的 Monorepo 結構
```
coaching_transcript_tool/
├── package.json               # Monorepo 根配置
├── turbo.json                # Turborepo 配置
├── apps/                     # 應用程式
│   ├── frontend/             # Next.js 應用 ✅
│   │   ├── app/              # App Router ✅
│   │   │   ├── (dashboard)/  # Dashboard 路由群組 ✅
│   │   │   │   ├── dashboard/page.tsx ✅
│   │   │   │   ├── transcript-converter/page.tsx ✅
│   │   │   │   └── layout.tsx ✅
│   │   │   ├── layout.tsx    # 根 Layout ✅
│   │   │   ├── page.tsx      # 首頁 ✅
│   │   │   └── globals.css   # 全域樣式 ✅
│   │   ├── lib/              # 工具函式 ✅
│   │   │   └── api.ts        # API 客戶端 ✅
│   │   ├── next.config.js    # Next.js 配置 ✅
│   │   ├── tailwind.config.ts # Tailwind 配置 ✅
│   │   ├── tsconfig.json     # TypeScript 配置 ✅
│   │   ├── .env.local        # 環境變數 ✅
│   │   └── package.json      # 依賴配置 ✅
│   ├── gateway/              # CF Workers Gateway (待開發)
│   │   ├── src/
│   │   │   ├── middleware/   # 中間件
│   │   │   └── routes/       # 路由處理
│   │   └── package.json
│   └── backend/              # FastAPI 應用 ✅
│       ├── src/coaching_assistant/
│       │   ├── main.py       # 重構後的主應用 ✅
│       │   ├── api/          # API 路由 ✅
│       │   │   ├── health.py ✅
│       │   │   ├── format_routes.py ✅
│       │   │   └── user.py ✅
│       │   ├── core/         # 核心邏輯 ✅
│       │   │   ├── config.py ✅
│       │   │   └── processor.py ✅
│       │   ├── middleware/   # 中間件 ✅
│       │   │   ├── logging.py ✅
│       │   │   └── error_handler.py ✅
│       │   └── utils/        # 工具函式 (保持) ✅
│       └── requirements.txt ✅
├── packages/                 # 共用套件 (待建立)
│   ├── shared-types/         # TypeScript 型別
│   └── eslint-config/        # ESLint 配置
├── scripts/                  # 部署腳本 (待建立)
├── docs/                     # 專案文件 (保持)
└── legacy/                   # 舊版檔案 (暫時保留)
    ├── app/                  # 舊 Flask 前端
    └── src/                  # 舊核心邏輯
```

## 核心功能 (Core Features)

### 1. 檔案格式支援
- **輸入格式：** VTT (WebVTT) 逐字稿檔案
- **輸出格式：** 
  - Markdown (.md) - 適合閱讀和版本控制
  - Excel (.xlsx) - 適合數據分析和處理

### 2. 文字處理功能
- **說話者匿名化：** 將特定姓名替換為 "Coach" 和 "Client"
- **中文轉換：** 簡體中文轉繁體中文支援
- **說話者合併：** 自動合併連續的同一說話者內容
- **時間戳保留：** 維持原始時間標記資訊

### 3. 多種使用介面
- **CLI 工具：** `transcript-tool` 命令行介面 ✅
- **Web 介面：** Next.js 響應式前端 ✅
- **API 服務：** RESTful API 端點供程式化存取 ✅
- **Custom GPT 整合：** (開發中) 透過 OpenAPI schema 整合

### 4. 雲端功能
- **檔案上傳：** 支援大檔案上傳處理 ✅
- **S3 整合：** AWS S3 儲存未識別格式檔案片段 ✅
- **容器化部署：** Docker 支援，準備雲端部署 ✅

## UI 設計風格 (UI Design)

### 設計主題
基於原始 app/static 設計，採用專業金色主題：
- **主色調：** 金色 (#C09357) - 專業、信任
- **輔助色：** 黑色 (#000000)、白色 (#FFFFFF)
- **灰階：** #f8f9fa, #e9ecef, #dee2e6, #343a40
- **字體：** Inter, -apple-system, BlinkMacSystemFont

### 設計元素
- **圓角半徑：** 8px 統一
- **陰影效果：** 0 4px 20px rgba(0, 0, 0, 0.1)
- **轉場動效：** all 0.3s ease
- **響應式斷點：** 768px (平板), 480px (手機)

### 組件風格
- **按鈕：** 金色主按鈕 + 透明邊框按鈕
- **卡片：** 白色背景 + 柔和陰影
- **表單：** 簡潔輸入框 + 金色焦點狀態
- **導航：** 專業深色頂部導航

## 專案配置 (Project Configuration)

### 環境變數配置
```bash
# Next.js 前端
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=development-secret-key
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...

# FastAPI 後端
GOOGLE_OAUTH_SECRETS="..."
GOOGLE_OAUTH_REDIRECT_URI="http://localhost:8000/oauth2callback"
FLASK_SECRET_KEY="your-secret-key-here"

# AWS 設定
S3_BUCKET_NAME="your-s3-bucket-name"
AWS_ACCESS_KEY_ID="your-aws-access-key-id"
AWS_SECRET_ACCESS_KEY="your-aws-secret-access-key"
AWS_REGION="your-aws-region"
```

### 依賴套件 (更新)
```json
{
  "frontend": {
    "next": "14.2.31",
    "@types/react": "^18",
    "typescript": "^5",
    "tailwindcss": "^3.4.0",
    "next-auth": "^4"
  },
  "backend": [
    "pandas>=1.3.0",
    "openpyxl>=3.0.9", 
    "fastapi>=0.100.0",
    "uvicorn>=0.22.0",
    "python-multipart",
    "typer[all]",
    "boto3>=1.28.0",
    "python-dotenv>=1.0.0",
    "opencc-python-reimplemented==0.1.7",
    "pydantic-settings>=2.0.0"
  ]
}
```

### Docker 配置
- **CLI 工具：** `Dockerfile` - 輕量級 Python 3.10 映像
- **API 服務：** `Dockerfile.api` - 多階段構建，包含健康檢查
- **Docker Compose：** 提供完整的開發和部署環境

## 開發工作流程 (Development Workflow)

### 可用的指令
```bash
# Monorepo 指令
npm run dev          # 啟動所有服務
npm run build        # 建置所有應用
npm run test         # 執行所有測試

# 前端開發
cd apps/frontend
npm run dev          # Next.js 開發伺服器 (http://localhost:3000)
npm run build        # 建置生產版本
npm run lint         # ESLint 檢查

# 後端開發
cd apps/backend
uvicorn coaching_assistant.main:app --reload  # 開發伺服器 (http://localhost:8000)
pytest               # 執行測試

# Legacy Make 命令 (仍可用)
make help            # 顯示所有可用命令
make clean           # 清理建置產物
make test            # 執行測試
make docker          # 建置 Docker 映像
```

### CLI 使用範例 (保持不變)
```bash
# 基本轉換
transcript-tool format-command input.vtt output.md

# Excel 輸出
transcript-tool format-command input.vtt output.xlsx --format excel

# 說話者匿名化
transcript-tool format-command input.vtt output.md \
    --coach-name "Dr. Smith" --client-name "Mr. Johnson"

# 繁體中文轉換
transcript-tool format-command input.vtt output.md --traditional
```

### API 端點 (更新)
```
# 健康檢查
GET /health

# 檔案處理 (重構後)
POST /api/v1/format
- 檔案上傳和處理
- 支援多種輸出格式
- 說話者替換和中文轉換

# 用戶管理 (新)
GET /api/v1/user/profile
POST /api/v1/user/preferences

# OpenAPI 文件
GET /docs (開發環境)
GET /openapi.json
```

## 🏗️ 當前架構狀態

### **階段 1：基礎架構準備** ✅ **已完成**
- ✅ Monorepo 結構建立 (Turborepo)
- ✅ 技術棧選擇和版本確定
- ✅ 開發環境配置
- ✅ 專案重組和清理

### **階段 2：前端重構** ✅ **已完成**
- ✅ Next.js 14 應用建立
- ✅ App Router 結構實作
- ✅ TypeScript + Tailwind CSS 設定
- ✅ 響應式 UI 組件開發
- ✅ API 客戶端實作
- ✅ 環境變數配置
- ✅ 導航系統實作
- ✅ 金色主題 UI 設計 (基於原始設計)

### **階段 3：API Gateway 開發** 📝 **待開始**
- [ ] CF Workers Gateway 建立
- [ ] Hono.js 路由設定
- [ ] 認證中間件實作
- [ ] Rate Limiting 機制
- [ ] 快取層實作

### **階段 4：後端重構與部署** ✅ **已完成**
- ✅ FastAPI 應用重構
- ✅ 基礎中間件實作 (logging, error handling)
- ✅ API 路由重構 (health, format, user)
- ✅ 設定管理重構 (pydantic-settings)
- ✅ 健康檢查端點
- [ ] 資料庫模型設計
- [ ] GCP Cloud Run 配置
- [ ] CI/CD Pipeline 設定

### **階段 5：整合測試與優化** 📝 **待開始**
- [ ] 端對端測試撰寫
- [ ] 效能基準測試
- [ ] 監控系統設定
- [ ] 安全性測試

## 當前開發狀態 (Current Development Status)

### ✅ 已完成功能
- [x] CLI 工具核心功能 (保持不變)
- [x] VTT 檔案解析和處理 (保持不變)
- [x] Markdown/Excel 輸出格式 (保持不變)
- [x] **Monorepo 結構建立** (新)
- [x] **Turborepo 配置設定** (新)
- [x] **FastAPI 應用重構** (新)
  - [x] 純 FastAPI 架構 (移除 Flask 混合)
  - [x] 中間件層重構 (logging, error handling)
  - [x] API 路由重構 (health, format, user)
  - [x] 設定管理現代化 (pydantic-settings)
  - [x] 所有現有測試通過
- [x] **Next.js 前端開發** (新)
  - [x] Next.js 14 + App Router 架構
  - [x] TypeScript + Tailwind CSS 技術棧
  - [x] 響應式 UI 組件開發
  - [x] Dashboard 和逐字稿轉換器頁面
  - [x] API 客戶端實作
  - [x] 環境變數配置
  - [x] 金色主題 UI 設計

### 🚧 進行中
- [ ] **認證系統整
