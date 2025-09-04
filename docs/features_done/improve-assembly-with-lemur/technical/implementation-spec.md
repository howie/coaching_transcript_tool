# 技術實施規格

## 核心介面設計

### 主函數簽名

```python
def smooth_and_punctuate(
    transcript_json: dict,
    th_short_head_sec: float = 0.9,
    th_filler_max_sec: float = 0.6,
    th_gap_sec: float = 0.25,
    th_max_move_sec: float = 1.5,
    th_sent_gap_sec: float = 0.6,
    th_echo_max_sec: float = 1.2,
    th_echo_gap_sec: float = 1.2,
    echo_jaccard_tau: float = 0.6,
    filler_whitelist: list[str] = None,
    n_pass: int = 2
) -> dict:
    """
    AssemblyAI 逐字稿講者邊界平滑與中文標點修復
    
    Args:
        transcript_json: AssemblyAI transcript 部分（含 utterances.words）
        th_short_head_sec: 短首段閾值（秒）
        th_filler_max_sec: 語氣詞最大時長（秒）
        th_gap_sec: 講者間隔閾值（秒）
        th_max_move_sec: 最大移動時長（秒）
        th_sent_gap_sec: 句界切分停頓閾值（秒）
        th_echo_max_sec: 回聲回填最大時長（秒）
        th_echo_gap_sec: 回聲間隔閾值（秒）
        echo_jaccard_tau: 回聲相似度閾值
        filler_whitelist: 語氣詞白名單
        n_pass: 最大迭代次數
        
    Returns:
        dict: 處理結果，包含 segments 和 stats
        
    Raises:
        ValueError: 當 utterances 或 words 缺失時
    """
```

## 資料結構定義

### 輸入格式驗證

```python
from typing import List, Dict, Optional
from pydantic import BaseModel, validator

class WordTimestamp(BaseModel):
    text: str
    start: int  # milliseconds
    end: int    # milliseconds

class Utterance(BaseModel):
    speaker: str
    start: int  # milliseconds  
    end: int    # milliseconds
    confidence: float
    words: List[WordTimestamp]
    
    @validator('words')
    def words_not_empty(cls, v):
        if not v:
            raise ValueError("words 缺失，無法做時間戳平滑")
        return v

class TranscriptInput(BaseModel):
    utterances: List[Utterance]
    
    @validator('utterances')
    def utterances_not_empty(cls, v):
        if not v:
            raise ValueError("utterances 缺失")
        return v
```

### 輸出格式定義

```python
class ProcessedSegment(BaseModel):
    speaker: str
    start_ms: int
    end_ms: int
    text: str
    source_utterance_indices: List[int]
    note: Optional[str] = None

class HeuristicStats(BaseModel):
    short_first_segment: int = 0
    filler_words: int = 0
    no_terminal_punct: int = 0
    echo_backfill: int = 0

class ProcessingStats(BaseModel):
    moved_word_count: int
    merged_segments: int
    split_segments: int
    heuristic_hits: HeuristicStats

class ProcessingResult(BaseModel):
    segments: List[ProcessedSegment]
    stats: ProcessingStats
```

## 核心算法實現

### 1. 講者邊界平滑器

```python
class SpeakerBoundarySmoother:
    def __init__(self, config: SmoothingConfig):
        self.config = config
        self.stats = HeuristicStats()
    
    def smooth_boundaries(self, utterances: List[Utterance]) -> List[Utterance]:
        """多輪迭代平滑講者邊界"""
        smoothed = utterances.copy()
        
        for pass_num in range(self.config.n_pass):
            changed = False
            new_smoothed = []
            
            for i in range(len(smoothed)):
                if i < len(smoothed) - 1:
                    current, next_utt = smoothed[i], smoothed[i + 1]
                    merged = self._try_merge_segments(current, next_utt)
                    
                    if merged:
                        new_smoothed.append(merged)
                        changed = True
                        i += 1  # 跳過已合併的下一個
                    else:
                        new_smoothed.append(current)
                else:
                    new_smoothed.append(smoothed[i])
            
            smoothed = new_smoothed
            if not changed:
                break
                
        return smoothed
    
    def _try_merge_segments(self, current: Utterance, next_utt: Utterance) -> Optional[Utterance]:
        """嘗試合併相鄰段落"""
        if current.speaker == next_utt.speaker:
            return None
            
        # 規則 1: 短首段回填
        merge_result = self._check_short_head_backfill(current, next_utt)
        if merge_result:
            self.stats.short_first_segment += 1
            return merge_result
            
        # 規則 2: 語氣詞回填
        merge_result = self._check_filler_backfill(current, next_utt)
        if merge_result:
            self.stats.filler_words += 1
            return merge_result
            
        # 規則 3: 回聲回填
        merge_result = self._check_echo_backfill(current, next_utt)
        if merge_result:
            self.stats.echo_backfill += 1
            return merge_result
            
        return None
    
    def _check_short_head_backfill(self, current: Utterance, next_utt: Utterance) -> Optional[Utterance]:
        """短首段回填規則"""
        # 計算下一段開頭部分的時長
        head_duration = self._calculate_head_duration(next_utt)
        
        if (head_duration < self.config.th_short_head_sec and 
            not self._has_terminal_punctuation(current.words[-1].text)):
            
            # 找出要回填的詞數
            words_to_move = self._get_words_within_duration(
                next_utt.words, self.config.th_short_head_sec
            )
            
            if self._calculate_total_duration(words_to_move) <= self.config.th_max_move_sec:
                return self._merge_words_to_previous(current, next_utt, words_to_move)
                
        return None
    
    def _check_filler_backfill(self, current: Utterance, next_utt: Utterance) -> Optional[Utterance]:
        """語氣詞回填規則"""
        if not next_utt.words:
            return None
            
        first_word = next_utt.words[0]
        word_duration = (first_word.end - first_word.start) / 1000.0
        
        if (first_word.text in self.config.filler_whitelist and 
            word_duration < self.config.th_filler_max_sec):
            
            return self._merge_words_to_previous(current, next_utt, [first_word])
            
        return None
    
    def _check_echo_backfill(self, current: Utterance, next_utt: Utterance) -> Optional[Utterance]:
        """回聲引述回填規則"""
        # 檢查引號包圍
        if self._has_quotation_marks(next_utt.words):
            quoted_content = self._extract_quoted_content(next_utt.words)
            if self._find_echo_in_previous(current.words, quoted_content):
                words_to_move = self._get_quoted_words(next_utt.words)
                
                if self._calculate_total_duration(words_to_move) <= self.config.th_echo_max_sec:
                    return self._merge_words_to_previous(current, next_utt, words_to_move)
        
        # 檢查重複內容
        similarity = self._calculate_similarity(
            current.words[-6:], next_utt.words[:6]  # 檢查前後各6個詞
        )
        
        if similarity >= self.config.echo_jaccard_tau:
            echo_words = self._find_echo_words(current.words, next_utt.words)
            
            if self._calculate_total_duration(echo_words) <= self.config.th_echo_max_sec:
                return self._merge_words_to_previous(current, next_utt, echo_words)
                
        return None
```

### 2. 中文標點修復器

```python
class ChinesePunctuationRepairer:
    def __init__(self, config: PunctuationConfig):
        self.config = config
    
    def repair_punctuation(self, utterances: List[Utterance]) -> List[ProcessedSegment]:
        """修復中文標點符號"""
        # 先合併所有詞彙並保留時間戳
        all_words = self._flatten_words_with_speaker(utterances)
        
        # 依據停頓切分句子
        sentences = self._split_into_sentences(all_words)
        
        # 為每個句子添加適當標點
        segments = []
        for sentence_words in sentences:
            segment = self._create_segment_with_punctuation(sentence_words)
            segments.append(segment)
            
        return segments
    
    def _split_into_sentences(self, words: List[WordWithSpeaker]) -> List[List[WordWithSpeaker]]:
        """依據停頓時間切分句子"""
        sentences = []
        current_sentence = []
        
        for i, word in enumerate(words):
            current_sentence.append(word)
            
            # 檢查與下一個詞的間隔
            if i < len(words) - 1:
                gap = (words[i + 1].start - word.end) / 1000.0
                
                if gap > self.config.th_sent_gap_sec:
                    # 檢查句子長度，避免過短
                    sentence_text = ''.join([w.text for w in current_sentence])
                    if len(sentence_text.strip()) >= 3:
                        sentences.append(current_sentence)
                        current_sentence = []
                    # 否則繼續累積到下一句
        
        # 處理最後一句
        if current_sentence:
            sentences.append(current_sentence)
            
        return sentences
    
    def _create_segment_with_punctuation(self, words: List[WordWithSpeaker]) -> ProcessedSegment:
        """為句子添加適當標點符號"""
        if not words:
            raise ValueError("Empty sentence")
            
        # 合併文本
        text = ''.join([w.text for w in words])
        
        # 判斷標點符號
        punctuation = self._determine_punctuation(text)
        
        # 標準化標點符號（半形轉全形）
        text_with_punct = self._normalize_punctuation(text + punctuation)
        
        # 處理引號
        text_with_punct = self._process_smart_quotes(text_with_punct)
        
        return ProcessedSegment(
            speaker=words[0].speaker,
            start_ms=words[0].start,
            end_ms=words[-1].end,
            text=text_with_punct,
            source_utterance_indices=list(set([w.utterance_index for w in words])),
            note=f"添加標點：{punctuation}"
        )
    
    def _determine_punctuation(self, text: str) -> str:
        """判斷適當的標點符號"""
        # 疑問語氣偵測
        question_patterns = ['嗎', '呢', '是不是', '對不對', '好不好', '怎麼', '什麼', '哪裡', '為什麼']
        if any(pattern in text for pattern in question_patterns):
            return '？'
        
        # 強烈語氣偵測
        exclamation_patterns = ['真的', '太', '非常', '超級', '哇', '哎呀', '天啊', '不行', '一定要']
        if any(pattern in text for pattern in exclamation_patterns):
            return '！'
        
        # 省略語氣偵測
        ellipsis_patterns = ['之類的', '什麼的', '等等', '等等等']
        if any(text.endswith(pattern) for pattern in ellipsis_patterns):
            return '…'
        
        # 預設句號
        return '。'
    
    def _normalize_punctuation(self, text: str) -> str:
        """標準化標點符號（半形轉全形）"""
        punctuation_map = {
            ',': '，', '.': '。', '?': '？', '!': '！',
            ':': '：', ';': '；', '(': '（', ')': '）'
        }
        
        for half, full in punctuation_map.items():
            text = text.replace(half, full)
            
        return text
    
    def _process_smart_quotes(self, text: str) -> str:
        """處理智能引號"""
        result = []
        quote_count = 0
        
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

## 配置管理

```python
@dataclass
class SmoothingConfig:
    th_short_head_sec: float = 0.9
    th_filler_max_sec: float = 0.6
    th_gap_sec: float = 0.25
    th_max_move_sec: float = 1.5
    th_echo_max_sec: float = 1.2
    th_echo_gap_sec: float = 1.2
    echo_jaccard_tau: float = 0.6
    n_pass: int = 2
    filler_whitelist: List[str] = field(default_factory=lambda: [
        "嗯", "呃", "唉", "喔", "哦", "唔", "啊", "欸", "對", "好",
        "唉呀", "唉呦", "哦對", "欸對"
    ])

@dataclass  
class PunctuationConfig:
    th_sent_gap_sec: float = 0.6
    min_sentence_length: int = 3
    
class ProcessorConfig:
    def __init__(self):
        self.smoothing = SmoothingConfig()
        self.punctuation = PunctuationConfig()
```

## 錯誤處理

```python
class TranscriptProcessingError(Exception):
    """轉錄處理相關錯誤"""
    pass

class MissingWordsError(TranscriptProcessingError):
    """Words 資料缺失錯誤"""
    pass

def validate_input(transcript_json: dict) -> None:
    """驗證輸入資料完整性"""
    if 'utterances' not in transcript_json:
        raise TranscriptProcessingError("Utterances missing from transcript")
    
    utterances = transcript_json['utterances']
    if not utterances:
        raise TranscriptProcessingError("Empty utterances list")
    
    for i, utterance in enumerate(utterances):
        if 'words' not in utterance or not utterance['words']:
            raise MissingWordsError(
                f"Words missing in utterance {i}; cannot perform smoothing"
            )
```

## 效能最佳化

### 1. 記憶體效率

```python
def process_in_batches(utterances: List[Utterance], batch_size: int = 100) -> List[ProcessedSegment]:
    """批次處理大量 utterances"""
    results = []
    
    for i in range(0, len(utterances), batch_size):
        batch = utterances[i:i + batch_size]
        batch_result = smooth_and_punctuate_batch(batch)
        results.extend(batch_result)
        
    return results
```

### 2. 快取機制

```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def calculate_text_similarity(text1: str, text2: str) -> float:
    """快取文本相似度計算結果"""
    return jaccard_similarity(text1, text2)
```

## 測試框架

```python
class TestSpeakerBoundarySmoothing:
    def test_short_head_backfill_should_merge(self):
        """測試短首段回填應該發生的情況"""
        # Arrange
        current = create_utterance("A", "然後我們就先這樣", has_terminal_punct=False)
        next_utt = create_utterance("B", "嗯 對", duration=0.5)
        
        # Act
        result = smoother._try_merge_segments(current, next_utt)
        
        # Assert
        assert result is not None
        assert result.speaker == "A"
        assert "嗯 對" in result.text
    
    def test_terminal_punct_should_not_merge(self):
        """測試有終止標點不應回填"""
        # Arrange  
        current = create_utterance("A", "然後我們就先這樣。", has_terminal_punct=True)
        next_utt = create_utterance("B", "嗯", duration=0.4)
        
        # Act
        result = smoother._try_merge_segments(current, next_utt)
        
        # Assert
        assert result is None
```

## API 整合設計

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/transcript")

class SmoothingRequest(BaseModel):
    transcript: dict
    config: Optional[dict] = None

class SmoothingResponse(BaseModel):
    segments: List[ProcessedSegment]
    stats: ProcessingStats
    processing_time_ms: int

@router.post("/smooth-and-punctuate", response_model=SmoothingResponse)
async def smooth_transcript(request: SmoothingRequest):
    """平滑講者邊界並修復中文標點"""
    try:
        start_time = time.time()
        
        result = smooth_and_punctuate(
            request.transcript,
            **(request.config or {})
        )
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return SmoothingResponse(
            segments=result['segments'],
            stats=result['stats'],
            processing_time_ms=processing_time
        )
        
    except MissingWordsError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")
```