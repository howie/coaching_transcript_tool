# US010 - Fix Model Column Name Inconsistency

## 問題描述

目前專案中存在嚴重的欄位命名不一致問題：

1. **資料庫模型** 使用 `transcription_session_id`
2. **前端程式碼** 仍在使用舊的 `audio_timeseq_id`
3. **API 介面** 混合使用兩種命名
4. **測試程式碼** 缺乏對新欄位的覆蓋

這導致：
- 轉檔記錄檢查功能失效
- 前後端資料不同步
- 程式碼可讀性差
- 維護困難

## 解決方案

全面清理和統一欄位命名，完全移除 `audio_timeseq_id`，統一使用 `transcription_session_id`。

## 修改範圍

### 1. 後端 API 修改

#### 檔案清單：
- `packages/core-logic/src/coaching_assistant/api/coaching_sessions.py`
- `packages/core-logic/src/coaching_assistant/api/sessions.py`
- `packages/core-logic/src/coaching_assistant/models/coaching_session.py` (已正確)

#### 修改內容：
- 確保所有 API 回應使用 `transcription_session_id`
- 移除任何對 `audio_timeseq_id` 的引用
- 更新 Pydantic 模型定義

### 2. 前端修改

#### 檔案清單：
- `apps/web/app/dashboard/sessions/[id]/page.tsx`
- `apps/web/app/dashboard/sessions/page.tsx`
- `apps/web/lib/api.ts`
- `apps/web/components/AudioUploader.tsx`

#### 修改內容：
- 更新 TypeScript 介面定義
- 移除所有 `audio_timeseq_id` 引用
- 統一使用 `transcription_session_id`
- 更新所有相關函數參數和回傳值
- 移除向後相容性程式碼

### 3. 測試更新

#### 需要建立/更新的測試：
- `packages/core-logic/tests/api/test_coaching_sessions_api.py` (新建)
- `packages/core-logic/tests/models/test_coaching_session.py` (更新)
- 更新所有相關的 API 測試案例

#### 測試覆蓋項目：
- Coaching Session CRUD 操作
- 轉檔會話關聯
- API 回應格式驗證
- 欄位驗證

### 4. 文檔更新

#### 檔案清單：
- 移除過時的文檔引用
- 更新 API 文檔
- 更新資料庫 ERD

## 實作步驟

### 階段 1: 後端清理
1. 檢查並更新所有後端 API 介面
2. 確保資料庫模型一致性
3. 移除所有 `audio_timeseq_id` 殘留程式碼

### 階段 2: 前端重構
1. 更新 TypeScript 介面定義
2. 重構所有使用舊欄位名稱的程式碼
3. 移除向後相容性邏輯
4. 更新元件屬性和函數簽名

### 階段 3: 測試完善
1. 建立完整的 API 測試套件
2. 測試所有 CRUD 操作
3. 驗證前後端整合
4. 確保所有功能正常運作

### 階段 4: 驗證與清理
1. 運行所有測試確保通過
2. 手動測試關鍵功能流程
3. 移除不必要的備份檔案
4. 更新相關文檔

## 驗收標準

✅ **功能性要求：**
- 會談詳情頁面正確檢測既有轉檔記錄
- 逐字稿上傳功能正常運作
- 轉檔狀態顯示正確
- 匯出功能使用正確的 ID

✅ **程式碼品質：**
- 移除所有 `audio_timeseq_id` 引用
- 統一使用 `transcription_session_id`
- 無向後相容性程式碼殘留
- TypeScript 類型檢查通過

✅ **測試覆蓋：**
- 所有 API 端點有對應測試
- 前後端整合測試通過
- 邊界條件測試覆蓋
- 測試覆蓋率 > 80%

✅ **效能要求：**
- 頁面載入時間不受影響
- API 回應時間保持穩定
- 無記憶體洩漏

## 風險評估

### 高風險：
- 資料庫遷移可能影響既有資料
- 前後端不同步可能導致功能中斷

### 中風險：
- 測試覆蓋不足可能遺漏問題
- 第三方整合可能受影響

### 低風險：
- UI/UX 變更最小
- 使用者體驗影響有限

## 回退計畫

如果出現問題：
1. 使用 git revert 回退變更
2. 重新運行資料庫遷移 downgrade
3. 恢復前端舊版本
4. 通知相關團隊成員

## 執行時間估計

- **階段 1 (後端)**: 2-3 小時
- **階段 2 (前端)**: 3-4 小時  
- **階段 3 (測試)**: 2-3 小時
- **階段 4 (驗證)**: 1-2 小時

**總計**: 8-12 小時