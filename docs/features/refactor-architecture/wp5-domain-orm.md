# WP5 - Domain ↔ ORM 收斂 & Schema Migration

Last Updated: 2025-09-16 5:32 pm by ChatGPT

## 狀態
- 未開始（依賴 WP1~WP4）

## 目標
- 完成 domain model 與 ORM 的最終切分，移除 legacy ORM 依賴。
- 建立 Alembic migration，確保資料庫 schema 與新模型對齊。
- 盤點資料庫中不再使用或預計淘汰的欄位/資料表，提出整理清單與移除建議。

## 主要檢查項目
- [ ] Domain models (`src/coaching_assistant/core/models`) 與 ORM models (`src/coaching_assistant/infrastructure/db/models`) 完整映射。
- [ ] 所有 repositories 僅依賴 infrastructure ORM，無 legacy import。
- [ ] Alembic migration 可順利 upgrade/rollback，並包含欄位刪除/新增的資料搬移步驟。
- [ ] 撰寫 `schema_review.md`（位於本頁同層）列出疑似未使用欄位/資料表，並註明依據。
- [ ] `make lint`, `make test-unit`, `make test-integration`, `pytest tests/e2e` 全數通過（如需 slow 測試請提前公告）。
- [ ] 若 schema 變動影響前端/匯出格式，相關服務同步更新。

## 注意事項
- 刪除欄位前須確認資料備份與 rollback 計畫。
- 若需要中間層 mapping，可先留暫時轉換函式並標註 TODO。
- 請與 DevOps 協調 migration 執行時段，避免影響上線操作。

## 交付物
- Migration script、schema review 清單與影響分析。
- 程式碼與測試結果紀錄。
- 本頁狀態更新與結論。
