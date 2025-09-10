# AI 分析功能技術規格

## 🤖 項目 7: AI 分析 tab 與 LLM 對談功能

此文檔詳細規劃新增的 AI 分析功能，包括與 LLM 對談、摘要生成和回饋生成等核心功能。

---

## 📋 功能概覽

### 核心功能
1. **AI 分析 Tab**: 獨立的分析介面
2. **產生會談摘要**: 結構化摘要生成
3. **給予會談回饋**: 學習導向的回饋建議
4. **LLM 對談介面**: 自由對話功能（未來擴展）

### 設計原則
- **學習輔助導向**: 避免評分式回饋
- **結構化輸出**: 易讀易懂的分析結果
- **多語言支援**: 中英文分析
- **性能優化**: 合理的回應時間

---

## 🏗️ 系統架構

### 整體架構
```
前端 (Next.js)
├── AI 分析 Tab 組件
├── 摘要生成介面
├── 回饋生成介面
└── 對談介面 (未來)

後端 (FastAPI)
├── AI 分析 API 端點
├── LLM 服務層
├── Prompt 管理
└── 結果處理

外部服務
├── AssemblyAI LeMUR (主要)
├── OpenAI GPT (備用)
└── 其他 LLM 服務 (未來)
```

---

## 🎨 前端實作規格

### 組件架構
```
apps/web/components/ai-analysis/
├── AIAnalysisTab.tsx          # 主容器組件
├── SummaryGenerator.tsx       # 摘要生成器
├── FeedbackGenerator.tsx      # 回饋生成器
├── AnalysisResult.tsx         # 結果顯示組件
├── LoadingState.tsx           # 載入狀態
└── ErrorState.tsx             # 錯誤狀態
```

### 主要組件實作

#### AIAnalysisTab.tsx
```typescript
import React, { useState } from 'react';
import { useTranscriptData } from '@/hooks/useTranscriptData';
import { SummaryGenerator } from './SummaryGenerator';
import { FeedbackGenerator } from './FeedbackGenerator';

interface AIAnalysisTabProps {
  sessionId: string;
}

export const AIAnalysisTab: React.FC<AIAnalysisTabProps> = ({ sessionId }) => {
  const { transcript, loading } = useTranscriptData(sessionId);
  const [activeAnalysis, setActiveAnalysis] = useState<string | null>(null);

  if (loading) {
    return <LoadingState />;
  }

  return (
    <div className="ai-analysis-tab">
      <div className="analysis-header">
        <h2>🤖 AI 分析</h2>
        <p>使用 AI 技術深度分析您的教練會談</p>
      </div>

      <div className="analysis-tools">
        <div className="tool-grid">
          <SummaryGenerator 
            sessionId={sessionId}
            transcript={transcript}
            isActive={activeAnalysis === 'summary'}
            onActivate={() => setActiveAnalysis('summary')}
          />
          
          <FeedbackGenerator
            sessionId={sessionId}
            transcript={transcript}
            isActive={activeAnalysis === 'feedback'}
            onActivate={() => setActiveAnalysis('feedback')}
          />
        </div>
      </div>

      <div className="analysis-results">
        {/* 分析結果顯示區域 */}
      </div>
    </div>
  );
};
```

#### SummaryGenerator.tsx
```typescript
import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { generateSummary } from '@/lib/api/ai-analysis';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';

interface SummaryGeneratorProps {
  sessionId: string;
  transcript: TranscriptData;
  isActive: boolean;
  onActivate: () => void;
}

export const SummaryGenerator: React.FC<SummaryGeneratorProps> = ({
  sessionId,
  transcript,
  isActive,
  onActivate
}) => {
  const [summary, setSummary] = useState<SummaryResult | null>(null);

  const summaryMutation = useMutation({
    mutationFn: () => generateSummary({
      session_id: sessionId,
      content: transcript.fullText,
      language: 'zh-TW'
    }),
    onSuccess: (result) => {
      setSummary(result);
      onActivate();
    },
    onError: (error) => {
      console.error('Summary generation failed:', error);
    }
  });

  return (
    <Card className="analysis-tool">
      <div className="tool-header">
        <h3>📋 會談摘要</h3>
        <p>生成結構化的會談摘要</p>
      </div>

      <div className="tool-content">
        <Button
          onClick={() => summaryMutation.mutate()}
          loading={summaryMutation.isPending}
          disabled={!transcript}
        >
          {summaryMutation.isPending ? '生成中...' : '產生會談摘要'}
        </Button>

        {summary && (
          <div className="summary-result">
            <SummaryDisplay summary={summary} />
          </div>
        )}
      </div>
    </Card>
  );
};
```

#### FeedbackGenerator.tsx
```typescript
import React, { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { generateFeedback } from '@/lib/api/ai-analysis';

interface FeedbackGeneratorProps {
  sessionId: string;
  transcript: TranscriptData;
  isActive: boolean;
  onActivate: () => void;
}

export const FeedbackGenerator: React.FC<FeedbackGeneratorProps> = ({
  sessionId,
  transcript,
  isActive,
  onActivate
}) => {
  const [feedback, setFeedback] = useState<FeedbackResult | null>(null);

  const feedbackMutation = useMutation({
    mutationFn: () => generateFeedback({
      session_id: sessionId,
      content: transcript.fullText,
      language: 'zh-TW',
      focus: 'learning_support' // 學習輔助導向
    }),
    onSuccess: (result) => {
      setFeedback(result);
      onActivate();
    }
  });

  return (
    <Card className="analysis-tool">
      <div className="tool-header">
        <h3>💡 會談回饋</h3>
        <p>獲得學習導向的建議和提示</p>
      </div>

      <div className="tool-content">
        <Button
          onClick={() => feedbackMutation.mutate()}
          loading={feedbackMutation.isPending}
          disabled={!transcript}
        >
          {feedbackMutation.isPending ? '分析中...' : '給予會談回饋'}
        </Button>

        {feedback && (
          <div className="feedback-result">
            <FeedbackDisplay feedback={feedback} />
          </div>
        )}
      </div>
    </Card>
  );
};
```

### 樣式設計

#### ai-analysis.css
```css
.ai-analysis-tab {
  padding: 1.5rem;
  max-width: 1200px;
  margin: 0 auto;
}

.analysis-header {
  text-align: center;
  margin-bottom: 2rem;
}

.analysis-header h2 {
  font-size: 1.75rem;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.analysis-header p {
  color: #6b7280;
  font-size: 1rem;
}

.tool-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.analysis-tool {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 1.5rem;
  background: white;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  transition: all 0.2s ease;
}

.analysis-tool:hover {
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.tool-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.tool-header p {
  color: #6b7280;
  font-size: 0.875rem;
  margin-bottom: 1rem;
}

.analysis-results {
  margin-top: 2rem;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .ai-analysis-tab {
    padding: 1rem;
  }
  
  .tool-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}
```

---

## 🔧 後端實作規格

### API 端點設計

#### 路由結構
```python
# src/coaching_assistant/api/v1/ai_analysis.py
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from .models import SummaryRequest, FeedbackRequest

router = APIRouter(prefix="/ai-analysis", tags=["AI Analysis"])

@router.post("/summary")
async def generate_summary(
    request: SummaryRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """生成會談摘要"""
    pass

@router.post("/feedback")  
async def generate_feedback(
    request: FeedbackRequest,
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """生成會談回饋"""
    pass
```

#### 請求/回應模型
```python
# src/coaching_assistant/api/v1/models/ai_analysis.py
from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class SummaryRequest(BaseModel):
    session_id: str
    content: str
    language: str = "zh-TW"
    format: str = "structured"  # structured, narrative

class SummaryResponse(BaseModel):
    session_id: str
    summary: Dict[str, Any]
    generated_at: str
    processing_time: float

class FeedbackRequest(BaseModel):
    session_id: str
    content: str
    language: str = "zh-TW"
    focus: str = "learning_support"  # learning_support, skill_development

class FeedbackResponse(BaseModel):
    session_id: str
    feedback: Dict[str, Any]
    generated_at: str
    processing_time: float
```

### LLM 服務層

#### AI 分析服務
```python
# src/coaching_assistant/services/ai_analysis.py
import asyncio
import time
from typing import Dict, Any, Optional
from ..core.config import settings
from .lemur_service import LeMURService
from .openai_service import OpenAIService

class AIAnalysisService:
    def __init__(self):
        self.lemur_service = LeMURService()
        self.openai_service = OpenAIService()  # 備用服務
        
    async def generate_summary(
        self, 
        content: str, 
        language: str = "zh-TW",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成會談摘要"""
        start_time = time.time()
        
        try:
            # 優先使用 LeMUR
            prompt = self._build_summary_prompt(content, language)
            result = await self.lemur_service.process(prompt)
            
            summary = self._parse_summary_result(result)
            
        except Exception as e:
            # 降級到 OpenAI
            logger.warning(f"LeMUR failed, falling back to OpenAI: {e}")
            result = await self.openai_service.generate_summary(content, language)
            summary = result
            
        processing_time = time.time() - start_time
        
        # 記錄分析歷史
        if session_id:
            await self._save_analysis_history(
                session_id, "summary", summary, processing_time
            )
            
        return {
            "summary": summary,
            "processing_time": processing_time,
            "provider": "lemur" if "lemur" in locals() else "openai"
        }

    async def generate_feedback(
        self,
        content: str,
        language: str = "zh-TW", 
        focus: str = "learning_support",
        session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """生成會談回饋"""
        start_time = time.time()
        
        try:
            prompt = self._build_feedback_prompt(content, language, focus)
            result = await self.lemur_service.process(prompt)
            feedback = self._parse_feedback_result(result)
            
        except Exception as e:
            logger.warning(f"LeMUR failed, falling back to OpenAI: {e}")
            result = await self.openai_service.generate_feedback(content, language, focus)
            feedback = result
            
        processing_time = time.time() - start_time
        
        if session_id:
            await self._save_analysis_history(
                session_id, "feedback", feedback, processing_time
            )
            
        return {
            "feedback": feedback,
            "processing_time": processing_time,
            "provider": "lemur" if "lemur" in locals() else "openai"
        }
```

### Prompt 設計

#### 摘要生成 Prompt
```python
def _build_summary_prompt(self, content: str, language: str) -> str:
    """構建摘要生成 prompt"""
    
    if language == "zh-TW":
        prompt = f"""
請分析以下教練會談逐字稿，並生成結構化摘要。

逐字稿內容：
{content}

請以 JSON 格式回應，包含以下結構：
{{
  "session_overview": {{
    "duration_estimate": "預估時長",
    "main_topic": "主要議題",
    "session_mood": "會談氛圍"
  }},
  "key_topics": [
    {{
      "topic": "議題名稱",
      "discussion_points": ["討論要點1", "討論要點2"],
      "insights": "關鍵洞察"
    }}
  ],
  "progress_indicators": [
    {{
      "area": "進展領域",
      "observation": "觀察到的進展",
      "evidence": "支持證據"
    }}
  ],
  "action_items": [
    {{
      "action": "行動項目",
      "owner": "負責人（教練/客戶）",
      "timeline": "時間框架"
    }}
  ],
  "coaching_notes": [
    "重要的教練筆記或觀察"
  ]
}}

請確保：
1. 摘要客觀準確，避免主觀判斷
2. 重點關注客戶的需求和目標
3. 識別具體的行動項目和下一步
4. 保持專業和建設性的語調
"""
    else:  # English
        prompt = f"""
Please analyze the following coaching session transcript and generate a structured summary.

Transcript content:
{content}

Please respond in JSON format with the following structure:
{{
  "session_overview": {{
    "duration_estimate": "estimated duration",
    "main_topic": "main topic discussed",
    "session_mood": "overall session atmosphere"
  }},
  "key_topics": [
    {{
      "topic": "topic name",
      "discussion_points": ["point 1", "point 2"],
      "insights": "key insights"
    }}
  ],
  "progress_indicators": [
    {{
      "area": "progress area",
      "observation": "observed progress",
      "evidence": "supporting evidence"
    }}
  ],
  "action_items": [
    {{
      "action": "action item",
      "owner": "responsible party (coach/client)",
      "timeline": "timeframe"
    }}
  ],
  "coaching_notes": [
    "important coaching notes or observations"
  ]
}}

Please ensure:
1. Summary is objective and accurate
2. Focus on client needs and goals
3. Identify specific action items and next steps
4. Maintain professional and constructive tone
"""
    
    return prompt
```

#### 回饋生成 Prompt
```python
def _build_feedback_prompt(self, content: str, language: str, focus: str) -> str:
    """構建回饋生成 prompt"""
    
    if language == "zh-TW":
        prompt = f"""
請分析以下教練會談逐字稿，並提供學習導向的回饋建議。

逐字稿內容：
{content}

請以 JSON 格式回應，包含以下結構：
{{
  "strengths_observed": [
    {{
      "skill_area": "技能領域",
      "observation": "觀察到的優勢",
      "examples": ["具體例子"],
      "impact": "對會談的正面影響"
    }}
  ],
  "learning_opportunities": [
    {{
      "area": "學習領域",
      "suggestion": "建議",
      "techniques": ["可嘗試的技巧"],
      "resources": ["學習資源建議"]
    }}
  ],
  "questioning_techniques": {{
    "effective_questions": ["有效的問題範例"],
    "suggested_improvements": ["問句改善建議"],
    "alternative_approaches": ["替代方法"]
  }},
  "communication_insights": {{
    "listening_patterns": "傾聽模式觀察",
    "response_style": "回應風格分析",
    "suggestions": ["溝通改善建議"]
  }},
  "next_session_considerations": [
    "下次會談的考慮要點"
  ]
}}

重要原則：
1. 避免評分或等級評估
2. 專注於學習和發展機會
3. 提供具體可行的建議
4. 保持鼓勵和支持的語調
5. 強調技能提升而非缺點指正
"""
    else:  # English
        prompt = f"""
Please analyze the following coaching session transcript and provide learning-oriented feedback.

Transcript content:
{content}

Please respond in JSON format with the following structure:
{{
  "strengths_observed": [
    {{
      "skill_area": "skill area",
      "observation": "observed strength",
      "examples": ["specific examples"],
      "impact": "positive impact on session"
    }}
  ],
  "learning_opportunities": [
    {{
      "area": "learning area",
      "suggestion": "suggestion",
      "techniques": ["techniques to try"],
      "resources": ["learning resource suggestions"]
    }}
  ],
  "questioning_techniques": {{
    "effective_questions": ["examples of effective questions"],
    "suggested_improvements": ["question improvement suggestions"],
    "alternative_approaches": ["alternative approaches"]
  }},
  "communication_insights": {{
    "listening_patterns": "listening pattern observations",
    "response_style": "response style analysis",
    "suggestions": ["communication improvement suggestions"]
  }},
  "next_session_considerations": [
    "considerations for next session"
  ]
}}

Important principles:
1. Avoid scoring or grading assessments
2. Focus on learning and development opportunities
3. Provide specific, actionable suggestions
4. Maintain encouraging and supportive tone
5. Emphasize skill enhancement rather than deficit correction
"""
    
    return prompt
```

---

## 🗄️ 資料模型

### 分析歷史表
```sql
-- 新增 AI 分析歷史表
CREATE TABLE ai_analysis_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES session(id) ON DELETE CASCADE,
    user_id UUID REFERENCES "user"(id) ON DELETE CASCADE,
    analysis_type VARCHAR(50) NOT NULL, -- 'summary', 'feedback'
    analysis_result JSONB NOT NULL,
    provider VARCHAR(50) NOT NULL, -- 'lemur', 'openai'
    processing_time FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_ai_analysis_session (session_id),
    INDEX idx_ai_analysis_user (user_id),
    INDEX idx_ai_analysis_type (analysis_type)
);
```

### 配置管理
```python
# src/coaching_assistant/core/config.py
class Settings(BaseSettings):
    # AI Analysis settings
    AI_ANALYSIS_ENABLED: bool = True
    AI_ANALYSIS_TIMEOUT: int = 30  # seconds
    AI_ANALYSIS_MAX_RETRIES: int = 2
    
    # LeMUR settings
    LEMUR_API_KEY: str
    LEMUR_BASE_URL: str = "https://api.assemblyai.com"
    
    # OpenAI backup settings
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
```

---

## 🔒 安全性考量

### 資料保護
```python
# 資料脫敏處理
def sanitize_transcript_for_ai(content: str) -> str:
    """移除敏感資訊後再送給 AI 分析"""
    # 移除電話號碼
    content = re.sub(r'\b\d{4}-\d{6}\b', '[電話]', content)
    # 移除身分證號
    content = re.sub(r'\b[A-Z]\d{9}\b', '[身分證]', content)
    # 移除信用卡號
    content = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[信用卡]', content)
    return content

# 權限檢查
async def verify_analysis_permission(session_id: str, user_id: str) -> bool:
    """確認用戶有權限分析該會談"""
    session = await get_session_by_id(session_id)
    return session.user_id == user_id
```

### 費用控制
```python
# AI 使用量控制
class AIUsageTracker:
    async def check_usage_limit(self, user_id: str) -> bool:
        """檢查用戶 AI 分析使用量"""
        monthly_usage = await get_monthly_ai_usage(user_id)
        user_plan = await get_user_plan(user_id)
        
        limits = {
            "free": 5,      # 免費版每月 5 次
            "student": 10,   # 學生版每月 10 次  
            "pro": 50,      # 專業版每月 50 次
        }
        
        return monthly_usage < limits.get(user_plan, 0)
```

---

## 📊 性能優化

### 快取策略
```python
# 結果快取
from functools import lru_cache
from typing import Optional

class AIAnalysisService:
    def __init__(self):
        self.result_cache = {}
        
    async def generate_summary_cached(
        self, 
        content: str, 
        language: str = "zh-TW"
    ) -> Dict[str, Any]:
        """帶快取的摘要生成"""
        cache_key = f"summary:{hash(content)}:{language}"
        
        if cache_key in self.result_cache:
            return self.result_cache[cache_key]
            
        result = await self.generate_summary(content, language)
        self.result_cache[cache_key] = result
        
        return result
```

### 非同步處理
```python
# 背景任務處理
from celery import Celery

@celery.task
def generate_analysis_background(session_id: str, analysis_type: str):
    """背景生成分析結果"""
    # 長時間分析任務可以在背景執行
    # 完成後通過 WebSocket 或輪詢通知前端
    pass
```

---

## 🧪 測試策略

### 單元測試
```python
# tests/unit/services/test_ai_analysis.py
import pytest
from unittest.mock import AsyncMock, patch
from coaching_assistant.services.ai_analysis import AIAnalysisService

class TestAIAnalysisService:
    @pytest.fixture
    def ai_service(self):
        return AIAnalysisService()
    
    @pytest.mark.asyncio
    async def test_generate_summary(self, ai_service):
        """測試摘要生成功能"""
        content = "教練: 你今天過得如何？\n客戶: 很好，謝謝。"
        
        with patch.object(ai_service.lemur_service, 'process') as mock_process:
            mock_process.return_value = {"summary": "test summary"}
            
            result = await ai_service.generate_summary(content)
            
            assert "summary" in result
            assert "processing_time" in result
            mock_process.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_feedback(self, ai_service):
        """測試回饋生成功能"""
        content = "教練: 你今天過得如何？\n客戶: 很好，謝謝。"
        
        result = await ai_service.generate_feedback(content)
        
        assert "feedback" in result
        assert "processing_time" in result
```

### 整合測試
```python
# tests/integration/api/test_ai_analysis.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_summary_api_endpoint(client: AsyncClient, auth_headers):
    """測試摘要 API 端點"""
    payload = {
        "session_id": "test-session-id",
        "content": "測試逐字稿內容",
        "language": "zh-TW"
    }
    
    response = await client.post(
        "/ai-analysis/summary",
        json=payload,
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "processing_time" in data
```

---

## 🚀 部署配置

### 環境變數
```bash
# .env
AI_ANALYSIS_ENABLED=true
AI_ANALYSIS_TIMEOUT=30
LEMUR_API_KEY=your_assemblyai_api_key
OPENAI_API_KEY=your_openai_api_key_optional
```

### Docker 配置
```dockerfile
# Dockerfile 更新
# 確保 AI 分析相關依賴已安裝
RUN pip install openai assemblyai
```

### 監控設置
```python
# 分析性能監控
import time
from prometheus_client import Counter, Histogram

ai_analysis_requests = Counter('ai_analysis_requests_total', 'Total AI analysis requests', ['type', 'status'])
ai_analysis_duration = Histogram('ai_analysis_duration_seconds', 'AI analysis duration', ['type'])

async def generate_summary_with_metrics(self, content: str, language: str = "zh-TW"):
    start_time = time.time()
    
    try:
        result = await self.generate_summary(content, language)
        ai_analysis_requests.labels(type='summary', status='success').inc()
        return result
    except Exception as e:
        ai_analysis_requests.labels(type='summary', status='error').inc()
        raise
    finally:
        duration = time.time() - start_time
        ai_analysis_duration.labels(type='summary').observe(duration)
```

---

## 📋 交付檢查清單

### 前端開發
- [ ] AI 分析 Tab 組件完成
- [ ] 摘要生成器組件完成
- [ ] 回饋生成器組件完成
- [ ] 載入和錯誤狀態處理
- [ ] 響應式設計適配
- [ ] i18n 翻譯完整

### 後端開發  
- [ ] API 端點實作完成
- [ ] LLM 服務層整合
- [ ] Prompt 設計和優化
- [ ] 資料庫表建立
- [ ] 權限和安全檢查
- [ ] 錯誤處理和降級機制

### 測試與品質
- [ ] 單元測試覆蓋率 ≥ 90%
- [ ] 整合測試完成
- [ ] 性能測試通過
- [ ] 安全測試完成
- [ ] 用戶驗收測試

### 部署與監控
- [ ] 環境配置完成
- [ ] 監控指標設置
- [ ] 日誌記錄完整
- [ ] 備份和恢復機制
- [ ] 文檔更新完成

---

*此規格文檔將隨開發進度持續更新，確保實作符合設計要求。*