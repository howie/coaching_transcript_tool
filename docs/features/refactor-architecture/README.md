# Clean Architecture Lite Refactoring

本資料夾統整 Clean Architecture Lite 重構的成果與後續計畫。

## ✅ 已完成的里程碑

- **[Phase 1: Foundation Setup](./phase-1-foundation-done.md)**：建立 repositories ports、infrastructure 層級、使用案例與 in-memory 測試實作。
- **[Phase 2: API Migration & Hotfixes](./phase-2-api-migration-done.md)**：整合 `/api/v1` 結構、導入依賴注入、解決 plans/subscriptions 交易錯誤，確保主流程恢復可用。
- **[Critical Fix Logs](./critical-transaction-error-fix.md)**、**[User Repository Fix](./user-repository-fix-2025-09-15.md)**、**[Phase 3-A Hotfixes](./phase-3-a-session-hotfixes-done.md)**：記錄 2025-09 熱修補（回退至 legacy ORM、修復 transaction 問題）。

## 🔍 目前狀態快照（2025-Q1）

- Core 層已具備 `ports` 與主要 use cases，但多數 API 仍直接 import SQLAlchemy Session 或 legacy ORM（例：`src/coaching_assistant/api/v1/sessions.py`, `src/coaching_assistant/api/v1/plans.py`）。
- Repositories 以「混用 legacy ORM + domain model 轉換」維持可運作的 Hybrid 模式。
- 測試面已有 unit / integration / e2e 套件，E2E 測試位於 `tests/e2e/`，前端則由 `apps/web` (Next.js) 維護。

## 🎯 Clean Architecture Lite 目標

1. **清楚的層級切分**：API → Use Case → Repository → Infrastructure，容許 pragmatic 的 Legacy 相容層。
2. **可回歸的垂直切片**：每個工作包需能在單一 LLM session 內完成、TDD 驗證、通過 unit / integration / e2e / lint，並確認前端主要 flow 正常。
3. **持續可部署**：任何階段後，都可跑 `make lint`, `make test`, 以及 `pytest tests/e2e`。前端需透過 `npm run lint`、`npm run test`（在 `apps/web`）與 smoke run 驗證。

完整的 Clean Architecture Lite 後續路線請參考 **[Phase 3: Clean Architecture Lite Roadmap](./phase-3-domain-models.md)**。

## 📚 文件索引

- [Architectural Rules](./architectural-rules.md)
- [Success Metrics](./success-metrics.md)
- [Critical Schema Migration Guide](./critical-schema-migration-guide.md)
- [Phase 1: Foundation Setup](./phase-1-foundation-done.md)
- [Phase 2: API Migration & Hotfixes](./phase-2-api-migration-done.md)
- [Phase 3: Clean Architecture Lite Roadmap](./phase-3-domain-models.md)
- [Phase 3-A: Session Hotfixes](./phase-3-a-session-hotfixes-done.md)
- [Critical Transaction Error Fix](./critical-transaction-error-fix.md)
- [User Repository Fix (2025-09-15)](./user-repository-fix-2025-09-15.md)

---

**最新更新**：2025-09-16 5:32 pm by ChatGPT

**聯絡窗口**：Development Team
