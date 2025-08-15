# Scripts 使用說明

## sync_progress_to_changelog.py

根據 `.clinerules/progress-changelog-rules.md` 規則自動同步已完成項目的腳本。

### 功能
- 自動解析 `docs/project-status.md` 中的 ✅ 已完成項目
- 生成格式化的 changelog 快照記錄
- 將已完成項目移至 `docs/changelog.md`
- 清理 `project-status.md` 保持精簡

### 使用方式

**預覽模式（推薦先執行）**：
```bash
python3 scripts/sync_progress_to_changelog.py --dry-run --verbose
```

**實際同步**：
```bash
python3 scripts/sync_progress_to_changelog.py
```

**參數說明**：
- `--dry-run`: 預覽模式，不修改實際文件
- `--verbose`: 詳細輸出，顯示所有已完成項目列表
- `--help`: 顯示幫助信息

### 執行時機

建議在以下情況執行：
- 每週固定時間（建議每週一）
- 完成重要功能或階段性任務後
- `project-status.md` 文件過長，需要清理時

### 執行結果

腳本會：
1. 在 `docs/changelog.md` 頂部插入新的進度快照
2. 從 `docs/project-status.md` 移除已完成項目
3. 保持兩個文件的 Markdown 格式完整性

### 注意事項

- 執行前建議先運行 `--dry-run` 模式預覽
- 腳本會自動備份重要內容到 changelog
- 支援中英文內容混合處理
- 自動處理日期分組和格式化

### 示例輸出

```
🚀 Progress to Changelog 同步工具
==================================================
📊 統計結果:
   - 已完成項目: 64
   - 活躍項目: 145
📝 生成 changelog 快照...
🎉 同步完成！
