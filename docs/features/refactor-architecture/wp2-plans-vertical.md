# WP2 - Plans 垂直切片

Last Updated: 2025-09-16 5:32 pm by ChatGPT

## 狀態
- 未開始（待排程）

## 目標
- 將 Plans 相關 API 完整改為 Clean Architecture Lite 流程。
- 移除 API 層中的 SQLAlchemy Session 相依，確保僅透過 use case。
- 確保前端 Plans/Usage 頁面功能正常並通過測試。

## 主要檢查項目
- [ ] `src/coaching_assistant/api/v1/plans.py` 僅負責 request/response 轉換。
- [ ] `PlanRetrievalUseCase`、`PlanValidationUseCase` 有完整單元測試（涵蓋成功/失敗）。
- [ ] Repositories 採用 domain DTO 輸出並保留必要的 legacy 轉換。
- [ ] Integration 測試覆蓋 `/api/v1/plans/*` 主要路徑。
- [ ] `pytest tests/e2e/test_plan_limits_e2e.py` 與相關 E2E 測試通過。
- [ ] 前端 `npm run lint`、`npm run test`、Plans/Usage 頁面 smoke 測試完成。

## 注意事項
- 若需要調整 `PLAN_CONFIGS`，請同步檢查 pricing 映射與翻譯檔。
- 確保 `_get_plan_value` 等 helper 集中於 use case 或 utility，而非散落於 API。
- 任何 schema 需求變動需回報給 WP5。

## 交付物
- 程式碼更新與測試結果。
- 本頁狀態與重點結論。
