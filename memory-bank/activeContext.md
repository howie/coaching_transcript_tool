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
     ✅ `wrangler.frontend.toml` → `apps/web/wrangler.toml`
     - 創建 `apps/web/turbo.json` 
     ✅ 更新 `apps/web/package.json` 添加部署腳本
   - ✅ Makefile 增強支援前端管理
     ✅ 添加 `dev-frontend`, `build-frontend`, `deploy-frontend` 等指令
     ✅ 統一的開發體驗 (`dev-all`, `build-all`, `install-all`)
   - ✅ 功能驗證測試通過
     ✅ 前端依賴安裝成功
     ✅ Next.js 建置成功  
     ✅ 開發服務器啟動正常

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

**資料庫模型與認證基礎完成！** ✅  
**Render PostgreSQL 生產資料庫部署完成！** ✅  
**基於 Render + PostgreSQL + GCS 的架構** 🔄

### 🎯 最新完成項目 (2025-08-05 更新)

#### ✅ Phase 1B 進展：Render 資料庫部署完成
- **PostgreSQL 資料庫建立完成**
  - 資料庫實例：dpg-d27igr7diees73cla8og-a (Singapore)
  - 連線設定文檔：docs/deployment/render-deployment.md
  - 安全密鑰已生成並記錄

- **Alembic 資料庫遷移系統**
  - Alembic 初始化完成 (packages/core-logic/alembic/)
  - 環境變數支援設定完成
  - 初始遷移腳本成功執行
  - 所有資料表已在生產環境建立

#### ✅ Phase 1A：資料模型與測試基礎 (已完成)
- **核心資料模型實作**
  - User、Session、TranscriptSegment、SessionRole 完整實作
  - SQLAlchemy ORM 模型與關聯關係
  - UUID 主鍵和時間戳基礎模式
  - Enum 類型：UserPlan、SessionStatus、SpeakerRole

- **完整單元測試覆蓋 (82 個測試，100% 通過)**
  - 模型基本功能測試
  - 外鍵約束和唯一性約束測試
  - 屬性方法和業務邏輯測試
  - 關聯關係和級聯刪除測試
  - SQLite 外鍵約束正確啟用

- **開發環境完善**
  - Docker 開發配置 (Dockerfile.dev, docker-compose.dev.yml)
  - 環境變數範例 (.env.example)
  - 測試配置優化 (conftest.py)

### 📋 實作計劃更新 (6週 MVP)

#### Phase 1B (當前優先)：Google Cloud 與 Render 部署
- 🎯 **建立 Render 專案**：Web Service + PostgreSQL 資料庫
- 🎯 **Google Cloud 設定**：專案建立、API 啟用、服務帳號
- 🎯 **資料庫遷移**：SQLite → PostgreSQL，Alembic 遷移腳本
- 🎯 **部署驗證**：Render 環境測試，資料庫連線確認

#### Phase 2 (第3-4週)：認證與檔案處理
- 🔄 Google OAuth 2.0 認證流程
- 🔄 JWT token 管理與 refresh 機制
- 🔄 Google Cloud Storage 檔案上傳
- 🔄 檔案大小和格式驗證

#### Phase 3 (第4-5週)：轉錄核心功能
- 🔄 Google Speech-to-Text API 整合
- 🔄 Background job 處理 (Celery + Redis)
- 🔄 Speaker diarization 結果處理
- 🔄 WebSocket 進度推播

#### Phase 4 (第5-6週)：完善與優化
- 🔄 轉錄結果匯出 (VTT, SRT, JSON)
- 🔄 使用量追蹤和計劃限制
- 🔄 前端 UI 整合與測試

### 🎯 當前最高優先任務

1. **完成 Render Web Service 部署** (今日目標)
   - ✅ PostgreSQL 資料庫已建立並配置
   - 🎯 在 Render Dashboard 建立 Web Service
   - 🎯 設定所有必要環境變數
   - 🎯 驗證 API 端點正常運作

2. **Google Cloud 環境設定** (本週)
   - 🎯 建立新的 GCP 專案
   - 🎯 啟用 Cloud Storage 和 Speech-to-Text API
   - 🎯 建立服務帳號並下載 JSON 金鑰
   - 🎯 建立 Storage bucket (命名：coaching-audio-prod)

3. **Google OAuth 設定** (本週)
   - 🎯 在 Google Cloud Console 設定 OAuth 2.0
   - 🎯 設定授權重定向 URI
   - 🎯 取得 Client ID 和 Client Secret
   - 🎯 更新 Render 環境變數

### 🏗️ 架構現狀

#### ✅ 已驗證組件
- **Monorepo 結構**：apps/ + packages/ 架構穩定
- **資料模型**：SQLAlchemy 模型完整且測試通過
- **前端部署**：Cloudflare Workers 運行正常
- **開發環境**：Docker 容器化開發流程

#### 🔄 整合中組件
- **後端部署**：從本地開發 → Render 生產環境
- **資料庫**：從 SQLite 開發 → PostgreSQL 生產
- **認證系統**：Google OAuth 整合

#### 📝 待實作組件
- **檔案處理**：Google Cloud Storage 整合
- **轉錄服務**：Google Speech-to-Text API
- **背景任務**：Celery 工作佇列

### 💰 成本結構 (確認)
- **固定成本**：$15/月 (Render Web + PostgreSQL + GCS)
- **變動成本**：$0.016/分鐘 (Google Speech-to-Text)
- **目標毛利**：70-78% (Pro plan $599/月)

### 🔧 技術決策記錄

#### 資料庫設計決策
- **UUID 主鍵**：分散式系統友善，避免 ID 衝突
- **時間戳追蹤**：created_at, updated_at 自動管理
- **外鍵約束**：確保資料完整性
- **軟刪除**：考慮未來需求，目前使用硬刪除簡化邏輯

#### 測試策略決策
- **單元測試優先**：模型層 100% 覆蓋
- **SQLite 測試**：快速、隔離的測試環境
- **外鍵約束啟用**：確保測試環境與生產環境一致性
