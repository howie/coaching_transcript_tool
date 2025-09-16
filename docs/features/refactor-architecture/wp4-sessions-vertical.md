# WP4 - Sessions 垂直切片

Last Updated: 2025-09-16 5:32 pm by ChatGPT

## 狀態
- 未開始（待排程）

## 目標
- 讓 Sessions 相關 API 完全解耦 SQLAlchemy Session，統一透過 use case。
- 強化錄音上傳、狀態查詢、轉錄下載的流程與測試。
- 確保前端 Session Console 可順利完成典型使用者旅程。

## 主要檢查項目
- [ ] `src/coaching_assistant/api/v1/sessions.py` 僅進行驗證與輸出轉換。
- [ ] `SessionManagement` 系列 use case 具備單元測試覆蓋。
- [ ] `SessionRepository` 仍支援 legacy ORM，但 domain output 一致。
- [ ] Integration 測試涵蓋建立、更新狀態、拉取 transcript。
- [ ] 新增或更新 `tests/e2e/test_session_workflow_e2e.py`（或同等）並通過。
- [ ] 前端 `npm run test` 涵蓋 Session 相關元件，且 smoke 測試通過。

## 注意事項
- 注意背景任務（Celery/Worker）與 API 層的責任切分。
- 若要重構檔案上傳流程，需與 GCS/S3 設定保持相容。
- 需紀錄任何暫時 fallback 案，供 WP6 移除。

## 交付物
- 程式碼與測試結果。
- 本頁狀態更新與重點摘要。
