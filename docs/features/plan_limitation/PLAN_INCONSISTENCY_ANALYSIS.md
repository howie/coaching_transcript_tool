# Plan Limitation 不一致性分析與修復計劃

## 問題概述

在實施 plan limitation 功能時發現前端 change-plan 頁面與後端資料庫設定存在多項不一致，影響用戶體驗和系統一致性。

## 不一致問題詳細分析

### 1. Plan 名稱不一致

| 位置 | FREE | PRO | 第三級 |
|------|------|-----|--------|
| 前端 change-plan | `Free` | `Pro` | `Business` |
| UserPlan enum | `FREE` | `PRO` | `ENTERPRISE` |
| PlanName enum | `free` | `pro` | `enterprise` |

**影響**: 前端無法正確映射到後端 plan 類型

### 2. 功能限制不一致

#### FREE Plan
| 功能項目 | 前端顯示 | 後端實際 (BETA) | 差異 |
|---------|---------|---------------|------|
| 會談數 | 5 uploaded recordings | 3 sessions | ❌ 不符 |
| 轉錄數 | 10 linked recordings | 5 transcriptions | ❌ 不符 |
| 時長限制 | Up to 30 min per recording | 60 minutes total | ❌ 概念不同 |
| 檔案大小 | 未列出 | 25MB per file | ❌ 遺漏 |
| 聊天額度 | 10 chat credits | 無此概念 | ❌ 多餘功能 |

#### PRO Plan  
| 功能項目 | 前端顯示 | 後端實際 (BETA) | 差異 |
|---------|---------|---------------|------|
| 會談數 | Unlimited | 25 sessions | ❌ 嚴重不符 |
| 轉錄數 | 1,200 min transcription | 50 transcriptions | ❌ 單位不同 |
| 時長限制 | Up to 90 min per recording | 300 minutes total | ❌ 概念不同 |
| 檔案大小 | 未列出 | 100MB per file | ❌ 遺漏 |

#### BUSINESS/ENTERPRISE Plan
| 功能項目 | 前端顯示 | 後端實際 (BETA) | 差異 |
|---------|---------|---------------|------|
| 會談數 | Unlimited | 500 sessions | ❌ 不符 |
| 轉錄數 | 6,000 min transcription | 1000 transcriptions | ❌ 單位不同 |
| 時長限制 | Up to 4 hours per recording | 1500 minutes total | ❌ 概念不同 |
| 檔案大小 | 未列出 | 500MB per file | ❌ 遺漏 |

### 3. 價格不一致

| Plan | 前端價格 (USD) | 後端價格 (USD) | 差異 |
|------|-------------|-------------|------|
| FREE | $0 | $0 | ✅ 一致 |
| PRO | $25/$20 (月/年) | $29/$290 (月/年) | ❌ 不符 |
| BUSINESS/ENTERPRISE | $60/$50 (月/年) | $99/$990 (月/年) | ❌ 嚴重不符 |

## 成本與獲利分析需求

### TODO: 成本計算分析

需要進行以下分析來確定合適的 plan limits:

1. **STT 服務成本分析**
   - Google Speech-to-Text API 計費
   - AssemblyAI 計費
   - 平均每分鐘轉錄成本

2. **基礎設施成本**
   - GCS 儲存成本
   - Compute 資源使用
   - 資料庫存儲和查詢成本

3. **獲利目標設定**
   - 每個 plan 的目標毛利率
   - 用戶獲取成本 (CAC)
   - 生命週期價值 (LTV)

4. **競爭對手分析**
   - 類似服務的定價策略
   - 功能對比分析

### TODO: 建議的 Plan 結構

基於成本分析後，建議重新設計：

```typescript
// 建議的新 plan 結構（待成本分析後確認）
interface PlanStructure {
  FREE: {
    sessions_per_month: number,      // 建議: 3-5
    transcription_minutes: number,   // 建議: 30-60 分鐘
    file_size_mb: number,           // 建議: 25MB
    price_usd: 0
  },
  PRO: {
    sessions_per_month: number,      // 建議: 25-50
    transcription_minutes: number,   // 建議: 300-600 分鐘
    file_size_mb: number,           // 建議: 100MB
    price_usd: number               // 待定
  },
  ENTERPRISE: {
    sessions_per_month: number,      // 建議: 100-500
    transcription_minutes: number,   // 建議: 1200-3000 分鐘
    file_size_mb: number,           // 建議: 500MB-1GB
    price_usd: number               // 待定
  }
}
```

## i18n 翻譯問題

### 當前錯誤

用戶看到錯誤訊息 `"errors.sessionLimitExceededWithPlan"` 而非翻譯後的文字，表示 i18n 翻譯功能未正確運作。

### 錯誤原因分析

1. **翻譯 key 未被解析**: `t()` 函數沒有正確接收或處理 key
2. **參數傳遞問題**: 動態參數 (limit, plan) 可能未正確傳遞
3. ** 翻譯檔案路徑問題**: translation key 可能不存在

### ✅ i18n 修復完成清單

- [x] ✅ **已修復**: 發現翻譯 keys 被加到錯誤的翻譯系統 (translations.ts vs i18n/translations)
- [x] ✅ **已修復**: 將錯誤訊息翻譯加到正確的模組化翻譯系統 (common.ts)
- [x] ✅ **已修復**: 更新 i18n-context 支援參數插值功能
- [x] ✅ **已修復**: 確認 ApiClient.setTranslationFunction() 正確設定
- [x] ✅ **已修復**: 檢查 parseErrorMessage 函數的參數傳遞
- [x] ✅ **已測試**: 建立完整測試覆蓋 13 個測試案例，全部通過
- [x] ✅ **已修復**: 用戶現在可以看到本地化的錯誤訊息而非 key

**修復結果**: 
- 中文: `"您已達到每月會談數限制 3 次（免費 方案）。考慮升級方案以獲得更高限制。"`
- English: `"You have reached your monthly session limit of 3 (FREE plan). Consider upgrading your plan for higher limits."`

## 修復優先級

### Phase 1: 緊急修復 (本週)
1. ✅ **完成**: 修復 i18n 翻譯顯示問題
2. 🔄 **進行中**: 統一 plan 名稱映射 (frontend ↔ backend)
3. 🔄 **待完成**: 更新前端 change-plan 頁面顯示正確的 BETA limits

### Phase 2: 成本分析 (下週)
1. 進行詳細的成本與獲利分析
2. 制定新的 plan pricing 策略
3. 確定最終的 plan limits

### Phase 3: 系統更新 (下下週)
1. 更新後端 plan limits 配置
2. 更新前端 plan 顯示
3. 進行完整的 E2E 測試

## 影響範圍

### 用戶體驗影響
- **高**: 用戶看到的功能與實際不符，造成困惑
- **中**: 錯誤訊息未翻譯影響非英語用戶體驗

### 商業影響
- **高**: 定價不一致可能影響付費轉換
- **中**: 功能限制不明確影響用戶期望管理

### 技術債務
- **中**: 前後端不一致增加維護複雜度
- **低**: i18n 問題影響代碼品質

## 下一步行動

1. **立即**: 修復 i18n 翻譯問題
2. **本週**: 完成 plan 一致性修復
3. **下週**: 開始成本分析和定價重新設計
4. **持續**: 建立自動化測試確保前後端一致性

---

**文件更新日期**: 2025-01-17  
**負責人**: Claude Code Assistant  
**狀態**: 分析完成，待修復實施