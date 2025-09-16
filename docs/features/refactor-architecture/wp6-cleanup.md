# WP6 - Regression & Cleanup

Last Updated: 2025-09-16 5:32 pm by ChatGPT

## 狀態
- 未開始（最終階段）

## 目標
- 移除所有暫時性相容層與 Legacy 代碼。
- 更新架構規則、成功指標與監控腳本，防止回歸。
- 確保整體系統在新的 Clean Architecture Lite 下可穩定部署。

## 主要檢查項目
- [ ] Legacy 模組（`src/coaching_assistant/models/*` 等）已確認刪除或標記淘汰。
- [ ] `Architectural Rules`、`Success Metrics` 文件同步更新。
- [ ] CI/CD 腳本（Makefile/GitHub Actions）含 architecture check、lint、unit、integration、e2e、前端測試。
- [ ] 全套測試（含前端 `npm run build`）通過並附紀錄。
- [ ] 監控/告警更新，能捕捉主要 use case 失敗或性能退化。
- [ ] README、CHANGELOG、發版說明同步完成。

## 注意事項
- 在刪除舊程式前，確認所有利害關係人已驗收。
- 若仍需保留 fallback，請標註期限與負責人。
- 建議在 staging/production 進行 smoke 測試後才標記完成。

## 交付物
- 程式碼調整與測試結果。
- 本頁狀態更新與總結。
