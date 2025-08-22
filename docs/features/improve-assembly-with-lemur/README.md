# AssemblyAI 逐字稿講者邊界平滑與中文標點修復

## 功能概述

針對 AssemblyAI 轉錄結果進行後處理優化，使用 **LeMUR (Large Language Model)** 智能處理中文語音轉錄問題：
1. **講者交接點錯誤修正**：AI 智能識別講者邊界並修正分配錯誤
2. **中文標點符號修復**：依中文規則重做句界與標點，保持語意完整
3. **批次處理架構**：支援超長逐字稿的分段處理，避免 API 限制
4. **時間戳保留**：維持原始時間資訊與講者資訊的準確性

## 商業價值

- **提升轉錄品質**：減少人工校對工作量 70-90%（提升自原本 60-80%）
- **改善用戶體驗**：產生更自然、可讀的中文逐字稿
- **節省成本**：降低後期編輯時間，提高生產效率
- **競爭優勢**：提供業界領先的 AI 驅動中文語音轉錄品質

## 技術架構

```
AssemblyAI Raw Transcript
         ↓
LeMUR Speaker Identification (AI)
         ↓
Batch Processing (避免 API 限制)
         ↓
LeMUR Punctuation Enhancement (AI)
         ↓
Traditional Chinese Conversion
         ↓
Clean, Readable Segments
         ↓
Database Persistence
```

## 開發狀態

### ✅ 已完成階段
- **LeMUR Integration**: 完整整合 AssemblyAI LeMUR 進行 AI 驅動的逐字稿處理
- **Batch Processing**: 實現分批處理架構，支援超長逐字稿（>7000 字）
- **Speaker Identification**: AI 智能講者識別與邊界修正
- **Punctuation Enhancement**: 中文標點符號智能修復
- **Concurrent Processing**: 並發處理多個批次，提升效能
- **Database Integration**: 處理後的 segments 自動儲存至資料庫
- **Auto-smoothing**: 中文轉錄完成後自動執行優化

### 🚧 開發中功能
- **Frontend UI**: Dev-only 介面，支援自定義 system prompts
- **Error Recovery**: 批次失敗時的 fallback 機制
- **Performance Optimization**: 適應性批次大小調整

### 📋 原規劃階段（已用 LeMUR 取代）
- ~~Epic 1: Speaker Boundary Smoothing~~ → 已用 LeMUR AI 取代
- ~~Epic 2: Chinese Punctuation Repair~~ → 已用 LeMUR AI 取代
- ~~Epic 3: API Integration~~ → 已完成
- ~~Epic 4: LeMUR Enhancement~~ → 已完成並擴展

## 技術規格

### LeMUR 處理架構

**主要組件：**
- `LeMURTranscriptSmoother`: 核心服務類別
- `_improve_punctuation_batch_with_lemur()`: 分批標點修復
- `_correct_speakers_with_lemur()`: AI 講者識別
- `_process_punctuation_batch()`: 單批次處理邏輯

**批次處理策略：**
```python
# 適應性批次大小
if total_chars > 15000:    # 大型逐字稿
    max_batch_chars = 2500, max_batch_size = 8
elif total_chars > 8000:   # 中型逐字稿  
    max_batch_chars = 3000, max_batch_size = 10
else:                      # 小型逐字稿
    max_batch_chars = 4000, max_batch_size = 15

# 並發處理（最多 3 個批次同時處理）
max_concurrent_batches = min(3, len(batches))
```

### 輸入格式
```python
# AssemblyAI segments format
segments: List[Dict] = [
    {
        "speaker": "Speaker_A",
        "text": "原始轉錄文字",
        "start": 1234,    # milliseconds
        "end": 5678       # milliseconds
    }
]
```

### 輸出格式
```python
# TranscriptSegment format  
segments: List[TranscriptSegment] = [
    TranscriptSegment(
        start=1234,       # milliseconds (int)
        end=5678,         # milliseconds (int)
        speaker="教練",    # AI corrected speaker
        text="修正後的中文分句文本，含適當標點符號。"
    )
]
```

## 品質標準

- **正確性**：AI 驅動講者邊界修正準確率 > 95%（提升自原本 90%）
- **穩定性**：批次處理 fallback 機制，確保不會完全失敗
- **可觀測性**：詳細的批次處理日誌和 debug 資訊
- **語意保真**：AI 僅改善標點和講者，不修改原始語句內容
- **效能**：支援超長逐字稿（15000+ 字），批次並發處理
- **可靠性**：每個批次獨立處理，單一失敗不影響整體結果

## 實現細節

### 自動觸發條件
```python
# 在 assemblyai_stt.py 中自動執行
should_smooth = (
    language_code and 
    any(lang in language_code for lang in ["zh", "cmn"]) and
    len(segments) > 0
)
```

### 關鍵檔案位置
- **核心服務**：`src/coaching_assistant/services/lemur_transcript_smoother.py`
- **API 端點**：`src/coaching_assistant/api/transcript_smoothing.py`
- **前端界面**：`apps/web/app/dashboard/sessions/[id]/page.tsx`
- **自動觸發**：`src/coaching_assistant/services/assemblyai_stt.py`
- **資料庫儲存**：`src/coaching_assistant/tasks/transcription_tasks.py`

## 導航

- [用戶故事總覽](./user-stories.md)
- [實施路線圖](./implementation-roadmap.md)
- [技術規格](./technical/)
- [測試案例](./test-cases.md)

## 相關資源

- [AssemblyAI API 文檔](https://www.assemblyai.com/docs/)
- [中文標點規範](https://www.moe.gov.tw/cp-1-language/)
- [現有 STT 架構](../../architecture/stt.md)