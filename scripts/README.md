# Scripts 使用說明

本目錄包含專案的運維腳本，按功能分類組織。測試相關腳本已移至 `tests/scripts/` 目錄。

## 📁 目錄結構

```
scripts/
├── README.md              # 本說明文件
├── monitoring/            # 監控和狀態檢查
├── database/              # 資料庫維護腳本
├── security/              # 安全檢查腳本
├── setup/                 # 環境設置腳本
└── maintenance/           # 維護和同步腳本
```

## 🔍 監控腳本 (monitoring/)

### beta_monitoring.py
追蹤 beta 階段的使用統計和成本監控。

### check_celery_status.py
檢查 Celery 工作程序的狀態和已註冊任務。

### monitor_stt_logs.sh
監控 Google STT API 調用的日誌輸出。

### check_transcription_status.sql
SQL 查詢腳本，檢查轉錄任務的狀態分布。

## 🗄️ 資料庫腳本 (database/)

### seed_beta_plan_configs.py
為 beta 階段建立保守的計畫配置。

### seed_plan_configurations.py
建立正式的訂閱計畫配置。

## 🔒 安全檢查 (security/)

### check-security.sh
檢查是否有敏感文件被意外提交到版本控制。

## ⚙️ 環境設置 (setup/)

### setup_env/
包含 Google Cloud Storage 環境設置腳本。

## 🔧 維護腳本 (maintenance/)

### sync_progress_to_changelog.py

根據 `.clinerules/progress-changelog-rules.md` 規則自動同步已完成項目的腳本。

#### 功能
- 自動解析 `docs/project-status.md` 中的 ✅ 已完成項目
- 生成格式化的 changelog 快照記錄
- 將已完成項目移至 `docs/changelog.md`
- 清理 `project-status.md` 保持精簡

#### 使用方式

**預覽模式（推薦先執行）**：
```bash
python3 scripts/maintenance/sync_progress_to_changelog.py --dry-run --verbose
```

**實際同步**：
```bash
python3 scripts/maintenance/sync_progress_to_changelog.py
```

**參數說明**：
- `--dry-run`: 預覽模式，不修改實際文件
- `--verbose`: 詳細輸出，顯示所有已完成項目列表
- `--help`: 顯示幫助信息

#### 執行時機

建議在以下情況執行：
- 每週固定時間（建議每週一）
- 完成重要功能或階段性任務後
- `project-status.md` 文件過長，需要清理時

#### 執行結果

腳本會：
1. 在 `docs/changelog.md` 頂部插入新的進度快照
2. 從 `docs/project-status.md` 移除已完成項目
3. 保持兩個文件的 Markdown 格式完整性

#### 注意事項

- 執行前建議先運行 `--dry-run` 模式預覽
- 腳本會自動備份重要內容到 changelog
- 支援中英文內容混合處理
- 自動處理日期分組和格式化

#### 示例輸出

```
🚀 Progress to Changelog 同步工具
==================================================
📊 統計結果:
   - 已完成項目: 64
   - 活躍項目: 145
📝 生成 changelog 快照...
🎉 同步完成！
