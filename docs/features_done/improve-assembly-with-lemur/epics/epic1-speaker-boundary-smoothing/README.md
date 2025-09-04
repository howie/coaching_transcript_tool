# Epic 1: Speaker Boundary Smoothing (講者邊界平滑)

## Epic 概述

**目標**：自動修正 AssemblyAI 轉錄結果中常見的講者邊界錯誤，包括句尾片段誤分配、語氣詞歸屬錯誤、引用句重複等問題。

**商業價值**：
- 減少人工校對工作量 70%
- 提升講者分段準確率至 95%
- 改善對話可讀性和邏輯連貫性

## 核心演算法

### 1. 短首段回填規則 (Short-Head Backfill)

```python
if (next_segment.duration < TH_SHORT_HEAD_SEC and 
    not has_terminal_punctuation(prev_segment.text)):
    merge_to_previous_speaker(next_segment.head_words)
```

**參數**：
- `TH_SHORT_HEAD_SEC = 0.9` 秒
- 終止標點：。！？…

### 2. 語氣詞白名單回填 (Filler Backfill)

```python
FILLER_WHITELIST = ["嗯","呃","唉","喔","哦","唔","啊","欸","對","好"]

if (is_filler_word(next_segment.first_word) and 
    next_segment.first_word.duration < TH_FILLER_MAX_SEC):
    merge_to_previous_speaker(next_segment.first_word)
```

**參數**：
- `TH_FILLER_MAX_SEC = 0.6` 秒

### 3. 跨講者尾詞保護 (Tail Protection)

```python
if (gap_between_segments < TH_GAP_SEC and 
    is_tail_particle(prev_segment.last_word)):
    keep_with_previous_speaker(prev_segment.last_word)
```

**參數**：
- `TH_GAP_SEC = 0.25` 秒

### 4. 回聲引述回填 (Echo/Quote Backfill)

```python
if (has_quotation_marks(next_segment) or 
    similarity(next_segment.head, prev_segment.tail) > ECHO_JACCARD_TAU):
    merge_to_previous_speaker(next_segment.echo_part)
```

**參數**：
- `ECHO_JACCARD_TAU = 0.6`
- `TH_ECHO_MAX_SEC = 1.2` 秒

## 迭代處理

系統進行最多 `N_PASS = 2` 次迭代，直到：
1. 無更多變更發生
2. 達到迭代上限

每次迭代會重新評估所有邊界點，確保修正的完整性。

## 約束條件

1. **最大移動量限制**：`TH_MAX_MOVE_SEC = 1.5` 秒
2. **時間連續性**：保持原始時間戳順序
3. **講者一致性**：不破壞原有正確的講者分段

## 輸出統計

```json
{
  "stats": {
    "moved_word_count": 12,
    "merged_segments": 4,
    "heuristic_hits": {
      "short_first_segment": 6,
      "filler_words": 9,
      "no_terminal_punct": 5,
      "echo_backfill": 1
    }
  }
}
```

## 用戶故事

- [US-1.1: 短首段回填修正](./user-story-1.1-short-head-backfill.md)
- [US-1.2: 語氣詞智能回填](./user-story-1.2-filler-backfill.md)
- [US-1.3: 引用句回聲偵測](./user-story-1.3-echo-detection.md)

## 測試策略

### 單元測試
- 各項啟發式規則的正確性
- 邊界條件和極端值處理
- 參數調整的敏感性分析

### 整合測試
- 多規則同時作用的協調性
- 迭代收斂性驗證
- 統計數據準確性

### 效能測試
- 大量 utterances 的處理效能
- 記憶體使用效率
- 時間複雜度驗證

## 品質保證

1. **正確性**：修正應該發生的錯誤 ≥ 90%
2. **穩定性**：不破壞原本正確的分段 ≥ 95%
3. **效能**：處理時間 < 原音檔長度的 5%