# Changelog

All notable changes to this project will be documented in this file.

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
