# Epic 2: Chinese Punctuation Repair (中文標點修復)

## Epic 概述

**目標**：依據中文語法規則對轉錄文本進行句界重切與標點修復，在不改變原始語意的前提下，產生符合中文閱讀習慣的專業文本。

**商業價值**：
- 提升文本專業度和可讀性
- 符合中文標點符號規範
- 減少後期編輯時間 60%

## 核心原則

### 1. 語意保真原則
- **絕對禁止**修改、增刪任何詞彙
- **僅允許**添加標點符號和調整句界
- **保持**原始語境和語意完整

### 2. 中文規範原則
- 使用全形標點符號
- 遵循中文語法和標點規則
- 保持中英文混合時的適當空格

## 核心演算法

### 1. 句界切分 (Sentence Boundary Detection)

```python
def split_sentences(words_with_timestamps):
    sentences = []
    current_sentence = []
    
    for i, word in enumerate(words_with_timestamps):
        current_sentence.append(word)
        
        # 停頓時間判斷
        if (i < len(words_with_timestamps) - 1 and 
            get_gap(word, words_with_timestamps[i+1]) > TH_SENT_GAP_SEC):
            
            # 避免過短句子
            if len(''.join([w.text for w in current_sentence])) >= 3:
                sentences.append(current_sentence)
                current_sentence = []
    
    return sentences
```

**參數**：
- `TH_SENT_GAP_SEC = 0.6` 秒
- 最短句子長度：3 字

### 2. 標點符號判斷 (Punctuation Assignment)

```python
def assign_punctuation(sentence_text):
    # 疑問語氣偵測
    question_indicators = ['嗎', '呢', '是不是', '對不對', '好不好']
    if any(indicator in sentence_text for indicator in question_indicators):
        return '？'
    
    # 強烈語氣偵測  
    exclamation_indicators = ['真的', '太', '非常', '超級']
    emotion_words = ['哇', '哎呀', '天啊']
    if (any(indicator in sentence_text for indicator in exclamation_indicators) or
        any(emotion in sentence_text for emotion in emotion_words)):
        return '！'
    
    # 省略語氣偵測
    if sentence_text.endswith(('之類的', '什麼的', '等等')):
        return '…'
    
    # 預設句號
    return '。'
```

### 3. 全形標點轉換 (Full-width Punctuation)

```python
PUNCTUATION_MAP = {
    ',': '，',
    '.': '。', 
    '?': '？',
    '!': '！',
    ':': '：',
    ';': '；',
    '(': '（',
    ')': '）',
    '"': '"',  # 智能引號處理
    "'": '''
}

def normalize_punctuation(text):
    for half, full in PUNCTUATION_MAP.items():
        text = text.replace(half, full)
    return text
```

### 4. 智能引號處理 (Smart Quote Processing)

```python
def process_quotes(text):
    # 成對引號轉換
    quote_count = 0
    result = []
    
    for char in text:
        if char == '"':
            if quote_count % 2 == 0:
                result.append('"')  # 開引號
            else:
                result.append('"')  # 閉引號
            quote_count += 1
        else:
            result.append(char)
    
    return ''.join(result)
```

## 時間戳保留策略

### 1. 段落時間範圍
```python
def calculate_segment_timespan(words):
    return {
        'start_ms': words[0].start,
        'end_ms': words[-1].end,
        'source_utterance_indices': get_source_indices(words)
    }
```

### 2. 跨 Utterance 合併
當句子跨越多個原始 utterances 時：
- 記錄所有相關的 `source_utterance_indices`
- 計算整體時間範圍
- 保持時間連續性

## 特殊處理規則

### 1. 短語氣詞處理
```python
def handle_short_fillers(sentence):
    """處理連續語氣詞造成的短句"""
    if (len(sentence.text) < 3 and 
        is_filler_only(sentence.text) and
        gap_to_previous < TH_SENT_GAP_SEC):
        merge_with_previous(sentence)
```

### 2. 中英混合文本
```python
def handle_mixed_language(text):
    """保留中英文間必要空格"""
    # 中文與英文字母間加空格
    text = re.sub(r'([\u4e00-\u9fff])([a-zA-Z])', r'\1 \2', text)
    text = re.sub(r'([a-zA-Z])([\u4e00-\u9fff])', r'\1 \2', text)
    
    # 移除多餘空格
    text = re.sub(r'\s+', ' ', text)
    
    return text
```

## 品質保證機制

### 1. 語意完整性檢查
```python
def verify_content_integrity(original_words, processed_segments):
    """確保沒有遺漏或增加詞彙"""
    original_content = ''.join([w.text for w in original_words])
    processed_content = ''.join([s.text for s in processed_segments])
    
    # 移除標點符號後比較
    original_clean = remove_punctuation(original_content)
    processed_clean = remove_punctuation(processed_content)
    
    assert original_clean == processed_clean
```

### 2. 時間連續性檢查
```python
def verify_time_continuity(segments):
    """確保時間戳的邏輯順序"""
    for i in range(len(segments) - 1):
        assert segments[i].end_ms <= segments[i+1].start_ms
```

## 輸出格式

```json
{
  "segments": [{
    "speaker": "A",
    "start_ms": 1234,
    "end_ms": 5678,
    "text": "修正後的中文分句文本，含適當標點。",
    "source_utterance_indices": [0, 1],
    "note": "句界重切，添加句號"
  }]
}
```

## 用戶故事

- [US-2.1: 智能句界切分](./user-story-2.1-sentence-boundary.md)
- [US-2.2: 中文標點符號修復](./user-story-2.2-punctuation-repair.md)

## 測試策略

### 語言學測試
- 各種中文句式的標點正確性
- 疑問句、感嘆句、陳述句識別
- 複雜語氣詞組合處理

### 技術測試
- 時間戳保留準確性
- 大文本處理效能
- 邊界條件處理

## 效能指標

1. **標點準確率** ≥ 95%
2. **句界切分準確率** ≥ 90%
3. **處理速度** < 1 秒/分鐘音檔
4. **語意保真率** = 100%