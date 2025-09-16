# WP3 - Subscriptions 垂直切片

Last Updated: 2025-09-16 5:32 pm by ChatGPT

## 狀態
- 未開始（待排程）

## 目標
- 重構訂閱 / 付款流程，確保 transaction 與錯誤流程穩定。
- 清理 `SubscriptionRepository`、`SubscriptionManagementUseCase`，並補強授權/扣款測試。
- 驗證前端 Billing Flow（升級、續訂、取消、收據下載）。

## 主要檢查項目
- [ ] Repository 僅使用必要的 transaction 操作（`flush`、例外時 `rollback`）。
- [ ] Use case 對外回傳統一 DTO，覆蓋正常/逾期/例外情境。
- [ ] Integration 測試覆蓋授權、扣款、狀態查詢。
- [ ] `pytest tests/e2e/test_plan_upgrade_e2e.py`、`tests/e2e/test_payment_comprehensive_e2e.py` 全數通過。
- [ ] 前端 Billing 相關單元測試與 smoke 測試完成。
- [ ] 交易錯誤日誌有紀錄並確認無 regression。

## 注意事項
- 測試資料需遮蔽個資與金流敏感資訊。
- 若調整金流 webhook 邏輯，需同步通知後端 worker/cron 負責人。
- 完成後請更新文件並附上風險與後續建議。

## 交付物
- 程式碼更新與測試紀錄。
- 本頁狀態與結論摘要。
