#  Clinerules：Progress 與 Changelog 分層規則（Token 優化版）

##  規則目標
確保 `progress.md` 保持極簡、聚焦於當前進度與問題；而所有過往歷程、版本紀錄、已完成任務則儲存至 `docs/changelog/changelog.md`。  
目的為節省 Token 並維持 AI 有效理解上下文。

##  Progress.md 使用規則

###  必須包含的內容：
- 尚未完成任務（To-do / In Progress）
- 當前活躍開發重點或修正項目
- 已知待處理問題或重大風險
- 最新一週內的即時進度摘要

###  不應包含的內容（應移至 changelog）：
- 已完成之 Tasks / Features
- 整體版本演進紀錄
- 冗長任務歷程或多階段討論
- 舊任務沿革與備註

---

##  docs/changelog/changelog.md 使用規則

###  應包含的內容：
- 已完成任務與功能（包含完成時間）
- 各階段 release notes / 版本變更摘要
- 重要決策背景與跨階段問題追蹤

###  建議格式（依時間記錄）：
```
## 2025-08-03 Progress Snapshot
- ✅ 完成 feat: search 增加 facet filter
- ✅ 修復 bug #45：錯誤分類導致計算異常
- 🧭 決策紀錄：取消原本 multi-step prompt 模組設計
```

### 💡 工作原則：
- changelog 為歷史儲存區，平時不會載入 AI context
- 需要查閱時才進行調用，以免增加 token 負擔

---

## 🔁 更新流程建議

可採手動或腳本自動化流程，如使用 `scripts/sync_progress_to_changelog.py`

- ✅ 時機：
  - 每週固定（建議每週一）
  - 任務完成或交付階段後

- ✅ 處理：
  - 將已完成內容從 `progress.md` 移至 `changelog.md`
  - 移除過期或不再進行之任務與決策內容

---

## 🎯 整體架構提醒

| 檔案名稱             | 功能定位                   |
|----------------------|----------------------------|
| `activeContext.md`   | 當前上下文焦點與即時推論參照 |
| `progress.md`        | 活躍任務、未解問題、短期摘要 |
| `changelog.md`       | 長期歷史、決策紀錄、完成事項 |





