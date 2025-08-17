# 測試腳本說明

本目錄包含腳本式測試工具，用於 API 測試和整合測試。

## 📁 目錄結構

```
tests/scripts/
├── README.md              # 本說明文件
└── api-tests/             # API 測試套件
```

## 🔧 API 測試套件 (api-tests/)

完整的 curl 基礎 API 測試腳本，用於驗證後端 API 功能。

### 可用的測試腳本

- **test_auth.sh** - 身份驗證測試
- **test_clients.sh** - 客戶管理測試
- **test_sessions.sh** - 教練會話測試
- **test_dashboard.sh** - 儀表板摘要測試
- **test_coach_profile.sh** - 教練檔案測試
- **run_all_tests.sh** - 主測試運行器

### 快速開始

```bash
# 啟動 API 伺服器
make run-api

# 運行所有測試
./tests/scripts/api-tests/run_all_tests.sh

# 或測試個別 API
./tests/scripts/api-tests/test_auth.sh
```

詳細使用說明請參考 `api-tests/README.md`。

## 整合測試腳本

以下腳本已從 `scripts/` 移至適當的測試目錄：

- `test_transcription_flow.py` → `tests/integration/test_transcription_flow.py`
- `test_status_tracking.py` → `tests/unit/services/test_status_tracking.py`

這些腳本現在遵循標準的 pytest 測試結構，可以通過 `make test` 或 `pytest` 運行。