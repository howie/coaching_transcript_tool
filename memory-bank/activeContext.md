# 當前工作重點

## 工具鏈重構完成 ✅

### 已完成的工具鏈重構任務

1. **目錄結構重組完成 (第一階段)**
   - ✅ `apps/container` → `apps/api-server`
   - ✅ 測試檔案從 `apps/api-server/tests/` 移至 `packages/core-logic/tests/`
   - ✅ CLI pyproject.toml 從 `apps/api-server/` 移至 `apps/cli/`
   - ✅ 清理了 `apps/api-server/src/` 中的舊檔案

2. **配置檔案更新完成 (第一階段)**
   - ✅ 更新 Makefile 中所有對 `apps/container` 的引用為 `apps/api-server`
   - ✅ 更新測試路徑從 `apps/container/tests/` 到 `packages/core-logic/tests/`
   - ✅ 更新 docker-compose.yml 適應新架構
   - ✅ 修復 Dockerfile.api 路徑問題
   - ✅ 修復 `apps/api-server/requirements.txt` 中相對路徑

3. **前端工具鏈重構完成 (第二階段)**
   - ✅ 備份 root 層級配置檔案 (.bk)
   - ✅ 前端配置遷移到 `apps/web/`
     - `wrangler.frontend.toml` → `apps/web/wrangler.toml`
     - 創建 `apps/web/turbo.json` 
     - 更新 `apps/web/package.json` 添加部署腳本
   - ✅ Makefile 增強支援前端管理
     - 添加 `dev-frontend`, `build-frontend`, `deploy-frontend` 等指令
     - 統一的開發體驗 (`dev-all`, `build-all`, `install-all`)
   - ✅ 功能驗證測試通過
     - 前端依賴安裝成功
     - Next.js 建置成功  
     - 開發服務器啟動正常

4. **Docker 構建測試完成**
   - ✅ API Docker 映像構建成功
   - ✅ CLI Docker 映像之前已驗證可正常運作

### 當前專案架構 (重構後)

```
coaching_transcript_tool/
├── apps/                    # 應用程式層
│   ├── api-server/         # FastAPI 服務器 (重構前: backend/)
│   │   ├── main.py         # FastAPI 應用入口
│   │   ├── requirements.txt # API 服務依賴
│   │   └── Dockerfile.api  # API Docker 檔案
│   ├── cli/                # 命令列工具 (重構前: backend/)
│   │   ├── main.py         # CLI 入口點
│   │   ├── requirements.txt # CLI 依賴
│   │   ├── pyproject.toml  # CLI 套件配置
│   │   └── Dockerfile      # CLI Docker 檔案
│   ├── cloudflare/         # Cloudflare Workers 閘道 (重構前: gateway/)
│   │   ├── main.py         # Workers 入口點
│   │   ├── requirements.txt # Workers 依賴
│   │   ├── wrangler.toml   # Cloudflare 配置
│   │   └── src/            # Workers 源碼
│   └── web/                # Next.js 前端 (重構前: frontend/)
│       ├── app/
│       ├── components/
│       └── package.json
├── packages/               # 共享套件層
│   ├── core-logic/         # 核心業務邏輯
│   │   ├── src/coaching_assistant/ # 核心模組
│   │   ├── tests/          # 測試檔案 (從 apps/api-server 移過來)
│   │   └── pyproject.toml  # 核心套件配置
│   └── shared-types/       # 共享類型定義 (預留)
├── docs/                   # 正式專案文檔
└── memory-bank/            # Cline AI 工作記憶
```

### 驗證結果

- ✅ API Docker 映像構建成功 (31.8s)
- ✅ CLI Docker 映像之前測試正常
- ✅ 所有路徑引用已更新
- ✅ 測試配置已調整

## 下一階段規劃

### 短期目標
1. 測試新架構下的完整功能
2. 驗證 docker-compose 整體服務啟動
3. 確認所有 make 指令正常運作

### 中期目標  
1. 實作前端與新 API 架構的整合
2. 完善 `packages/shared-types` 的型別定義
3. 優化 Docker 構建效率

### 技術債務
- 考慮使用 multi-stage build 優化 Docker 映像大小
- 評估是否需要統一 Python 依賴管理 (poetry/pipenv)
- 規劃 CI/CD pipeline 適應新架構

## 當前工作重點 - Coach Assistant MVP 實作 🚀

**MVP 架構設計已完成！** ✅  
**基於 Render + PostgreSQL + GCS 的新架構** ✅

### 🎯 最新架構決策 (2025-08-04)
- **前端平台**：Cloudflare Workers (保持現狀)
- **後端平台**：Render.com + FastAPI
- **資料庫**：PostgreSQL (Render 內建)
- **檔案儲存**：Google Cloud Storage
- **STT 服務**：Google Speech-to-Text v2 (內建 diarization)
- **背景任務**：Celery + Redis (Render Redis)

### 🏗️ 新架構優勢
- **開發友善**：Render 自動部署，PostgreSQL 熟悉度高
- **成本可控**：免費版適合 MVP，付費版僅 $7/月
- **Google 整合**：GCS + Speech-to-Text 深度整合
- **遷移準備**：Repository Pattern 為未來 Cloud Run 遷移做準備

### 📋 實作計劃 (6週 MVP)
#### Phase 1 (第1-2週)：基礎架構
- ✅ 更新 MVP 設計文件 (v1.1)
- 🔄 建立 Render 專案和 PostgreSQL
- 🔄 Google Cloud 設定 (GCS + Speech-to-Text API)
- 🔄 實作 Repository Pattern 和資料模型

#### Phase 2 (第3-4週)：核心功能
- 🔄 Google OAuth 認證系統
- 🔄 檔案上傳到 GCS
- 🔄 Google Speech-to-Text 整合
- 🔄 背景任務處理 (Celery)

#### Phase 3 (第5-6週)：完善功能
- 🔄 Speaker diarization 和角色標註
- 🔄 WebSocket 進度推播
- 🔄 使用量追蹤和限制

### 🎯 當前任務
1. **建立 Render 專案**：設定 Web Service 和 PostgreSQL
2. **Google Cloud 設定**：建立專案、啟用 API、服務帳號
3. **更新後端代碼**：整合 SQLAlchemy + PostgreSQL
4. **實作認證系統**：Google OAuth + JWT

### 💰 成本結構 (更新)
- **固定成本**：$15/月 (Render Web + DB + GCS)
- **變動成本**：$0.016/分鐘 (Google STT)
- **目標毛利**：70-78% (Pro plan $599/月)
