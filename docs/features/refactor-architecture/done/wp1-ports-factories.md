# WP1 - Ports & Factories Hardening

Last Updated: 2025-09-16 7:15 pm by Claude

## 狀態
✅ **已完成** (2025-09-16)

## 目標
- 釐清所有 use case 所需的 repository 依賴，避免遺漏。
- 為 factories 的建立流程補上自動化測試與文件。
- 保留 Hybrid 模式下的 legacy ORM 轉接點，並加註 TODO 供後續移除。

## 主要檢查項目
- [x] `src/coaching_assistant/infrastructure/factories.py` 無遞迴/循環依賴問題。
- [x] Repository factory 與 use case factory 均有單元測試覆蓋。
- [x] 測試檔（擴充 `tests/unit/infrastructure/test_factory_circular_reference.py`）涵蓋所有新 factory。
- [x] `make lint`, `make test-unit`, `make test-integration` 皆成功。
- [x] README/文件標記 legacy 暫時方案。

## 實際完成內容

### 1. Factory 問題修正
✅ **修正 RepositoryFactory 不一致的實例化模式**
- 修正 `create_subscription_repository` 方法直接實例化問題
- 統一使用 factory 函數調用模式

### 2. 新增遺漏的 Factory 方法
✅ **新增 SpeakerRoleServiceFactory 類別**
- `create_speaker_role_assignment_use_case`
- `create_segment_role_assignment_use_case`
- `create_speaker_role_retrieval_use_case`
- 所有方法均正確注入依賴並使用正確的建構子參數

### 3. 測試覆蓋率擴充
✅ **擴充測試檔案涵蓋所有 factory 類別**
- `TestRepositoryFactory` (6 個 repository 方法)
- `TestUsageTrackingServiceFactory` (2 個 use case)
- `TestSessionServiceFactory` (11 個方法)
- `TestSpeakerRoleServiceFactory` (3 個新方法)
- `TestPlanServiceFactory` (2 個 use case)
- `TestSubscriptionServiceFactory` (已存在，3 個 use case)
- `TestLegacyCompatibilityFunctions` (1 個 legacy 函數)
- `TestFactoryMemoryManagement` (記憶體管理測試)

### 4. 文件與 TODO 標記
✅ **新增 legacy 轉換點標記**
- 在 `get_usage_tracking_service` 函數標註 DEPRECATED
- 新增 TODO 標記指向後續工作包 (WP2-WP4)
- 補充完整的 docstring 說明

### 5. 測試驗證結果
✅ **所有測試通過**
- **34 個測試全部通過** (從 21 失敗改善為 0 失敗)
- 無循環依賴問題
- 無記憶體洩漏問題
- 所有 factory 方法能正確建立物件

## 交付物
- ✅ **程式碼變更**: 修正 factory 不一致問題，新增 SpeakerRoleServiceFactory
- ✅ **測試完整性**: 34 個測試涵蓋所有 factory 方法
- ✅ **文件更新**: 完整 TODO 標記與文件說明
- ✅ **驗證通過**: 所有測試通過，無 circular dependency 問題

## 後續工作
- **WP2**: Plans 垂直切片 - 使用已驗證的 factory pattern
- **WP3**: Subscriptions 垂直切片 - 清理 transaction 問題
- **WP4**: Sessions 垂直切片 - 移除直接 SQLAlchemy 依賴
- **WP5+**: 移除 legacy 相容函數（如 `get_usage_tracking_service`）
