# Epic 1: Testing Strategy - 保守驗證方法

## 概述

本文檔描述 Epic 1 LeMUR Combined Processing 的全面測試和驗證策略。採用保守的三層驗證方法，確保新實施的混合處理系統能夠在生產環境中穩定運行。

## 測試階段架構

### 第一層：單元測試 (Unit Tests)
**已完成 ✅** - 覆蓋所有新增函數的獨立測試

#### 測試文件
- **`test_lemur_response_parsing.py`** - 測試解析邏輯
- **覆蓋函數**:
  ```python
  test_parse_combined_response_json_mapping()
  test_parse_combined_response_transcript_content()
  test_parse_combined_response_speaker_format()
  test_apply_mandatory_cleanup()
  test_merge_close_segments()
  test_infer_speaker_mapping_from_content()
  ```

#### 測試場景
- ✅ 各種 LeMUR 回應格式解析
- ✅ 中文空格移除邏輯
- ✅ 繁體中文轉換
- ✅ 片段合併演算法
- ✅ 角色映射推斷

### 第二層：整合測試 (Integration Tests)
**已完成 ✅** - 測試完整處理流程

#### 測試文件
- **`test_lemur_chinese_processing.py`** - 端到端處理測試
- **測試範圍**:
  - 模擬 LeMUR API 回應
  - 完整的 `smooth_transcript_with_lemur` 流程
  - 各種輸入數據格式

#### 測試案例
```python
# 測試場景 1: 標準中文對話
input_segments = [
    {"text": "只是 想 說 這個 問題", "speaker": "Speaker_1"},
    {"text": "好 的 ， 我 明白 了", "speaker": "Speaker_2"}
]

# 預期輸出
expected_output = [
    {"text": "只是想說這個問題", "speaker_role": "客戶"},
    {"text": "好的，我明白了", "speaker_role": "教練"}
]
```

### 第三層：手動驗證 (Manual Verification)
**已完成 ✅** - 真實案例快速測試

#### 測試文件
- **`test_lemur_fixes.py`** - 手動執行腳本
- **用途**: 快速驗證修復是否解決了具體問題

## 生產環境驗證策略

### 階段一：影子測試 (Shadow Testing)
**時間**: 1-2 週  
**範圍**: 5% 隨機選取的會談

#### 實施方法
1. **雙軌運行**: 同時執行舊系統和新系統
2. **數據收集**: 記錄兩個系統的輸出差異
3. **品質分析**: 人工評估新系統的改進程度
4. **錯誤追蹤**: 識別和修復新系統的問題

#### 成功標準
- **零崩潰**: 新系統不能造成任何處理失敗
- **品質提升**: 至少 80% 的案例顯示品質改善
- **性能可接受**: 處理時間增加不超過 50%

### 階段二：分段推出 (Gradual Rollout)
**時間**: 2-3 週  
**範圍**: 10% → 30% → 70% → 100%

#### 推出計劃
```
Week 1: 10% 用戶 (新用戶優先)
Week 2: 30% 用戶 (包含活躍用戶)
Week 3: 70% 用戶 (大部分用戶)
Week 4: 100% 用戶 (全面部署)
```

#### 監控指標
- **成功率指標**:
  - 空格移除成功率: ≥ 98%
  - 繁體轉換成功率: ≥ 99%
  - 角色識別準確率: ≥ 85%
  
- **性能指標**:
  - 處理時間中位數: ≤ 原系統的 120%
  - API 錯誤率: ≤ 1%
  - 用戶投訴率: 不增加

#### 每階段檢查點
1. **數據收集**: 24 小時後收集指標
2. **品質評估**: 人工檢查 50 個隨機樣本
3. **決策點**: 繼續推出或暫停修復
4. **用戶反饋**: 主動收集用戶意見

### 階段三：全面監控 (Full Monitoring)
**時間**: 持續進行  
**範圍**: 100% 用戶

#### 監控系統
```python
# 監控指標收集
class LeMURProcessingMetrics:
    def record_processing_result(self, session_id, metrics):
        """記錄每次處理的成功指標"""
        self.track_space_removal_success(metrics.spaces_removed)
        self.track_traditional_conversion(metrics.traditional_success)
        self.track_speaker_accuracy(metrics.speaker_correct)
        self.track_processing_time(metrics.duration_ms)
```

#### 告警設置
- **即時告警**:
  - 空格移除成功率低於 95%
  - API 錯誤率超過 2%
  - 處理時間超過 30 秒

- **每日報告**:
  - 品質指標趨勢
  - 用戶滿意度評分
  - 成本效益分析

## 回滾策略

### 快速回滾機制
**目標**: 5 分鐘內切回舊系統

#### 實施方法
```python
# 功能開關
LEMUR_COMBINED_PROCESSING_ENABLED = get_feature_flag("lemur_combined_v2")

if LEMUR_COMBINED_PROCESSING_ENABLED:
    # 使用新的混合處理系統
    return new_combined_processing(segments)
else:
    # 回滾到原有系統
    return legacy_processing(segments)
```

#### 回滾觸發條件
- **自動回滾**:
  - 空格移除成功率 < 90%
  - API 錯誤率 > 5%
  - 處理失敗率 > 3%

- **手動回滾**:
  - 用戶投訴率顯著增加
  - 發現未預期的品質問題
  - 緊急維護需求

### 數據保護
- **處理記錄**: 保留所有處理前後的數據樣本
- **錯誤日誌**: 詳細記錄每個處理失敗的案例
- **用戶通知**: 如有品質問題，主動通知受影響的用戶

## 測試數據和基準

### 基準數據集
**來源**: 過去 3 個月的真實用戶會談  
**規模**: 500 個會談樣本  
**分布**: 
- 教練新手: 40%
- 教練有經驗: 60%
- 會談長度: 30-90 分鐘

### 品質評估標準
#### 空格移除評估
```python
def evaluate_space_removal(original, processed):
    """評估中文空格移除的成功率"""
    chinese_chars = re.findall(r'[\u4e00-\u9fff]', processed)
    spaces_between_chinese = re.findall(r'[\u4e00-\u9fff]\s+[\u4e00-\u9fff]', processed)
    return len(spaces_between_chinese) == 0
```

#### 角色識別評估
```python
def evaluate_speaker_accuracy(processed_segments, ground_truth):
    """評估角色識別的準確率"""
    correct = sum(1 for p, t in zip(processed_segments, ground_truth) 
                 if p['speaker_role'] == t['expected_role'])
    return correct / len(processed_segments)
```

## A/B 測試框架

### 測試設計
- **控制組**: 使用舊的分步處理系統
- **實驗組**: 使用新的 LeMUR 混合處理系統
- **分流比例**: 50% : 50%
- **測試期間**: 2 週

### 測試指標
| 指標類型 | 具體指標 | 目標改善 |
|---------|---------|---------|
| **品質** | 空格移除成功率 | 95% → 98% |
| **品質** | 繁體轉換準確率 | 90% → 99% |
| **品質** | 角色識別準確率 | 70% → 85% |
| **效率** | 需要手動優化的比例 | 40% → 5% |
| **滿意度** | 用戶滿意度評分 | 7.5/10 → 8.5/10 |

### 統計顯著性
- **最小樣本量**: 每組 1000 個會談
- **置信水平**: 95%
- **統計功效**: 80%

## 長期品質保證

### 持續改進流程
1. **每週品質審查**: 檢查品質指標趨勢
2. **每月用戶調查**: 收集使用體驗反饋
3. **季度深度分析**: 分析失敗案例，優化系統

### 知識積累
- **失敗案例庫**: 收集和分析處理失敗的案例
- **最佳實踐更新**: 根據實際運行經驗更新 prompt
- **演算法優化**: 基於真實數據持續改進處理邏輯

## 風險管控

### 已識別風險
| 風險 | 可能性 | 影響 | 緩解措施 |
|-----|-------|------|---------|
| **LeMUR API 不穩定** | 中 | 高 | 多重 fallback 機制 |
| **中文處理邊緣案例** | 中 | 中 | 強制清理兜底 |
| **角色識別準確率下降** | 低 | 中 | 保留手動修正功能 |
| **處理時間顯著增加** | 低 | 高 | 性能監控和優化 |

### 應急預案
- **技術預案**: 自動 fallback 到舊系統
- **業務預案**: 人工客服支持受影響用戶
- **溝通預案**: 主動向用戶說明改進和問題修復

---

**文檔版本**: 1.0  
**最後更新**: 2025-09-09  
**負責人**: AI Coach 開發團隊  
**審核狀態**: 等待產品經理確認