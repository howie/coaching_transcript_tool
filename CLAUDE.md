# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Backend Development (Python)
- **Install dependencies**: `make dev-setup` or `pip install -e packages/core-logic --break-system-packages`
- **Run API server**: `make run-api` (starts FastAPI at http://localhost:8000)
- **Run tests**: `make test` or `pytest packages/core-logic/tests/`
- **Run linting**: `make lint` (runs flake8 on core-logic)
- **Run single test**: `pytest packages/core-logic/tests/test_processor.py::test_specific_function -v`

### Frontend Development (Next.js)
- **Install dependencies**: `make install-frontend` or `cd apps/web && npm install`
- **Run dev server**: `make dev-frontend` (starts Next.js at http://localhost:3000)
- **Build frontend**: `make build-frontend`
- **Deploy to Cloudflare**: `make deploy-frontend`
- **Run tests**: `cd apps/web && npm test`
- **Run linting**: `cd apps/web && npm run lint`

### Docker Operations
- **Build Docker images**: `make docker` (builds both API and CLI images)
- **Run CLI container**: `make docker-run-cli INPUT=./input.vtt OUTPUT=./output.md`
- **Run API service**: `docker-compose up -d`

## Architecture Overview

This is a monorepo project using Python (FastAPI) for backend and Next.js for frontend, designed for serverless deployment.

### Key Components

1. **apps/web/** - Next.js frontend application
   - Deployed to Cloudflare Workers using OpenNext
   - Uses Tailwind CSS, React Hook Form, and Zustand for state management
   - API client configured to use different endpoints based on environment

2. **apps/api-server/** - FastAPI backend service
   - Core transcript processing logic
   - Handles VTT to Markdown/Excel conversion
   - Supports Chinese language conversion (Simplified to Traditional)

3. **apps/cli/** - Command-line interface
   - Standalone tool for transcript processing
   - Uses the same core logic as API

4. **packages/core-logic/** - Shared Python business logic
   - VTT parser and processors
   - Excel and Markdown exporters
   - Chinese converter utilities

### API Environment Configuration
- **Local Development**: API runs on `http://localhost:8000`
- **Production**: API deployed to `https://api.doxa.com.tw`
- Environment detection is automatic based on build/runtime context

### File Processing Flow
1. User uploads VTT file through web interface
2. Frontend validates file and sends to API
3. API parses VTT content and applies transformations
4. Processed content returned as Markdown or Excel format
5. Frontend allows user to download the result

### Testing Strategy
- Backend: pytest with test data in `packages/core-logic/tests/data/`
- Frontend: Jest with Testing Library
- Always verify test framework before running tests

### Important Notes
- The project uses `--break-system-packages` for pip installs due to Python environment setup
- Makefile provides unified interface for all common operations
- Memory bank files in `memory-bank/` contain detailed context about the project
- CORS is enabled in production for cross-origin API requests

### API Response Format Handling
When backend returns i18n keys instead of actual labels (e.g., dropdown options):
- Backend returns: `{"value": "referral", "labelKey": "clients.sourceReferral"}`
- Frontend needs to convert `labelKey` to actual label using i18n `t()` function
- Example transformation:
  ```typescript
  const processedOptions = apiData.map((item: any) => ({
    value: item.value,
    label: item.labelKey ? t(item.labelKey) : item.label || item.value
  }));
  ```
- Always check if backend returns `labelKey` instead of `label` when dropdowns appear empty
- Don't assume API failure - check the actual response format first


# Claude Code 前端單元測試規則 (claude.md)

## 目標
指導 Claude Code 以最佳實踐生成清晰且有效的前端單元測試。

---

## Rule 1：明確指定測試範圍與功能
- 清楚描述要測試的元件或函式名稱，及其功能行為。
- 強調測試目標是驗證輸入輸出、狀態變化或事件觸發。

## Rule 2：指定使用的測試框架與工具
- 明確告知要使用的測試框架，如 Jest、React Testing Library。
- 如需模擬 API 呼叫或事件，請說明需使用的 mock 方法。

## Rule 3：採用 Test-Driven Development (TDD) 流程
- 先由 Claude 產生只能通過測試的測試案例，且不寫實作。
- 讓用戶驗證測試失敗是正常狀態。
- 再生成讓測試通過的實作程式碼，明確不修改測試。
- 重複迭代直到測試全部通過。

## Rule 4：測試內容與格式要求
- 包含測試多種輸入條件及邊界案例。
- 測試中加入適當的 mock 或 stub，避免外部資源依賴。
- 以簡潔且易懂的描述來定義測試用例。

## Rule 5：輸出格式
- 使用標準 Jest/React Testing Library 語法。
- 必須包含描述性測試用例名稱。
- 確保代碼可直接運行。

## Rule 6：審查與修正
- 自動執行 lint / type check，如有錯誤須自動修正。
- 產生測試後，請模擬執行並報告結果。
- 對測試結果異常或失敗給出診斷與修正建議。

---

## 使用範例 Prompt

