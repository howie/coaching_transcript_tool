# AI Coach System - LLM Integration Architecture

## Overview

This document outlines the technical architecture for integrating multiple LLM providers into the coaching assistant platform. The system supports the [AI Coach user stories](../user-stories.md) by providing three tiers of AI-powered coaching analysis, from simple transcript correction to complex insight generation.

**Supporting User Stories**: All Epic 1-4 features depend on this LLM integration foundation.

**Related Documentation**: 
- [User Stories & Requirements](../user-stories.md)
- [Implementation Roadmap](../implementation-roadmap.md)

## Architecture Goals

- **Provider Flexibility**: Switch between LLM providers based on performance and cost
- **Tiered Complexity**: Three levels of AI assistance from simple to advanced
- **Cost Optimization**: Route requests to the most cost-effective provider for each task
- **Quality Assurance**: Maintain consistent quality across different providers

## System Architecture

### High-Level Architecture Diagram

```mermaid
graph TD
    A[原始音檔/逐字稿] --> B{前處理模組};
    B --> C[LLM 抽象層 (LLM Abstraction Layer)];
    C --> D1[LLM Provider 1: OpenAI];
    C --> D2[LLM Provider 2: Anthropic];
    C --> D3[LLM Provider 3: Google Gemini];
    C --> D4[LLM Provider 4: AssemblyAI LeMUR];

    subgraph "AI 分析核心功能"
        E1[層級 1: 逐字稿修正];
        E2[層級 2: ICF 核心能力分析];
        E3[層級 3: 教練洞察生成];
    end

    C -- 路由 --> E1;
    C -- 路由 --> E2;
    C -- 路由 --> E3;

    E1 --> F[分析結果];
    E2 --> F;
    E3 --> F;

    F --> G[後處理 & 儲存];
    G --> H[API / 使用者介面];
```

### Component Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │  LLM Router     │
│  Coaching UI    │───▶│   FastAPI       │───▶│   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                                       ▼
                        ┌─────────────────────────────────────────────────┐
                        │                LLM Providers                   │
                        ├─────────────┬─────────────┬─────────────────────┤
                        │  OpenAI     │  Anthropic  │  Google Gemini     │
                        │  GPT-4      │  Claude     │  Gemini Pro        │
                        ├─────────────┼─────────────┼─────────────────────┤
                        │ AssemblyAI  │ Azure       │  Local Models      │
                        │ LeMUR       │ OpenAI      │  Ollama/LM Studio  │
                        └─────────────┴─────────────┴─────────────────────┘
```

### LLM 抽象層 (LLM Abstraction Layer)

這是系統的核心組件，目標是將不同 LLM 的 API 封裝成統一的介面：

- **統一介面**: 定義標準化的 `generate`, `analyze`, `correct` 等方法
- **配置驅動**: 透過配置文件指定特定任務要使用的 LLM
- **動態路由**: 根據任務複雜度、成本預算動態選擇最適合的模型
- **錯誤處理**: 統一處理 API 錯誤、超時和速率限制

## Three-Tier AI Services

### Tier 1: Transcript Correction (Simple)
**Purpose**: Fix errors, punctuation, and speaker classification.  
**Detailed Workflow**: [Tier 1 Workflow: Transcript Correction](./workflow_transcript_correction.md)

**Features**:
- Correct transcription errors and typos
- Add proper punctuation and formatting
- Fix speaker diarization mistakes
- Standardize terminology (coach vs. client)

**Recommended Providers**:
1. **AssemblyAI LeMUR** (Primary)
2. **GPT-3.5 Turbo** (Fallback)
3. **Claude Haiku** (Alternative)

### Tier 2: ICF Competency Analysis (Medium)
**Purpose**: Analyze coaching skills against ICF standards.  
**Detailed Workflow**: [Tier 2 Workflow: ICF Competency Analysis](./workflow_icf_analysis.md)

**Features**:
- Map conversation to ICF Core Competencies
- Identify PCC markers and ACC requirements
- Track skill progression over time
- Generate competency scores and feedback

**Recommended Providers**:
1. **Claude 3.5 Sonnet** (Primary)
2. **GPT-4o** (Secondary)
3. **Gemini 1.5 Pro** (Alternative)

### Tier 3: Coaching Insight Generation (Complex)
**Purpose**: Generate deep insights and improvement recommendations.  
**Detailed Workflow**: [Tier 3 Workflow: Coaching Insight Generation](./workflow_insight_generation.md)

**Features**:
- Advanced conversation pattern analysis
- Client engagement and breakthrough identification
- Coach blind spot detection
- Personalized coaching style analysis

**Recommended Providers**:
1. **Gemini 1.5 Pro** (Primary for long context)
2. **Claude 3 Opus** (Primary for deep reasoning)
3. **GPT-4o** (Secondary)

## LLM Provider Analysis

### Cost Comparison (per 1M tokens)

**價格基準**: 以 2025 年 Q3 的公開資訊為準，1k tokens 約等於 750 個英文單詞或 500 個漢字。

| Provider | Model | Input Cost | Output Cost | Best Use Case | 備註 |
|----------|-------|------------|-------------|---------------|------|
| **OpenAI** | GPT-4o | $5.00 | $15.00 | 業界標竿，速度快，多模態 | 所有層級任務，高準確度 |
| OpenAI | GPT-4 Turbo | $10.00 | $30.00 | 超長上下文，性能強大 | 長會談逐字稿處理 |
| OpenAI | GPT-3.5 Turbo | $0.50 | $1.50 | 成本極低，速度快 | **層級1逐字稿修正**首選 |
| **Anthropic** | Claude 3.5 Sonnet | $3.00 | $15.00 | 最具成本效益的旗艦模型 | **層級2 ICF分析**首選 |
| Anthropic | Claude 3 Opus | $15.00 | $75.00 | 頂尖推理能力 | 最複雜分析任務 |
| Anthropic | Claude 3 Haiku | $0.25 | $1.25 | 最快最便宜 | **層級1逐字稿修正**備選 |
| **Google** | Gemini 1.5 Pro | $3.50 (128k+) / $7.00 (<128k) | $10.50 (128k+) / $21.00 (<128k) | 超長上下文 (1M tokens) | **層級3洞察生成**首選 |
| Google | Gemini 1.5 Flash | $0.35 (128k+) / $0.70 (<128k) | $1.05 (128k+) / $2.10 (<128k) | 速度優化，成本低廉 | 層級1修正和快速預覽 |
| **AssemblyAI** | LeMUR | 依基礎模型計費 | - | 專為對話數據設計 | **層級1逐字稿修正**專用 |

### 任務特定模型選型建議

| 任務層級 | 主要目標 | 推薦首選模型 | 備選/成本導向模型 | 考量點 |
|----------|----------|-------------|------------------|-------|
| **層級1: 逐字稿修正** | 準確、快速、低成本 | **AssemblyAI LeMUR** | Claude 3 Haiku, GPT-3.5 Turbo | LeMUR專為此場景設計，Haiku或GPT-3.5具極佳成本效益 |
| **層級2: ICF分析** | 遵循複雜指令、結構化輸出 | **Claude 3.5 Sonnet** | GPT-4o | Sonnet在成本和性能上取得絕佳平衡 |
| **層級3: 洞察生成** | 深度推理、全局理解 | **Gemini 1.5 Pro** | Claude 3.5 Sonnet, GPT-4o | Gemini長上下文能力在此有巨大優勢 |

### Provider Strengths

#### OpenAI
**Advantages**:
- Mature API and ecosystem
- Consistent performance
- Good documentation
- Function calling capabilities

**Disadvantages**:
- Higher cost for advanced models
- Rate limiting concerns
- Data privacy considerations

#### Anthropic (Claude)
**Advantages**:
- Excellent reasoning capabilities
- Strong safety and ethical alignment
- Large context windows (200K tokens)
- Superior for complex analysis

**Disadvantages**:
- Higher cost for Opus
- Limited availability in some regions
- Newer ecosystem

#### Google (Gemini)
**Advantages**:
- Competitive pricing
- Multimodal capabilities
- Good performance/cost ratio
- Enterprise integrations

**Disadvantages**:
- Newer model family
- Less proven in production
- API stability concerns

#### AssemblyAI LeMUR
**Advantages**:
- Specialized for audio/transcript processing
- Built-in understanding of speech patterns
- Cost-effective for transcript tasks
- Direct integration with transcription

**Disadvantages**:
- Limited to audio/transcript domain
- Less flexible than general LLMs
- Smaller context windows

## Implementation Plan

### Phase 1: Basic Infrastructure
1. **LLM Router Service**
   - Abstract provider interface
   - Request routing logic
   - Cost tracking and monitoring
   - Fallback mechanisms

2. **Provider Integrations**
   - OpenAI API client
   - Anthropic API client
   - Google Gemini client
   - AssemblyAI LeMUR integration

### Phase 2: Tier 1 Implementation
1. **Transcript Correction Service**
   - Error detection and correction
   - Punctuation and formatting
   - Speaker classification fixes
   - Quality validation

### Phase 3: Tier 2 Implementation
1. **ICF Competency Analysis**
   - Competency mapping algorithms
   - Scoring mechanisms
   - Progress tracking database
   - Reporting dashboard

### Phase 4: Tier 3 Implementation
1. **Advanced Insight Generation**
   - Pattern recognition algorithms
   - Personalized recommendations
   - Cross-session analysis
   - Predictive insights

### Phase 5: Optimization
1. **Performance Tuning**
   - Cost optimization algorithms
   - Caching strategies
   - Batch processing
   - Quality monitoring

## Database Schema Extensions

```sql
-- LLM Provider configurations
CREATE TABLE llm_providers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    api_endpoint TEXT,
    model_name VARCHAR(100),
    cost_per_input_token DECIMAL(10,6),
    cost_per_output_token DECIMAL(10,6),
    max_tokens INTEGER,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Analysis requests and results
CREATE TABLE ai_analyses (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    analysis_type VARCHAR(20) NOT NULL, -- 'correction', 'competency', 'insight'
    provider_id INTEGER REFERENCES llm_providers(id),
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,4),
    processing_time_ms INTEGER,
    status VARCHAR(20) DEFAULT 'pending',
    result_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- ICF Competency scores
CREATE TABLE competency_scores (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES ai_analyses(id),
    competency_name VARCHAR(100) NOT NULL,
    score DECIMAL(3,2), -- 0.00 to 10.00
    evidence TEXT,
    recommendations TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Coach insights and recommendations
CREATE TABLE coaching_insights (
    id SERIAL PRIMARY KEY,
    analysis_id INTEGER REFERENCES ai_analyses(id),
    insight_category VARCHAR(50),
    insight_text TEXT,
    recommendation TEXT,
    priority INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API Design

### Tier 1: Transcript Correction
```http
POST /api/v1/ai/correct-transcript
Content-Type: application/json

{
    "session_id": "12345",
    "provider": "auto", // or specific provider
    "options": {
        "fix_grammar": true,
        "fix_punctuation": true,
        "fix_speakers": true
    }
}
```

### Tier 2: ICF Analysis
```http
POST /api/v1/ai/analyze-competencies
Content-Type: application/json

{
    "session_id": "12345",
    "provider": "claude-opus",
    "competencies": ["all"], // or specific competencies
    "include_evidence": true
}
```

### Tier 3: Generate Insights
```http
POST /api/v1/ai/generate-insights
Content-Type: application/json

{
    "session_id": "12345",
    "provider": "claude-opus",
    "analysis_depth": "comprehensive",
    "include_comparisons": true,
    "session_history_months": 6
}
```

## Quality Assurance

### Validation Metrics
1. **Accuracy**: Compare AI corrections with human validation
2. **Consistency**: Ensure similar results across providers
3. **Relevance**: Validate ICF competency mappings
4. **Usefulness**: Track coach adoption of recommendations

### A/B Testing Framework
- Test different providers for same tasks
- Measure coach satisfaction and engagement
- Track performance improvements over time
- Cost-effectiveness analysis

## Security and Privacy

### Data Protection
- Encrypt all AI processing requests
- Implement data retention policies
- Ensure GDPR compliance
- Audit AI provider data handling

### Access Control
- Role-based access to AI features
- Coach consent for AI analysis
- Client anonymization options
- Audit logs for AI usage

## Monitoring and Analytics

### Performance Metrics
- Response times per provider
- Success/failure rates
- Cost per analysis type
- User satisfaction scores

### Business Intelligence
- Most effective providers by task
- Cost optimization opportunities
- Feature adoption rates
- ROI analysis for coaches

## Future Enhancements

### Advanced Features
1. **Real-time Analysis**: Live coaching session analysis
2. **Voice Analysis**: Tone, pace, and emotion detection
3. **Predictive Coaching**: AI-suggested conversation directions
4. **Custom Models**: Fine-tuned models for specific coaching styles
5. **Multi-language Support**: Extend beyond English and Chinese

### Integration Opportunities
1. **Coaching Certification Bodies**: Direct ICF reporting
2. **LMS Integration**: Connect with coaching education platforms
3. **CRM Systems**: Integrate with coach business tools
4. **Mobile Apps**: On-the-go analysis and insights

---

*This document will be updated as the AI Coach system evolves and new providers or capabilities are added.*
