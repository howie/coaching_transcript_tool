# Clean Architecture Lite Refactoring

本資料夾統整 Clean Architecture Lite 重構的成果、現況快照與後續計畫。內容分為「進行中指南」與「歷史紀錄 (./done)」。

## ✅ 已完成的里程碑

- **[Phase 1: Foundation Setup](./done/phase-1-foundation-done.md)**：建立 repository `ports`、初版 infrastructure 層與 in-memory 測試腳本。
- **[Phase 2: API Migration & Hotfixes](./done/phase-2-api-migration-done.md)**：導入 dependency injection、整合 `/api/v1` 結構、修復 plans/subscriptions 關鍵交易錯誤。
- **[Phase 3-A: Session Hotfixes](./done/phase-3-a-session-hotfixes-done.md)** 與 **[Critical Transaction Fix Logs](./done/critical-transaction-error-fix.md)**：記錄 2025-09 熱修補（rollback 至 legacy ORM、補強交易安全）。
- **[User Repository Fix (2025-09-15)](./done/user-repository-fix-2025-09-15.md)**：說明 legacy → domain model 轉換細節與風險。
- **[WP6-Cleanup-2: Payment Processing Vertical (2025-09-18)](./done/wp6-cleanup-2-implementation-complete.md)**：完整實作 ECPay 付款處理垂直切片，解決所有 11 個關鍵 TODO 項目，建立生產就緒的付款系統與 Clean Architecture 範例實作。

更多歷史紀錄請參考 `docs/features/refactor-architecture/done/`。

## 🔍 現況快照（2025-Q3）

- **Core 層**：`src/coaching_assistant/core/models/` 已提供 session、usage_log、transcript 等 dataclass；use case 主要集中於 `core/services/session_management_use_case.py:1`、`core/services/usage_tracking_use_case.py:18`、`core/services/subscription_management_use_case.py:17` 與 `core/services/plan_management_use_case.py:17`。
- **Hybrid 依賴**：plans / subscription use case 仍直接 import legacy ORM 模組，例如 `src/coaching_assistant/core/services/plan_management_use_case.py:19`、`src/coaching_assistant/core/services/subscription_management_use_case.py:19`；domain ↔ ORM 轉換由 repository 實作處理。
- **API 層**：Plans 與 Subscriptions 垂直切片已改用 dependency 注入 (`src/coaching_assistant/api/v1/plans.py:1`, `src/coaching_assistant/api/v1/subscriptions.py:1`)；整體仍有 88 個 `Depends(get_db)` 直接注入資料庫會話（`rg "Depends(get_db" src/coaching_assistant/api/v1 | wc -l`）。
- **核心例外**：`src/coaching_assistant/core/services/admin_daily_report.py:9` 已變更為使用 dependency injection pattern；`core/services/ecpay_service.py:11` 已在 WP6-Cleanup-2 中重構為 Clean Architecture 標準實作，使用 repository ports 與 HTTP client abstractions。
- **測試面**：unit / integration / e2e 測試均可用，Factory 與 Session/Subscription 垂直切片測試分別位於 `tests/unit/infrastructure/test_factory_circular_reference.py`、`tests/unit/services/test_session_management_use_case.py`、`tests/unit/services/test_subscription_management_use_case.py` 等；E2E 測試集中於 `tests/e2e/`。
- **前端**：Next.js 應用維護於 `apps/web`；Plans/Subscription 相關流程仍需 smoke 驗證以確保串接契約維持一致。

## 🎯 Clean Architecture Lite 目標

1. **層級分離**：API → Use Case → Repository → Infrastructure；在尚未完成的區域允許 pragmatic 的 legacy 相容層，並在文件中標註例外。
2. **垂直切片**：每個工作包需能在單一 LLM session 內完成，並於提交前通過 `make lint`, `make test`, `pytest tests/e2e`（必要時可加快選定標籤）。
3. **持續可部署**：後端保持上述測試、前端需跑 `npm run lint`、`npm run test` 與基本 smoke；部署前需更新本資料夾相關文件。

完整路線請參考 **[Phase 3: Clean Architecture Lite Roadmap](./phase-3-domain-models.md)**。

## 📚 文件索引

### 🔄 進行中工作包
- [WP6 – Cleanup Series Master Plan](./wp6-cleanup-master-plan.md)
- [WP6-Cleanup-1 – Speaker Roles](./wp6-cleanup-1-speaker-roles.md)
- [WP6-Cleanup-3 – Factory Migration](./wp6-cleanup-3-factory-migration.md)
- [WP6-Cleanup-4 – Analytics Exports](./wp6-cleanup-4-analytics-exports.md)
- [WP6-Cleanup-5 – Frontend Features](./wp6-cleanup-5-frontend-features.md)
- [WP6-Cleanup-6 – Infrastructure Polish](./wp6-cleanup-6-infrastructure-polish.md)

### 📋 架構指引
- [Architectural Rules](./architectural-rules.md)
- [Success Metrics](./success-metrics.md)
- [Phase 3: Clean Architecture Lite Roadmap](./phase-3-domain-models.md)
- [WP6 – Regression & Cleanup Overview](./wp6-cleanup.md)

### ✅ 已完成工作包
所有已完成的工作包移至：`./done/`
- **Phase 1-2**: Foundation, API Migration & Hotfixes
- **WP1-WP5**: Ports & Factories → Domain ↔ ORM Convergence (完整垂直切片)
- **WP6-Bug-Fixes**: 所有 P0/P1 關鍵錯誤修復
- **WP6-Cleanup-2**: Payment Processing Vertical (v2.21.0)

完整歷史紀錄：`./done/`

---

**最新更新**：2025-09-18 09:00 CST - Completed WP1-WP6 Documentation Cleanup & Organization

**聯絡窗口**：Development Team
