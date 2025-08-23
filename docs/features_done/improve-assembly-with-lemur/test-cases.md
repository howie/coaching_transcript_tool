# 測試案例與驗收標準

## 講者邊界平滑測試案例

### Case 1: 短首段回填（應回填）

**測試場景**：句尾被下一位講者錯誤切分

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A", 
      "start": 1000, 
      "end": 5000,
      "words": [
        {"text": "然後", "start": 1000, "end": 1500},
        {"text": "我們", "start": 1500, "end": 2000}, 
        {"text": "就", "start": 2000, "end": 2300},
        {"text": "先", "start": 2300, "end": 2600},
        {"text": "這樣", "start": 2600, "end": 3000}
      ]
    },
    {
      "speaker": "B",
      "start": 3100,
      "end": 3600, 
      "words": [
        {"text": "嗯", "start": 3100, "end": 3300},
        {"text": "對", "start": 3300, "end": 3600}
      ]
    }
  ]
}
```

**期望輸出**：
```json
{
  "segments": [
    {
      "speaker": "A",
      "start_ms": 1000,
      "end_ms": 3600,
      "text": "然後我們就先這樣嗯對。",
      "source_utterance_indices": [0, 1],
      "note": "短首段回填"
    }
  ],
  "stats": {
    "moved_word_count": 2,
    "merged_segments": 1,
    "heuristic_hits": {
      "short_first_segment": 1
    }
  }
}
```

**驗收標準**：
- ✅ 短語氣詞「嗯對」正確回填給講者 A
- ✅ 時間戳正確合併（1000-3600ms）
- ✅ 統計數據正確記錄

### Case 2: 有終止標點（不應回填）

**測試場景**：前句已有完整標點，不應回填

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A",
      "start": 1000,
      "end": 3000, 
      "words": [
        {"text": "好", "start": 1000, "end": 1300},
        {"text": "的", "start": 1300, "end": 1600},
        {"text": "。", "start": 1600, "end": 1700}
      ]
    },
    {
      "speaker": "B",
      "start": 3100,
      "end": 3400,
      "words": [
        {"text": "嗯", "start": 3100, "end": 3400}
      ]
    }
  ]
}
```

**期望輸出**：
```json
{
  "segments": [
    {
      "speaker": "A", 
      "start_ms": 1000,
      "end_ms": 1700,
      "text": "好的。",
      "source_utterance_indices": [0]
    },
    {
      "speaker": "B",
      "start_ms": 3100, 
      "end_ms": 3400,
      "text": "嗯。",
      "source_utterance_indices": [1]
    }
  ]
}
```

**驗收標準**：
- ✅ 有終止標點時不觸發回填
- ✅ 保持原有講者分段
- ✅ 各自添加適當標點

### Case 3: 超過最大移動量（不應回填）

**測試場景**：下一段時長超過閾值

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A",
      "start": 1000,
      "end": 3000,
      "words": [{"text": "我覺得", "start": 1000, "end": 3000}]
    },
    {
      "speaker": "B", 
      "start": 3100,
      "end": 4900,
      "words": [
        {"text": "這個", "start": 3100, "end": 3400},
        {"text": "想法", "start": 3400, "end": 3800},
        {"text": "很", "start": 3800, "end": 4000},
        {"text": "不錯", "start": 4000, "end": 4400},
        {"text": "呢", "start": 4400, "end": 4900}
      ]
    }
  ]
}
```

**期望輸出**：保持原有分段，不進行回填

**驗收標準**：
- ✅ 超過 1.5 秒限制不回填
- ✅ 統計中 `moved_word_count = 0`

### Case 4: 引用回聲回填

**測試場景**：引用句被誤分配

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A",
      "start": 1000,
      "end": 6000,
      "words": [
        {"text": "這件", "start": 1000, "end": 1300},
        {"text": "事", "start": 1300, "end": 1500},
        {"text": "啊", "start": 1500, "end": 1700},
        {"text": "你", "start": 2000, "end": 2200},
        {"text": "用", "start": 2200, "end": 2400},
        {"text": "的", "start": 2400, "end": 2600},
        {"text": "這個", "start": 2600, "end": 2900},
        {"text": "字", "start": 2900, "end": 3100},
        {"text": "也", "start": 3300, "end": 3500},
        {"text": "蠻", "start": 3500, "end": 3700},
        {"text": "算", "start": 4000, "end": 4200},
        {"text": "有點", "start": 4200, "end": 4500},
        {"text": "強烈", "start": 4500, "end": 4800},
        {"text": "喔", "start": 4800, "end": 5000}
      ]
    },
    {
      "speaker": "B",
      "start": 6100,
      "end": 8500,
      "words": [
        {"text": "「", "start": 6100, "end": 6150},
        {"text": "算", "start": 6150, "end": 6300},
        {"text": "有點", "start": 6300, "end": 6600},
        {"text": "強烈", "start": 6600, "end": 6900},
        {"text": "喔", "start": 6900, "end": 7100},
        {"text": "」", "start": 7100, "end": 7150},
        {"text": "對", "start": 7300, "end": 7500},
        {"text": "其實", "start": 7600, "end": 7900},
        {"text": "沒有", "start": 7900, "end": 8200},
        {"text": "那麼", "start": 8200, "end": 8500},
        {"text": "嚴重", "start": 8500, "end": 8800}
      ]
    }
  ]
}
```

**期望輸出**：
```json
{
  "segments": [
    {
      "speaker": "A",
      "start_ms": 1000,
      "end_ms": 7150,
      "text": "這件事啊，你用的這個字也蠻，算有點，強烈喔「算有點強烈喔」。",
      "source_utterance_indices": [0, 1],
      "note": "引用回聲回填"
    },
    {
      "speaker": "B", 
      "start_ms": 7300,
      "end_ms": 8800,
      "text": "對，其實沒有那麼嚴重。",
      "source_utterance_indices": [1]
    }
  ]
}
```

**驗收標準**：
- ✅ 引用句正確回填給原講者
- ✅ 引號內容識別準確
- ✅ 時間戳正確調整

## 中文標點修復測試案例

### Case 5: 疑問句標點修復

**測試場景**：疑問語氣自動添加問號

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A",
      "start": 1000,
      "end": 3000,
      "words": [
        {"text": "你", "start": 1000, "end": 1200},
        {"text": "覺得", "start": 1200, "end": 1600},
        {"text": "怎麼樣", "start": 1600, "end": 2200},
        {"text": "呢", "start": 2200, "end": 2400}
      ]
    }
  ]
}
```

**期望輸出**：
```json
{
  "segments": [
    {
      "speaker": "A",
      "start_ms": 1000, 
      "end_ms": 2400,
      "text": "你覺得怎麼樣呢？",
      "note": "添加標點：？"
    }
  ]
}
```

**驗收標準**：
- ✅ 疑問語氣詞「呢」觸發問號
- ✅ 全形標點符號
- ✅ 無多餘空格

### Case 6: 感嘆句標點修復

**測試場景**：強烈語氣自動添加感嘆號

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "B",
      "start": 1000,
      "end": 2500,
      "words": [
        {"text": "哇", "start": 1000, "end": 1200},
        {"text": "真的", "start": 1200, "end": 1600},
        {"text": "太", "start": 1600, "end": 1800},
        {"text": "厲害", "start": 1800, "end": 2200},
        {"text": "了", "start": 2200, "end": 2500}
      ]
    }
  ]
}
```

**期望輸出**：
```json
{
  "segments": [
    {
      "speaker": "B",
      "start_ms": 1000,
      "end_ms": 2500, 
      "text": "哇真的太厲害了！",
      "note": "添加標點：！"
    }
  ]
}
```

**驗收標準**：
- ✅ 感嘆詞「哇」和強語氣「太」觸發感嘆號
- ✅ 正確識別情緒表達

### Case 7: 長句切分

**測試場景**：依據停頓時間切分長句

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A",
      "start": 1000,
      "end": 8000,
      "words": [
        {"text": "我", "start": 1000, "end": 1200},
        {"text": "覺得", "start": 1200, "end": 1600},
        {"text": "這個", "start": 1600, "end": 2000},
        {"text": "方案", "start": 2000, "end": 2400},
        // 0.8 秒停頓
        {"text": "應該", "start": 3200, "end": 3600}, 
        {"text": "可以", "start": 3600, "end": 4000},
        {"text": "考慮", "start": 4000, "end": 4400},
        {"text": "一下", "start": 4400, "end": 4800},
        // 1.0 秒停頓
        {"text": "你", "start": 5800, "end": 6000},
        {"text": "覺得", "start": 6000, "end": 6400},
        {"text": "呢", "start": 6400, "end": 6600}
      ]
    }
  ]
}
```

**期望輸出**：
```json
{
  "segments": [
    {
      "speaker": "A",
      "start_ms": 1000,
      "end_ms": 2400,
      "text": "我覺得這個方案。",
      "source_utterance_indices": [0]
    },
    {
      "speaker": "A", 
      "start_ms": 3200,
      "end_ms": 4800,
      "text": "應該可以考慮一下。",
      "source_utterance_indices": [0]
    },
    {
      "speaker": "A",
      "start_ms": 5800,
      "end_ms": 6600, 
      "text": "你覺得呢？",
      "source_utterance_indices": [0]
    }
  ]
}
```

**驗收標準**：
- ✅ 停頓 > 0.6 秒觸發句界切分
- ✅ 同講者保持分段
- ✅ 各句添加適當標點

### Case 8: 智能引號處理

**測試場景**：引號配對處理

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A",
      "start": 1000,
      "end": 5000,
      "words": [
        {"text": "他", "start": 1000, "end": 1200},
        {"text": "說", "start": 1200, "end": 1400},
        {"text": "\"", "start": 1400, "end": 1450},
        {"text": "這樣", "start": 1450, "end": 1800},
        {"text": "不行", "start": 1800, "end": 2100},
        {"text": "\"", "start": 2100, "end": 2150},
        {"text": "我", "start": 2300, "end": 2500},
        {"text": "覺得", "start": 2500, "end": 2800},
        {"text": "有", "start": 2800, "end": 3000},
        {"text": "道理", "start": 3000, "end": 3400}
      ]
    }
  ]
}
```

**期望輸出**：
```json
{
  "segments": [
    {
      "speaker": "A",
      "start_ms": 1000,
      "end_ms": 3400,
      "text": "他說"這樣不行"我覺得有道理。",
      "note": "智能引號配對"
    }
  ]
}
```

**驗收標準**：
- ✅ 半形引號轉全形配對引號
- ✅ 開閉引號正確配對

## 邊界條件測試

### Case 9: 空 words 陣列

**輸入**：
```json
{
  "utterances": [
    {
      "speaker": "A",
      "start": 1000,
      "end": 2000,
      "words": []
    }
  ]
}
```

**期望輸出**：
```json
{
  "error": "words 缺失，無法做時間戳平滑"
}
```

### Case 10: 缺少 utterances

**輸入**：
```json
{}
```

**期望輸出**：
```json
{
  "error": "Utterances or words missing; cannot perform smoothing."
}
```

### Case 11: 極短音檔

**輸入**：單個詞的 utterance

**期望輸出**：正確處理，不發生錯誤

## 效能測試標準

### 處理速度要求
- **小檔案** (< 5 分鐘)：< 1 秒處理時間
- **中檔案** (5-30 分鐘)：< 5 秒處理時間  
- **大檔案** (30-120 分鐘)：< 20 秒處理時間

### 記憶體使用
- **峰值記憶體** < 200MB（120 分鐘音檔）
- **無記憶體洩漏**

### 準確率要求
- **講者邊界修正準確率** ≥ 90%
- **標點符號準確率** ≥ 95%
- **語意保真率** = 100%（絕不修改原文）

## 自動化測試框架

### 單元測試覆蓋率
- **核心算法** ≥ 95%
- **邊界條件** ≥ 90%
- **錯誤處理** = 100%

### 整合測試
- 端到端處理流程
- 多種音檔類型測試
- 異常情況恢復測試

### 迴歸測試
- 維護標準測試集
- 每次代碼變更必須通過全部案例
- 效能退化監控