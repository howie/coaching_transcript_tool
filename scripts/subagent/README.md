# Subagent Scripts

這個目錄包含各種 Claude Code subagent 使用的專用腳本。

## 現有 Subagent Scripts

### database_query.py
**用途**: 為 `database-query-analyzer` subagent 提供資料庫查詢功能

**支援命令**:
```bash
# 查詢系統狀況
python scripts/subagent/database_query.py query_system_status

# 查詢最近活動
python scripts/subagent/database_query.py query_recent_activity  

# 查詢用戶增長 (預設7天)
python scripts/subagent/database_query.py query_user_growth

# 查詢用戶增長 (自訂期間)
python scripts/subagent/database_query.py query_user_growth --period=30

# 檢查系統健康狀況
python scripts/subagent/database_query.py check_system_health
```

**環境變數**: 需要設定 `DATABASE_URL` 來連接到正確的資料庫

## 使用方式

這些腳本主要由 Claude Code 的 subagent 系統自動調用，但也可以直接執行用於測試或手動查詢。

## 新增 Subagent Scripts

當需要為新的 subagent 建立專用腳本時：

1. 在此目錄建立新的 Python 檔案
2. 確保腳本支援命令行參數
3. 更新此 README 文件
4. 在相關的 subagent markdown 檔案中記錄使用方式