# Project Guidelines

## Documentation Organization

### /docs - 正式專案文檔
**用途：** 面向開發者、用戶、維護者的穩定文檔
**特性：** 正式、標準化、版本控制、公開使用
**更新權限：** 只有在用戶明確要求時才更新

內容類型：
- CHANGELOG.md - 版本變更記錄 (每次對話結束前，或是 git commit 時更新紀錄)
- 架構決策記錄 (ADR)
- 設計系統和 UI/UX 規範
- API 文檔和部署指南
- 用戶手冊和 FAQ
- 貢獻指南和代碼規範

### /memory-bank - Cline 工作記憶
**用途：** 專門為 Cline AI 助手設計的動態工作記憶
**特性：** 動態更新、上下文豐富、內部使用、決策支援
**更新權限：** Cline 可根據專案進展自動更新

核心文件結構：
- projectBrief.md - 專案核心概念 (必需)
- productContext.md - 產品定位與目標 (必需)
- activeContext.md - 當前工作重點 (必需)
- systemPatterns.md - 系統架構模式 (必需)
- techContext.md - 技術堆疊 (必需)
- progress.md - 進度追蹤 (必需)

## Cline Workflow Guidelines

### Task Management
- 每次任務前先使用 Plan 模式分析
- 避免一次修改超過3個檔案
- 專注於單一功能實現
- 遇到錯誤時先總結問題再尋求幫助

### Context Management
- 當對話變長時，使用 `/smol` 指令產生摘要並壓縮上下文
- 定期更新 memory-bank 文件反映當前狀態
- 保持 memory-bank 內容簡潔且聚焦當前狀態


## Code Style & Patterns

-   Generate API clients using OpenAPI Generator
-   Use TypeScript axios template
-   Place generated code in /src/generated
-   Prefer composition over inheritance
-   Use repository pattern for data access
-   Follow error handling pattern in /src/utils/errors.ts

## Testing Standards

-   Unit tests required for business logic
-   Integration tests for API endpoints
-   E2E tests for critical user flows

# Security

## Sensitive Files

DO NOT read or modify:

-   .env files
-   \*_/config/secrets._
-   \*_/_.pem
-   Any file containing API keys, tokens, or credentials

## Security Practices

-   Never commit sensitive files
-   Use environment variables for secrets
-   Keep credentials out of logs and output
