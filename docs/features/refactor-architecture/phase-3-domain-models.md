# Phase 3: Clean Architecture Lite Roadmap

Last Updated: 2025-09-16 5:32 pm by ChatGPT

本文件重新規劃 Phase 3，目標是在 **Clean Architecture Lite** 前提下完成剩餘重構。Lite 版代表：

- Core 層維持「用例 + 介面 (`ports`) + domain model」的乾淨界線。
- Infrastructure 層允許 pragmatic 的 legacy 相容層（例如：沿用舊 ORM model），但所有 API / Use Case 僅透過 ports 互動。
- 每個工作包都能在單一 LLM session 內完成：包含需求理解、TDD/Refactor、程式碼審查與測試執行（unit、integration、e2e、lint、前端 smoke）。

---

## 0. 共同原則與前置作業

1. **分支策略**：每個工作包使用獨立 feature branch，命名格式 `feature/ca-lite/<work-package>`。
2. **平行作業**：工作包預設可平行進行，僅需在介面變更時同步契約；若需要資源調度，由整合人每週協調。
3. **TDD 驗證流程**（每包至少一次）：
   - `make lint`
   - `make test-unit`
   - `make test-integration`
   - `pytest tests/e2e -m "not slow"`（如需要全量，請與 DevOps 協調時間）
   - 前端 (`apps/web`)
     - `npm install`（首次）
     - `npm run lint`
     - `npm run test`
     - `npm run dev` → 手動 smoke：登入、Plans/Subscriptions/Sessions 主流程載入
4. **使用者價值導向的 E2E**：每次 E2E 執行需記錄覆蓋的關鍵使用者旅程與觀測到的價值（例如：成功完成方案升級流程）。
5. **文件同步**：完成後更新本檔案與對應 feature 子文件，標註日期與狀態。
6. **觀測點**：保留現有日誌級別，新增/調整時需經過 code review。
7. **本機驗證能力**：允許在開發機上執行上述測試，確保每個工作包在提交前完成本機自我驗證。

---

## 工作包總覽

| 編號 | 名稱 | 目標 | 主要驗證 |
|------|------|------|-----------|
| [WP1](./wp1-ports-factories.md) | Ports & Factories Hardening | 確保所有 use case 依賴注入與 repository 實作一致，建立 regression 測試腳本 | Unit / Integration / Lint |
| [WP2](./wp2-plans-vertical.md) | Plans 垂直切片 | Plans API → Use Case → Repository 完整走 Clean Architecture Lite | Unit / Integration / `tests/e2e/test_plan_*` / 前端 Plans Page |
| [WP3](./wp3-subscriptions-vertical.md) | Subscriptions 垂直切片 | Subscription pipeline 清理、補齊授權/支付整合測試 | Unit / Integration / `tests/e2e/test_payment_*` / 前端 Billing Flow |
| [WP4](./wp4-sessions-vertical.md) | Sessions 垂直切片 | Sessions API 解除直接 SQLAlchemy 相依，補上錄音上傳流程的 e2e | Unit / Integration / 新增 `tests/e2e/test_session_*` / 前端 Session Console |
| [WP5](./wp5-domain-orm.md) | Domain ↔ ORM 收斂 & Schema Migration | 完成模型切分、建置 Alembic migration、移除 legacy ORM | Unit / Integration / e2e 全量 / DB migration dry-run |
| [WP6](./wp6-cleanup.md) | Regression & Cleanup | 刪除暫時性相容層、更新文件與監控指標 | Full test suite / Observability |

各工作包都應留下 README snippet（追加在 `docs/features/refactor-architecture/` 底下）以利下個 session 接續。

---

## WP1. Ports & Factories Hardening

**目的**：鞏固 Phase 1/2 打下的基礎，確保任何 use case 建構都能穩定取得對應 repository，同時提供 regression 測試以保護 factories。

**範圍**
- 清理 `src/coaching_assistant/infrastructure/factories.py` 的重複程式與暫時邏輯。
- 為所有 `create_*_repository`、`create_*_use_case` 提供 unit 測試（擴充 `tests/unit/infrastructure/test_factory_circular_reference.py`）。
- 明確標註 legacy ORM 轉接處（EX: user/session repository）。

**預期成果**
- 工廠函式有對應 unit test + integration smoke。
- README 補上「如何新增新的 port/factory」指南。

**建議流程**
1. 撰寫/補強 test double，顯式檢查是否使用正確 repository 實作。
2. 若需要新增 helper modules，範圍限制在 infrastructure 層。
3. 確認 `make lint` / `make test-unit` / `make test-integration` 全部通過。

**交付物**
- 測試結果截圖或記錄。
- `docs/features/refactor-architecture/wp1-ports-factories.md`（新增）簡述重點、日期。

---

## WP2. Plans 垂直切片

**目的**：計畫 / 可用方案 API 完整遵循 Clean Architecture Lite，API 僅做轉換與授權，所有商業邏輯收斂到 use cases。

**範圍**
- `src/coaching_assistant/api/v1/plans.py`
- `src/coaching_assistant/core/services/plan_management_use_case.py`
- 關聯 repositories (`plan_configuration`, `subscription`, `user`)
- 前端 `apps/web` Plans/Usage 頁面。

**步驟建議**
1. **用例整理**：列出需要的輸入/輸出 DTO，補上單元測試。
2. **API 清理**：移除 API 內直接的 SQLAlchemy 操作，透過依賴注入取得 use case。
3. **Repository 調整**：保留 legacy ORM，但輸出固定使用 domain model + DTO。
4. **測試**：
   - `pytest tests/unit/services/test_plan_*`
   - `pytest tests/integration/api/test_plans_*`
   - `pytest tests/e2e/test_plan_limits_e2e.py`
   - 前端 `npm run test`（需要新增/更新 Plans 頁面測試）
   - 手動 smoke：切換方案、查看可用度。
   - 產出簡短紀錄：此輪 E2E 驗證到的使用者價值與異常觀察。

**交付物**
- `docs/features/refactor-architecture/wp2-plans-vertical.md`
- 更新 README “目前狀態” 欄位

---

## WP3. Subscriptions 垂直切片

**目的**：整理訂閱/付款流程，防止再出現 transaction rollback 問題，同時對應台灣常見金流流程（ECPay）。

**範圍**
- `src/coaching_assistant/core/services/subscription_management_use_case.py`
- `src/coaching_assistant/infrastructure/db/repositories/subscription_repository.py`
- `src/coaching_assistant/api/v1/subscriptions.py`
- 前端 Billing / Upgrade 頁面（`apps/web/components/billing/*`）。

**步驟建議**
1. 強化 use case 的錯誤處理與回傳 DTO，補齊單元測試。
2. repository 確保僅有 transaction-safe 操作（`flush` / `rollback`），新增 integration 測試覆蓋授權/付款流程。
3. API 僅做驗證與回傳 mapping。
4. E2E 測試：
   - `pytest tests/e2e/test_payment_comprehensive_e2e.py`
   - `pytest tests/e2e/test_plan_upgrade_e2e.py`
   - 若需新案例（例如退款），請新增檔案並標註 `@pytest.mark.slow`。
   - 產出簡短紀錄：此輪 E2E 驗證到的使用者價值與異常觀察。
5. 前端：
   - `npm run lint`
   - `npm run test`（補齊 Billing 組件測試）
   - 手動 smoke：升級、取消、下載收據。

**交付物**
- `docs/features/refactor-architecture/wp3-subscriptions-vertical.md`

---

## WP4. Sessions 垂直切片

**目的**：重構錄音/轉錄相關 API，解除與 SQLAlchemy Session 的強耦合，支援後續 domain 模型擴充。

**範圍**
- `src/coaching_assistant/api/v1/sessions.py`
- `src/coaching_assistant/core/services/session_management_use_case.py` 及相關 use cases
- `src/coaching_assistant/infrastructure/db/repositories/session_repository.py`
- 任務佇列 / background job（若有使用 `tasks/transcription_tasks.py`）。
- 前端 Session Console。

**步驟建議**
1. 釐清必要的 use cases（建立 session、上傳、查詢狀態、下載 transcript）。
2. API 僅保留 request 校驗與 response 封裝。
3. Repository 保留 legacy ORM 轉接但統一出口為 domain model。
4. 測試：
   - 新增 `tests/unit/services/test_session_management_use_case.py`
   - `pytest tests/integration/api/test_sessions_*`
   - 新增 E2E：`tests/e2e/test_session_workflow_e2e.py`（上傳 → 等待完成 → 下載）
   - 產出簡短紀錄：此輪 E2E 驗證到的使用者價值與異常觀察。
5. 前端：手動錄音上傳流程、轉錄結果顯示。

**交付物**
- `docs/features/refactor-architecture/wp4-sessions-vertical.md`

---

## WP5. Domain ↔ ORM 收斂與 Schema Migration

**目的**：完成 domain model 與 ORM 的最終切分與資料庫 schema 更新，移除 hybride 依賴。

**範圍**
- `src/coaching_assistant/core/models/*`
- `src/coaching_assistant/infrastructure/db/models/*`
- `alembic/versions/` 新增 migration
- 調整 repositories 使其僅依賴 infrastructure ORM。
- 審視現有資料庫 schema，列出不再使用或待淘汰的欄位/資料表，提供移除建議與影響分析。

**步驟建議**
1. 定義 domain model（使用 dataclass / pydantic）與 ORM 互轉介面。
2. 撰寫 Alembic migration：新增缺漏欄位（ex: `progress_percentage`）、處理 enum/string 差異。
3. 整合測試：
   - `alembic upgrade head`（dev DB）
   - `pytest tests/integration`、`pytest tests/e2e`
   - 若 schema 變動影響前端，更新 `apps/web` 對應 DTO。
   - 產出簡短紀錄：此輪 E2E 驗證到的使用者價值與異常觀察。
4. 整理文件：更新 `critical-schema-migration-guide.md` 為實際操作紀錄。

**交付物**
- Migration script + rollback 說明
- `docs/features/refactor-architecture/wp5-domain-orm.md`

---

## WP6. Regression & Cleanup

**目的**：確認整體成果、刪除暫時性相容層、建立觀測指標。

**範圍**
- 移除 legacy ORM 檔案（如 `src/coaching_assistant/models/` 中已替換完成的檔案）
- 更新 `Architectural Rules`、`Success Metrics`
- 建立持續整合腳本（Makefile / GitHub Actions）保護層級依賴。

**測試與驗證**
- 完整跑 `make lint`, `make test`, `pytest tests/e2e`
- 前端 `npm run lint`, `npm run test`, `npm run build`
- 若有 staging，執行 smoke 測試並更新 `tests/e2e/E2E_TEST_SUMMARY.md`
 - 產出簡短紀錄：此輪 E2E 驗證到的使用者價值與異常觀察。

**交付物**
- `docs/features/refactor-architecture/wp6-cleanup.md`
- README 最終狀態更新

---

## 完成定義 (Definition of Done)

- 每個工作包都有：
  - 對應程式碼變更與測試
  - 更新後的文件與驗證紀錄
  - PR checklist：
    - [ ] `make lint`
    - [ ] `make test-unit`
    - [ ] `make test-integration`
    - [ ] `pytest tests/e2e`
    - [ ] 前端 `npm run lint`
    - [ ] 前端 `npm run test`
    - [ ] 手動 smoke 或錄影
- README 與各子文件呈現最新狀態，移除已完成的 TODO。
- `Success Metrics` 內指標（架構違規、coverage、e2e pass 率）可自動報告。

---

## 後續建議

- 若下一階段需要更嚴格的 Clean Architecture，可在 WP6 完成後評估是否拆分成 microservice 或導入 CQRS。
- 定期（每 sprint）回顧工作包顆粒，確保仍能在單一 LLM session 內完成。
- 針對跨領域議題（例如金流、取號）建議在 WP3 或 WP4 中同步與 Domain Expert 討論，避免重構後行為偏差。
