# Clean Architecture Refactoring - Current Status

**Last Updated**: 2025-09-21
**Overall Progress**: 90% Complete - Core refactoring finished, cleanup in progress

## Current Architecture Snapshot

### ✅ **Completed Areas**

#### **Core Clean Architecture Implementation**
- **Repository Pattern**: All core repositories implement clean ports (✅)
- **Use Cases**: Business logic extracted into testable services (✅)
- **Domain Models**: Core entities isolated from infrastructure (✅)
- **Factory System**: Dependency injection established (✅)

#### **Vertical Slices Complete**
- **Plans API**: `/api/v1/plans/*` fully using Clean Architecture (✅)
- **Subscriptions API**: `/api/v1/subscriptions/*` complete with payment processing (✅)
- **Sessions Core**: Session management use cases implemented (✅)
- **Payment Processing**: Full ECPay integration with proper error handling (✅)
- **Speaker Roles**: Complete transcript functionality with role assignment (✅)

### ⚠️ **Legacy Areas Still Requiring Migration**

#### **Direct Database Access (89 endpoints remaining)**
```bash
# Command to check current count:
rg "Depends(get_db)" src/coaching_assistant/api/v1 | wc -l
# Current: 89 matches (down from 120+)
```

**Legacy endpoint distribution:**
- `dependencies.py`: 19 (factory methods)
- `billing_analytics.py`: 10 endpoints
- `coach_profile.py`: 8 endpoints
- `clients.py`: 7 endpoints
- `coaching_sessions.py`: 7 endpoints
- `usage.py`: 7 endpoints
- `usage_history.py`: 7 endpoints
- `auth.py`: 5 endpoints
- `user.py`: 5 endpoints
- `admin.py`: 7 endpoints
- `transcript_smoothing.py`: 3 endpoints
- `admin_reports.py`: 2 endpoints
- `sessions.py`: 1 endpoint
- `summary.py`: 1 endpoint

**High-priority legacy endpoints:**
- Session upload endpoints (`/api/v1/sessions/{id}/upload-url`, `/api/v1/sessions/{id}/start-transcription`)
- Transcript retrieval (`/api/v1/sessions/{id}/transcript`)
- User management endpoints
- Analytics and reporting endpoints

#### **Legacy Services in Core Layer**
```bash
# Command to check current count:
rg "from sqlalchemy" src/coaching_assistant/core/services
# Current: 2 files, 5 import statements
```

1. **`admin_daily_report.py`** - Analytics service with direct SQLAlchemy queries
   - 4 SQLAlchemy imports: `Session`, `func`, `and_`, `desc`, `DECIMAL`, `case`, `or_`
   - Lines 9, 10, 817, 818
2. **`ecpay_service.py`** - Payment service (partially migrated in WP6-Cleanup-2)
   - 1 SQLAlchemy import: `Session`
   - Line 10

## Phase 3 Clean Architecture Lite Roadmap

### 🎯 **Clean Architecture Lite 原則**
- **Core 層**：維持「用例 + 介面 (`ports`) + domain model」的乾淨界線
- **Infrastructure 層**：允許 pragmatic 的 legacy 相容層（例如：沿用舊 ORM model），但所有 API / Use Case 僅透過 ports 互動
- **工作包策略**：每個工作包都能在單一 LLM session 內完成，包含需求理解、TDD/Refactor、程式碼審查與測試執行

### 📋 **歷史工作包狀態**

| 編號 | 名稱 | 目標 | 狀態 | 完成日期 |
|------|------|------|------|----------|
| WP1 | Ports & Factories Hardening | 確保所有 use case 依賴注入與 repository 實作一致 | ✅ **完成** | 2025-09 |
| WP2 | Plans 垂直切片 | Plans API → Use Case → Repository 完整走 Clean Architecture Lite | ✅ **完成** | 2025-09 |
| WP3 | Subscriptions 垂直切片 | Subscription pipeline 清理、補齊授權/支付整合測試 | ✅ **完成** | 2025-09 |
| WP4 | Sessions 垂直切片 | Sessions API 解除直接 SQLAlchemy 相依，補上錄音上傳流程的 e2e | ✅ **完成** | 2025-09 |
| WP5 | Domain ↔ ORM 收斂 & Schema Migration | 完成模型切分、建置 Alembic migration、移除 legacy ORM | ✅ **完成** | 2025-09 |

## WP6 Cleanup Series - 剩餘工作

### ✅ **已完成的 WP6 子項目**

#### **WP6-Cleanup-1: Speaker Role Vertical** (✅ 完成 - 2025-09-20)
- **TODOs 解決**: 3 個關鍵架構違規 + 前端大小寫敏感性錯誤
- **用戶價值**: 完整的轉錄稿說話者分配功能
- **E2E 示範**: 教練分配說話者角色 → 匯出專業轉錄稿
- **商業影響**: 核心轉錄功能完成（收入關鍵）

#### **WP6-Cleanup-2: Payment Processing Vertical** (✅ 完成 - 2025-09-17)
- **TODOs 解決**: 11 個付款整合缺口
- **用戶價值**: 可靠的訂閱計費和付款管理
- **E2E 示範**: 建立訂閱 → 重試付款 → 升級方案 → 退款取消
- **商業影響**: 收入處理可靠性（業務關鍵）

### 🔥 **WP6-Cleanup-3: Factory Pattern Migration** (進行中)
**優先級**: 關鍵
**工作量**: 3 天
**目標**: 完成所有 API 端點的依賴注入

**範圍:**
- 移除散布在代碼庫中的 28 個 legacy model imports
- 將剩餘的 89 個 `Depends(get_db)` 端點轉換為使用 factories
- 標準化所有 API 端點使用 clean architecture 模式

**需要遷移的文件:**
```bash
# 需要替換的 legacy imports (28 個):
rg "from.*models\." src/coaching_assistant/api/v1/     # 23 個
rg "from.*models import" src/coaching_assistant/api/v1/ # 5 個

# 需要移除的直接 DB 依賴 (89 個):
rg "Depends\(get_db\)" src/coaching_assistant/api/v1/
```

**重點遷移文件:**
- `billing_analytics.py` (10 endpoints) - 分析功能
- `coach_profile.py` (8 endpoints) - 教練資料
- `clients.py` (7 endpoints) - 客戶管理
- `coaching_sessions.py` (7 endpoints) - 教練會話
- `usage.py` (7 endpoints) - 用量統計
- `usage_history.py` (7 endpoints) - 使用歷史

**執行計劃:**
1. **分析階段**: 識別所有需要遷移的端點和 import statements
2. **Factory 擴展**: 為剩餘服務建立 factory 方法
3. **API 遷移**: 逐一轉換端點使用依賴注入
4. **測試驗證**: 確保所有端點功能正常

### ⚠️ **WP6-Cleanup-4: Analytics & Export Features** (待處理)
**優先級**: 高
**工作量**: 4 天
**目標**: 完成用戶要求的分析功能

**範圍:**
- 遷移 `admin_daily_report.py` 使用 repository pattern
- 實作缺失的 CSV/PDF 匯出功能
- 建立用量分析儀表板後端
- 為匯出操作添加適當的錯誤處理

**當前 TODOs**: 5 個待處理項目
- `google_stt.py`: Speaker diarization 後處理
- `stt_factory.py`: Whisper STT Provider 實作
- `permissions.py`: 通知郵件發送
- `usage_reset_task.py`: 實際郵件發送
- `transcript_repository.py`: Speaker role 更新功能

**關鍵任務:**
1. **Admin Service 重構**: 將 `core/services/admin_daily_report.py` 從直接 SQLAlchemy 查詢改為使用 repository
2. **匯出功能**: 實作 PDF 報告生成和 CSV 數據匯出
3. **分析儀表板**: 建立用量統計和趨勢分析 API
4. **錯誤處理**: 完善匯出過程中的錯誤處理和用戶回饋

### 📋 **WP6-Cleanup-5: Frontend Features** (待處理)
**優先級**: 中等
**工作量**: 5 天
**目標**: 完成剩餘的前端功能

**範圍:**
- 個人檔案照片上傳功能
- 付款方式管理介面
- 會話編輯和轉錄稿管理
- 用戶偏好設定

**TODOs 解決**: 7 個前端功能缺口

**關鍵功能:**
1. **個人檔案管理**: 照片上傳、基本資訊編輯
2. **付款設定**: 信用卡管理、發票設定
3. **會話管理**: 轉錄稿編輯、批量操作
4. **系統設定**: 通知偏好、語言設定

### 📌 **WP6-Cleanup-6: Infrastructure Polish** (待處理)
**優先級**: 低
**工作量**: 5 天
**目標**: 運營卓越和監控

**範圍:**
- 完成電子郵件通知系統
- 增強 STT 提供商回退邏輯
- 系統監控和警報設置
- 效能優化和快取

**TODOs 解決**: 12+ 個基礎設施改進

**關鍵改進:**
1. **通知系統**: 完成電子郵件發送和模板系統
2. **STT 穩定性**: 改進提供商之間的自動回退
3. **監控告警**: 建立系統健康監控和異常告警
4. **效能優化**: 實作快取策略和查詢優化

## Technical Debt Metrics

### Architecture Compliance Tracking

| Metric | Target | Current | Trend | Status |
|--------|--------|---------|-------|--------|
| SQLAlchemy imports in core/ | 0 | 2 files (5 imports) | ↓ | ⚠️ **Improving** |
| Direct DB access in API | 0 | 89 endpoints | ↓ | ⚠️ **Decreasing** |
| Legacy model imports in API | 0 | 28 imports | ↓ | ⚠️ **Tracking** |
| Active TODOs/FIXMEs | 0 | 5 items | ↓ | ⚠️ **Managing** |
| Clean vertical slices | 100% | 70% | ↗ | ✅ **Good progress** |

### Quality Gates Status

```bash
# Current quality checks (all should pass):
make lint                    # ✅ Passing
make test-unit              # ✅ Passing
make test-integration       # ✅ Passing
pytest tests/e2e -m "not slow"  # ✅ Passing
```

## Migration Priorities

### **Immediate Actions Required (Next 2 Weeks)**

1. **Complete WP6-Cleanup-3** (Factory Pattern Migration)
   - Highest impact on architecture compliance
   - Removes majority of remaining technical debt
   - Enables faster future development

2. **Finish Legacy Service Migration**
   - Move `admin_daily_report.py` to use repository pattern
   - Complete `ecpay_service.py` migration started in WP6-Cleanup-2

### **Medium-term Goals (Next Month)**

1. **User Experience Features** (WP6-Cleanup-4, WP6-Cleanup-5)
   - Analytics dashboard for business insights
   - Complete frontend feature set
   - Professional user experience polish

2. **Operational Excellence** (WP6-Cleanup-6)
   - Monitoring and alerting setup
   - Performance optimization
   - Email notification system

## Risk Assessment

### **Low Risk (Can Execute Immediately)**
- Factory pattern migrations - well-established pattern
- API endpoint conversions - proven successful for Plans/Subscriptions
- Frontend feature additions - isolated from backend changes

### **Medium Risk (Requires Careful Planning)**
- Legacy service migrations - involve complex business logic
- Database query optimizations - need performance testing
- Email system integration - external service dependencies

### **High Risk (Requires Staging Validation)**
- ORM model consolidation - database-level changes
- STT provider modifications - core functionality changes
- Payment system changes - revenue-critical features

## Success Criteria for Completion

### **Architecture Goals**
- [ ] Zero SQLAlchemy imports in `core/services/`
- [ ] Zero `Depends(get_db)` in `api/v1/` endpoints
- [ ] All business logic in use cases with >90% test coverage
- [ ] Complete vertical slices for all major features

### **Quality Goals**
- [ ] All quality gates passing consistently
- [ ] E2E test coverage for all user journeys
- [ ] Performance benchmarks maintained or improved
- [ ] Zero critical security vulnerabilities

### **Business Goals**
- [ ] All user-requested features implemented
- [ ] System reliability >99.9% uptime
- [ ] Development velocity improved by 30%
- [ ] Team onboarding time reduced by 50%

## Next Steps

1. **Execute WP6-Cleanup-3** - Factory pattern migration (highest priority)
2. **Plan WP6-Cleanup-4** - Analytics features (user value)
3. **Monitor metrics** - Track architecture compliance trends
4. **Update documentation** - Keep status current as work progresses

The remaining work is well-defined and follows established patterns. The foundation is solid, and completion is primarily a matter of systematic execution rather than architectural innovation.

## 🔥 WP6-Cleanup-3 詳細重構 Checklist

### **🔥 核心功能組 - 優先處理 (架構違規項目)**

#### **客戶管理 (clients.py) - 7 endpoints**
**違規項目**: 7 個 `Depends(get_db)` + Legacy model imports

- [ ] **list_clients** (line 75) - 客戶列表查詢
- [ ] **get_client_statistics** (line 158) - 客戶統計數據
- [ ] **get_client** (line 267) - 單一客戶查詢
- [ ] **create_client** (line 326) - 建立客戶
- [ ] **update_client** (line 394) - 更新客戶資料
- [ ] **delete_client** (line 487) - 刪除客戶
- [ ] **anonymize_client** (line 524) - 客戶匿名化

**Legacy imports 需替換**: `from ...models import Client, CoachingSession, User`

#### **教練會話 (coaching_sessions.py) - 7 endpoints**
**違規項目**: 7 個 `Depends(get_db)` + 多個 Legacy model imports

- [ ] **list_coaching_sessions** (line 141) - 會話列表查詢
- [ ] **get_coaching_session** (line 243) - 單一會話查詢
- [ ] **create_coaching_session** (line 311) - 建立教練會話
- [ ] **update_coaching_session** (line 389) - 更新會話資料
- [ ] **delete_coaching_session** (line 497) - 刪除會話
- [ ] **get_client_last_session** (line 526) - 取得客戶最後會話
- [ ] **upload_session_transcript** (line 587) - 上傳會話轉錄稿

**Legacy imports 需替換**:
- `from ...models import CoachingSession, Client, User, SessionSource`
- `from ...models.session import Session as TranscriptionSession, SessionStatus`
- `from ...models.transcript import TranscriptSegment, SpeakerRole, SessionRole`

#### **轉錄稿處理 (transcript_smoothing.py) - 3 endpoints**
**違規項目**: 3 個 `Depends(get_db)` + Legacy model imports + TODO 項目

- [ ] **get_default_config** (line 1207) - 取得預設配置
- [ ] **smooth_transcript_database** (line 1427) - 資料庫轉錄稿平滑處理
- [ ] **get_stt_optimization_result** (line 1623) - 取得 STT 優化結果

**Legacy imports 需替換**:
- `from ...models.session import Session`
- `from ...models.transcript import TranscriptSegment as TranscriptSegmentModel`
- `from ...models.coaching_session import CoachingSession`

**TODO 項目**: 1 個待處理
- `transcript_repository.py:55` - Speaker role 更新功能

#### **會話管理 (sessions.py) - 1 endpoint**
**違規項目**: 1 個 `Depends(get_db)` + Legacy model imports

- [ ] **update_segment_roles** (line 879) - 更新轉錄片段角色

**Legacy imports 需替換**:
- `from ...models.session import Session, SessionStatus`
- `from ...models.transcript import TranscriptSegment`
- `from ...models.user import User`

#### **摘要功能 (summary.py) - 1 endpoint**
**違規項目**: 1 個 `Depends(get_db)` + Legacy model imports

- [ ] **get_transcription_summary** (line 35) - 取得轉錄稿摘要

**Legacy imports 需替換**:
- `from ...models import` (多個模型)

### **高優先級文件**

#### **billing_analytics.py - 10 endpoints**
**優先級**: ⚠️ **高** (Business Analytics)

- [ ] **10 個分析端點** - 需要建立 analytics use cases
- Legacy imports: `from ...models.user import User`

#### **coach_profile.py - 8 endpoints**
**優先級**: ⚠️ **高** (Coach Management)

- [ ] **8 個教練資料端點** - 需要建立 coach profile use cases
- Legacy imports: `from ...models import User, CoachProfile, CoachingPlan`

#### **usage.py - 7 endpoints**
**優先級**: ⚠️ **高** (Usage Tracking)

- [ ] **7 個用量追蹤端點** - 需要擴展現有 usage use cases
- Legacy imports: `from ...models.user import User, from ...models.usage_analytics import UsageAnalytics`

#### **usage_history.py - 7 endpoints**
**優先級**: ⚠️ **高** (Usage History)

- [ ] **7 個使用歷史端點** - 需要建立 usage history use cases
- Legacy imports: `from ...models.user import User, from ...models.usage_history import UsageHistory`

### **中等優先級文件**

#### **auth.py - 5 endpoints**
**優先級**: 📋 **中等** (Authentication)

- [ ] **5 個認證端點** - 需要建立 auth use cases
- Legacy imports: `from ...models.user import User, UserPlan`

#### **user.py - 5 endpoints**
**優先級**: 📋 **中等** (User Management)

- [ ] **5 個用戶管理端點** - 需要建立 user management use cases
- Legacy imports: `from ...models.user import User, UserPlan`

#### **admin.py - 7 endpoints**
**優先級**: 📋 **中等** (Admin Functions)

- [ ] **7 個管理端點** - 需要建立 admin use cases
- Legacy imports: `from ...models.user import User, UserRole`

### **低優先級文件**

#### **transcript_smoothing.py - 3 endpoints**
**優先級**: 📌 **低** (Transcript Processing)

- [ ] **3 個轉錄稿處理端點** - 需要建立 transcript processing use cases

#### **sessions.py - 1 endpoint**
**優先級**: 📌 **低** (Session Support)

- [ ] **1 個會話支援端點** - 已有部分 session use cases

#### **summary.py - 1 endpoint**
**優先級**: 📌 **低** (Summary Functions)

- [ ] **1 個摘要端點** - 需要建立 summary use cases

#### **admin_reports.py - 2 endpoints**
**優先級**: 📌 **低** (Admin Reports)

- [ ] **2 個管理報告端點** - 需要建立 admin reporting use cases

### **🚀 重新調整執行策略**

#### **第一階段**: 🔥 **核心功能組優先** (2-3 天)
**原因**: 核心功能直接影響業務流程，且違規項目最集中

1. **`clients.py`** - 客戶管理核心 (7 endpoints)
2. **`coaching_sessions.py`** - 教練會話核心 (7 endpoints)
3. **`transcript_smoothing.py`** - 轉錄稿處理核心 (3 endpoints) + TODO 修復
4. **`sessions.py`** - 會話管理核心 (1 endpoint)
5. **`summary.py`** - 摘要功能核心 (1 endpoint)

**重點**:
- 建立對應的 use cases 和 repositories
- 解決 TODO 項目 (`transcript_repository.py` speaker role 更新)
- 清理核心功能的所有架構違規

#### **第二階段**: ⚠️ **業務支援功能** (2-3 天)
1. 完成 `billing_analytics.py` 重構 (10 endpoints)
2. 完成 `coach_profile.py` 重構 (8 endpoints)
3. 完成 `usage.py` 和 `usage_history.py` 重構 (14 endpoints)

#### **第三階段**: 📋 **管理和輔助功能** (1-2 天)
1. 完成 `auth.py`, `user.py`, `admin.py` 重構 (17 endpoints)
2. 完成 `admin_reports.py` 重構 (2 endpoints)
3. 最終驗證所有端點功能正常

### **📋 核心功能優先驗證清單**

#### **🔥 第一階段核心功能驗證**
- [ ] **clients.py**: 7 個 `Depends(get_db)` + legacy imports 已清理
- [ ] **coaching_sessions.py**: 7 個 `Depends(get_db)` + 3 組 legacy imports 已清理
- [ ] **transcript_smoothing.py**: 3 個 `Depends(get_db)` + legacy imports + TODO 已解決
- [ ] **sessions.py**: 1 個 `Depends(get_db)` + legacy imports 已清理
- [ ] **summary.py**: 1 個 `Depends(get_db)` + legacy imports 已清理
- [ ] 核心功能對應的 use cases 和 repositories 已建立
- [ ] 核心功能的 unit tests 覆蓋率 >90%

#### **⚠️ 整體架構合規驗證**
- [ ] 所有 89 個 `Depends(get_db)` 已移除
- [ ] 所有 28 個 legacy model imports 已替換
- [ ] 新增的 use cases 都有對應的 unit tests
- [ ] 5 個 TODO/FIXME 項目已處理完成
- [ ] 2 個 core services 中的 SQLAlchemy imports 已清理

#### **✅ 品質保證驗證**
- [ ] `make lint` 通過 - 代碼風格符合標準
- [ ] `make test-unit` 通過 - 所有單元測試
- [ ] `make test-integration` 通過 - 集成測試
- [ ] 核心功能 API 透過 sugagent 啟動 server 驗證通過
- [ ] 前端核心流程 smoke 測試通過

----
2025-09-21 15:36

📊 實際重構數據 (2025-09-21)

  🔥 核心架構違規

  - SQLAlchemy imports in core services: 2 個文件，5 個 import statements
    - admin_daily_report.py: 4 個 imports (lines 9, 10, 817, 818)
    - ecpay_service.py: 1 個 import (line 10)

  ⚠️ API 層遺留依賴

  - Direct DB access (Depends(get_db)): 89 個端點 (比文件記錄的 88 多了 1 個)
  - Legacy model imports: 28 個 imports (比文件記錄的 40+ 少很多)

  📋 待處理 TODOs

  - 活躍 TODOs: 5 個項目 (比文件記錄的 67 個少很多)
    - Speaker diarization 後處理
    - Whisper STT Provider 實作
    - 通知郵件發送 (2 處)
    - Speaker role 更新功能

  🎯 WP6-Cleanup-3 實際範圍調整

  原文件預估 vs 實際情況:
  - ❌ Legacy imports: 40+ → ✅ 實際: 28 個
  - ❌ DB 依賴: 88 → ✅ 實際: 89 個
  - ❌ TODOs: 67 → ✅ 實際: 5 個

  📈 優先級重新排序

  基於實際掃描，建議調整工作優先級：

  1. 最高優先級: 89 個 API 端點的 DB 依賴遷移
  2. 高優先級: 28 個 legacy model imports 替換
  3. 中等優先級: 2 個 core services 的 SQLAlchemy 清理
  4. 低優先級: 5 個 TODOs 處理

  🔍 重點遷移文件

  根據實際掃描，這些文件需要重點關注：
  - billing_analytics.py (10 endpoints)
  - coach_profile.py (8 endpoints)
  - clients.py (7 endpoints)
  - coaching_sessions.py (7 endpoints)
  - usage.py (7 endpoints)
  - usage_history.py (7 endpoints)