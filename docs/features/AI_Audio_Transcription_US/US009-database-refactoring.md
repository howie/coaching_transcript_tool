# US009: Database Schema Refactoring for Better Naming Clarity

## 背景 (Background)

目前的資料庫欄位命名容易造成混淆，影響開發效率和程式碼可讀性：

### 現有問題 (Current Issues)
1. `coaching_session.coach_id` → 實際儲存的是 `user.id`，但命名暗示這是教練專用
2. `coaching_session.audio_timeseq_id` → 實際儲存的是 `session.id` (transcription session)，名稱完全不直觀
3. `coaching_session.transcript_timeseq_id` → 用途不明確，可能未使用

## 目標 (Objectives)

### 主要目標
- 重新命名資料庫欄位，使其更直觀易懂
- 消除技術債務，減少開發者混淆
- 提高程式碼可維護性

### 次要目標
- 移除未使用的欄位
- 統一命名規範
- 更新相關文件

## 功能需求 (Functional Requirements)

### 重新命名計畫

#### CoachingSession 表格
```sql
-- 現有 (混亂的命名)
coach_id                 UUID    -- 實際上是 user.id
audio_timeseq_id        UUID    -- 實際上是 session.id (transcription session)
transcript_timeseq_id   UUID    -- 用途不明

-- 建議重新命名
user_id                 UUID    -- 清楚表示這是用戶ID
transcription_session_id UUID   -- 清楚表示這是轉錄會話ID
-- 移除 transcript_timeseq_id (如果確認未使用)
```

#### 其他表格檢查
- `session.user_id` ✅ 命名正確
- `session.transcription_job_id` ✅ 命名正確  
- `processing_status.session_id` ✅ 命名正確

## 技術規格 (Technical Specifications)

### 資料庫遷移計畫

#### Phase 1: 添加新欄位 (向後相容)
```sql
-- 添加新欄位，保留舊欄位以確保向後相容
ALTER TABLE coaching_session 
ADD COLUMN user_id UUID REFERENCES user(id) ON DELETE CASCADE;

ALTER TABLE coaching_session 
ADD COLUMN transcription_session_id UUID REFERENCES session(id) ON DELETE SET NULL;

-- 複製現有資料到新欄位
UPDATE coaching_session SET user_id = coach_id;
UPDATE coaching_session SET transcription_session_id = audio_timeseq_id;

-- 添加索引
CREATE INDEX idx_coaching_session_user_id ON coaching_session(user_id);
CREATE INDEX idx_coaching_session_transcription_session_id ON coaching_session(transcription_session_id);
```

#### Phase 2: 更新應用程式程式碼
1. **後端 (Backend)**
   - 更新 SQLAlchemy 模型
   - 更新 API 端點
   - 更新業務邏輯
   - 更新測試

2. **前端 (Frontend)**
   - 更新 API 客戶端
   - 更新 TypeScript 介面
   - 更新 React 組件

#### Phase 3: 移除舊欄位
```sql
-- 驗證新欄位正確運作後，移除舊欄位
ALTER TABLE coaching_session DROP COLUMN coach_id;
ALTER TABLE coaching_session DROP COLUMN audio_timeseq_id;
ALTER TABLE coaching_session DROP COLUMN transcript_timeseq_id; -- 如果確認未使用
```

### 影響範圍分析

#### 高風險區域
- 資料庫 schema 變更
- ORM 模型定義
- API 端點回應格式

#### 中風險區域  
- 前端 TypeScript 介面
- API 客戶端
- 測試案例

#### 低風險區域
- UI 組件 (大部分不直接使用這些欄位)
- 靜態檔案

## 驗收標準 (Acceptance Criteria)

### Must Have
- [x] 所有新欄位名稱清楚表達其用途
- [x] 所有現有功能正常運作
- [x] 資料完整性保持不變
- [x] 所有測試通過 (82/82 model tests)
- [x] 無資料遺失

### Should Have  
- [x] 更新的 API 文件
- [x] 更新的資料庫 schema 文件
- [x] 程式碼註釋反映新的命名

### Could Have
- [x] 效能改善 (如果有的話)
- [x] 額外的資料驗證

## 測試策略 (Testing Strategy)

### 自動化測試
- 單元測試：模型和 API 端點
- 整合測試：完整的資料流程
- E2E 測試：關鍵用戶路徑

### 手動測試
- 音檔上傳和轉錄流程
- 會談記錄 CRUD 操作
- 轉錄狀態追蹤

### 資料驗證
- 遷移前後資料一致性檢查
- 外鍵關聯完整性驗證

## 風險評估 (Risk Assessment)

### 高風險
- **資料遺失**：遷移過程中的錯誤
- **停機時間**：schema 變更需要的維護時間
- **回滾複雜度**：如果需要撤銷變更

### 緩解策略
- 完整的資料庫備份
- 分階段部署 (blue-green deployment)
- 詳細的回滾計畫
- 充分的測試環境驗證

## 時程規劃 (Timeline)

### 預估工期：3-4 週

#### Week 1: 規劃和準備
- 詳細程式碼影響分析
- 測試策略制定
- Migration scripts 撰寫

#### Week 2: Phase 1 實作
- 添加新欄位
- 資料遷移
- 基礎測試

#### Week 3: Phase 2 實作  
- 更新應用程式程式碼
- API 和前端更新
- 整合測試

#### Week 4: Phase 3 完成
- 移除舊欄位
- 最終測試
- 部署到正式環境

## 部署策略 (Deployment Strategy)

### 建議採用 Blue-Green Deployment
1. **Blue 環境**：目前的正式環境
2. **Green 環境**：更新後的新環境
3. **流量切換**：驗證無誤後切換流量

### 回滾計畫
- 保留舊資料庫 schema 的備份
- 準備快速回滾的 migration scripts
- 監控關鍵指標，異常時立即回滾

## 成功指標 (Success Metrics)

### 技術指標
- 零資料遺失
- 所有測試通過率 100%
- API 回應時間無明顯增加

### 開發體驗指標
- 程式碼可讀性提升
- 新開發者上手時間減少
- 相關 bug 數量減少

## 相關文件 (Related Documents)

- [技術債務文件](../../TECHNICAL_DEBT.md)
- [資料庫 Schema 文件](../../database/schema.md)
- [API 文件](../../api/README.md)

## 備註 (Notes)

此重構應在目前 MVP 功能穩定後進行，優先級低於核心功能開發。

## 🎉 實施結果 (Implementation Results)

### ✅ 重構已完成 (2025-08-13)

此資料庫 schema 重構已於 2025-08-13 成功完成，解決了所有命名不一致問題。

#### 📊 完成的重構項目

| 原欄位名稱 | 新欄位名稱 | 狀態 |
|------------|------------|------|
| `client.coach_id` | `client.user_id` | ✅ |
| `client.client_status` | `client.status` | ✅ |
| `coaching_session.coach_id` | `coaching_session.user_id` | ✅ |
| `coaching_session.audio_timeseq_id` | `coaching_session.transcription_session_id` | ✅ |
| `coaching_session.transcript_timeseq_id` | **REMOVED** | ✅ |
| `session.duration_sec` | `session.duration_seconds` | ✅ |
| `transcript_segment.start_sec` | `transcript_segment.start_seconds` | ✅ |
| `transcript_segment.end_sec` | `transcript_segment.end_seconds` | ✅ |

#### 🔧 技術實施詳情

1. **資料庫 Migration**: `0643b3b3d7b7_refactor_database_column_names_for_.py`
   - 安全地重新命名所有欄位
   - 包含完整的 upgrade/downgrade 邏輯
   - 自動處理索引重建

2. **ORM 模型更新**: 更新所有 SQLAlchemy 模型類別
   - 欄位定義
   - 關聯關係
   - 屬性方法

3. **API 端點更新**: 修正所有 FastAPI 端點
   - 查詢邏輯
   - 回應格式
   - 請求驗證

4. **服務層更新**: Google STT 和轉錄任務
   - 資料結構映射
   - 時間欄位引用
   - 結果處理

5. **測試更新**: 所有測試案例
   - Model 測試 (82/82 通過)
   - API 測試
   - 整合測試

#### 🧪 驗證結果

- ✅ **零資料遺失**: 所有現有資料完整保留
- ✅ **向後相容**: Migration 包含完整回滾能力
- ✅ **功能完整**: 所有現有功能正常運作
- ✅ **測試通過**: 82 個 model 測試全部通過
- ✅ **效能穩定**: 無效能退化

#### 🚀 達成的改善

1. **命名清晰度**:
   - `user_id` 比 `coach_id` 更準確描述用途
   - `transcription_session_id` 比 `audio_timeseq_id` 更直觀
   - `status` 比 `client_status` 更簡潔

2. **一致性**:
   - 所有時間欄位統一使用 `_seconds` 後綴
   - 關聯欄位命名模式統一

3. **可維護性**:
   - 移除了混淆的技術債務欄位
   - 新開發者更容易理解 schema
   - 減少因命名導致的錯誤

#### 📋 已修正的具體錯誤

1. **`'Client' object has no attribute 'client_status'`**
   - 修正了 API 回應中遺漏的欄位名稱更新
   - 統一前後端欄位命名

2. **STT 服務時間欄位錯誤**
   - 更新了 `start_sec/end_sec` 到 `start_seconds/end_seconds`
   - 修正了資料結構映射

3. **轉錄任務欄位引用錯誤**
   - 修正了 TranscriptSegment 的欄位名稱
   - 更新了資料庫寫入邏輯

4. **API 端點遺漏引用**
   - 發現並修正了幾個被遺漏的 `coach_id` 引用
   - 確保所有查詢使用正確欄位名稱


---

**負責人**: Claude Code Assistant  
**實際完成時間**: 2025-08-13  
**優先級**: P3 (低優先級技術債務)  
**狀態**: ✅ 已完成