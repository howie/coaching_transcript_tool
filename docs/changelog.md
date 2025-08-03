# Changelog

All notable changes to this project will be documented in this file.

## [2.2.0-dev] - 2025-08-03 (Cloudflare Workers 環境變數修復)

### Fixed
- **環境變數建置時注入問題**: 
  - 修復 Next.js 在 Cloudflare Workers 部署時環境變數無效問題
  - 根本原因：`NEXT_PUBLIC_*` 環境變數是在建置時固化，而非運行時讀取
  - 解決方案：創建 `apps/web/.env.production` 文件，確保建置時正確注入 production API URL
- **CORS 跨域請求問題**:
  - 更新後端 `ALLOWED_ORIGINS` 支援 production 前端域名 `https://coachly.doxa.com.tw`
  - 修復前端 API client 健康檢查端點路徑從 `/health` 改為 `/api/health`

### Added
- **Cloudflare Workers 建置流程**: 新增 `build-frontend-cf` Makefile target 專門處理 Cloudflare 建置
- **環境分離機制**: 建立清楚的本地開發/預覽/生產環境配置分離
- **生產環境配置**: 創建 `apps/web/.env.production` 文件管理 production 專用環境變數

### Changed
- **部署流程優化**: `deploy-frontend` 現在使用完整建置流程 (`build` → `build:cf` → `wrangler deploy`)
- **Makefile 建置依賴**: 優化建置流程避免重複建置，提升效率
- **wrangler.toml 清理**: 移除無效的 `NEXT_PUBLIC_API_URL` 設定，加入適當註解說明

### Verified
- ✅ 成功部署到 Cloudflare Workers: `https://coachly-doxa-com-tw.howie-yu.workers.dev`
- ✅ JavaScript 檔案包含正確的 production API URL: `https://api.doxa.com.tw`
- ✅ 移除所有 localhost 引用，環境變數正確切換
- ✅ 三種環境完全分離：Local Dev (localhost:3000) / Local Preview (localhost:8787) / Production

## [2.1.0-dev] - 2025-08-02 (Monorepo 架構重構)

### Changed
- **Monorepo 架構實施**: 將專案重構為標準 monorepo 架構，提升可維護性和擴展性
  - `backend/` 拆分為 `apps/api-server/` (FastAPI 服務) 和 `apps/cli/` (CLI 工具)
  - `frontend/` 重命名為 `apps/web/` 
  - `gateway/` 重命名為 `apps/cloudflare/`
  - 新增 `packages/core-logic/` 統一管理核心業務邏輯
- **關注點分離**: API 服務和 CLI 工具完全獨立，各自擁有獨立的配置和部署能力
- **程式碼重用**: 將共同的業務邏輯提取到 `packages/core-logic/`，提升重用性

### Technical
- **測試重組**: 將測試檔案從 `apps/api-server/tests/` 移至 `packages/core-logic/tests/`
- **套件依賴**: API 服務和 CLI 工具都依賴 `packages/core-logic/` 進行業務邏輯處理
- **Docker 配置**: 更新 `docker-compose.yml` 和 Dockerfile 路徑以適應新架構
- **Makefile 更新**: 修改所有指令以支援新的目錄結構
- **路徑修正**: 調整 `requirements.txt` 中的相對路徑引用

### Verified
- ✅ API Docker 映像構建成功 (31.8s)
- ✅ CLI Docker 映像構建成功
- ✅ 所有 Makefile 指令正常運作
- ✅ 測試套件在新位置正常執行

## [2.0.0-dev] - 2025-08-01 (專案扁平化重構)

### Changed
- **Project Structure**: Flattened the project structure by moving `frontend`, `backend`, and `gateway` from the `apps/` directory to the root level. This improves clarity and simplifies pathing.

### Technical
- **NPM Workspaces**: Updated `package.json` to reflect the new flattened structure, changing from `"apps/*"` to explicit paths (`"frontend"`, `"backend"`, `"gateway"`).
- **Docker Configuration**: Modified `docker-compose.yml` and `Dockerfile.api` to correctly reference the new paths for the backend service.
- **Documentation**: Updated `README.md` to show the new project structure.

## [2.0.0-dev] - 2025-01-31 (配色系統修復)

### Fixed
- **首頁配色統一問題**: 
  - 修復 Footer 配色，從黑色背景改為深藍色 (`bg-nav-dark`)，與導航欄保持一致
  - 強調色從橙色統一改為淺藍色 (`text-primary-blue`)
  - 社媒圖標 hover 效果統一使用淺藍色主視覺
- **Dashboard 配色恢復原始設計**:
  - Header 背景恢復為淺藍色 (#71c9f1)，符合原始設計圖
  - Sidebar 背景改為淺藍色，與 header 完全一致
  - Header 和 Sidebar 文字改為白色，確保良好對比度
  - 統計數字 (24, 12, 8, 95%) 恢復為淺藍色 (#71c9f1)
  - 保持黃色強調色在按鈕和圖標的使用

### Changed
- **Tailwind 配置更新**: 新增 `dashboard-header-bg` 和 `dashboard-stats-blue` 專用顏色變數
- **組件配色統一**: 更新 Dashboard Header、Sidebar、Stats 組件使用統一的淺藍色配色
- **設計系統文件**: 更新 `docs/design-system.md` 版本至 1.1，記錄完整的配色修改

### Technical
- 所有配色修改經過瀏覽器測試驗證
- 響應式設計確保在不同裝置正確顯示
- 文字對比度符合可訪問性標準

## [1.0.0] - 2025-07-25

### Added
- **FastAPI Service**: Introduced a new API service based on FastAPI to provide transcript formatting functionalities over HTTP.
- **Core Logic Module**: Created a dedicated `coaching_assistant.core` module to encapsulate all business logic, making it reusable and testable.
- **API Endpoint**: Implemented a `POST /format` endpoint that accepts VTT file uploads and returns formatted files in either Markdown or Excel format.
- **Excel Export**: Added functionality to export transcripts to a styled `.xlsx` file, with alternating colors for speakers.
- **Configuration**: Added `pyproject.toml` dependencies for the API, including `fastapi`, `uvicorn`, and `python-multipart`.
- **Containerization**: Included `Dockerfile.api` and `docker-compose.yml` for easy local development and future deployment.
- **Documentation**: Added `docs/roadmap.md` and `docs/todo.md` to track project progress.

### Changed
- **Project Structure**: Refactored the project from a single CLI script into a modular service-oriented architecture.
- **VTT Parser**: Modified `parser.py` to accept file content as a string directly, instead of a file path, to better integrate with the API.
- **Excel Exporter**: Reworked `exporters/excel.py` to return an in-memory `BytesIO` object instead of writing to a file, which is crucial for sending file responses via the API. The function was also refactored to improve code quality.

### Removed
- **CLI Script**: Deleted the original `src/vtt.py` CLI script, as its functionality is now provided by the API service.
