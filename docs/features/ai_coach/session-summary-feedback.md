# AI 分析功能：會談摘要與回饋

## 📋 概覽

**來源**: 客戶回饋項目 7 (從 `customer-feedback` 移轉)
**狀態**: ⏳ 待開發
**優先級**: 🟡 中
**工作量**: 8-10 人天
**預計期程**: 2025-10-04 ~ 2025-10-11

---

## 🎯 功能需求

### 需求描述
新增 AI 分析 tab，允許用戶針對逐字稿內容與 LLM 對談，初期提供兩個主要功能按鈕。

### 業務價值
- 提供 AI 驅動的分析功能，增加產品價值和競爭力
- 幫助教練快速理解會談重點和改進方向
- 提升學習輔助功能，符合新的品牌定位（非評分導向）

---

## 🎨 功能規格

### 7.1 產生會談摘要按鈕

**輸入**: 完整逐字稿內容

**輸出**: 結構化會談摘要，包含：
- 關鍵議題 (key topics)
- 進展指標 (progress indicators)
- 行動項目 (action items)

**使用情境**:
```
用戶點擊「產生會談摘要」按鈕
→ 系統發送逐字稿至 LLM
→ LLM 分析並生成結構化摘要
→ 顯示摘要結果於 AI 分析 tab
```

---

### 7.2 給予會談回饋按鈕

**輸入**: 完整逐字稿內容

**輸出**: 教練技巧回饋和建議

**重點原則**:
- ✅ 學習輔助導向
- ❌ 避免評分式回饋
- ✅ 提供建設性建議
- ❌ 避免「通過/未通過」評語

**回饋格式**:
- 技能提示 (skill highlights)
- 問句方向建議 (questioning approach)
- 改進機會 (improvement opportunities)
- 參考資源 (learning resources)

---

## 🏗️ 技術架構

### 前端架構
```
apps/web/app/dashboard/sessions/[id]/
└── AI 分析 Tab (新增)
    ├── AIAnalysisTab.tsx           # 主要 tab 組件
    ├── SummaryGenerator.tsx        # 摘要生成組件
    ├── FeedbackGenerator.tsx       # 回饋生成組件
    └── ChatInterface.tsx           # 對談介面 (未來擴展)
```

### 後端架構
```
src/coaching_assistant/
├── api/v1/ai_analysis.py           # API 端點
├── core/services/
│   └── ai_analysis_use_case.py     # 業務邏輯
└── infrastructure/
    └── llm/
        ├── llm_provider.py         # LLM 整合介面
        └── prompts/
            ├── summary_prompt.py   # 摘要生成 prompt
            └── feedback_prompt.py  # 回饋生成 prompt
```

---

## 🔌 API 設計

### POST /v1/ai-analysis/summary

生成會談摘要

**Request:**
```json
{
  "session_id": "uuid",
  "transcript_content": "完整逐字稿內容...",
  "language": "zh-TW"
}
```

**Response:**
```json
{
  "summary": {
    "key_topics": [
      "職涯轉換焦慮",
      "家庭與工作平衡"
    ],
    "progress_indicators": [
      "客戶已開始探索新的職涯選項",
      "建立了初步的時間管理框架"
    ],
    "action_items": [
      {
        "description": "研究目標產業的入門路徑",
        "deadline": "下次會談前"
      },
      {
        "description": "與家人討論轉職計劃",
        "deadline": "本週內"
      }
    ]
  },
  "generated_at": "2025-10-04T10:30:00Z"
}
```

---

### POST /v1/ai-analysis/feedback

生成教練技巧回饋

**Request:**
```json
{
  "session_id": "uuid",
  "transcript_content": "完整逐字稿內容...",
  "language": "zh-TW",
  "focus_areas": ["questioning", "listening", "reframing"]  // 可選
}
```

**Response:**
```json
{
  "feedback": {
    "skill_highlights": [
      "善於使用開放式問題引導客戶思考",
      "能夠適時反映客戶的情緒狀態"
    ],
    "improvement_opportunities": [
      {
        "area": "提問技巧",
        "suggestion": "可以多使用「如何」開頭的問題，協助客戶探索具體行動步驟",
        "examples": [
          "如何開始第一步？",
          "如何知道這個方法對你有效？"
        ]
      }
    ],
    "learning_resources": [
      {
        "title": "強效提問的藝術",
        "type": "article",
        "url": "https://..."
      }
    ]
  },
  "generated_at": "2025-10-04T10:31:00Z"
}
```

---

## 🤖 LLM 整合

### Provider 選擇
- **主要**: OpenAI GPT-4 (或 GPT-4 Turbo)
- **備選**: Anthropic Claude 3
- **考量因素**:
  - 繁體中文支援品質
  - API 價格
  - 回應速度
  - 上下文長度限制

### Prompt 設計原則

#### Summary Prompt
```python
SUMMARY_PROMPT_TEMPLATE = """
你是一位專業的教練會談分析助理。請分析以下教練會談逐字稿，並提供結構化摘要。

逐字稿內容：
{transcript_content}

請以 JSON 格式提供以下內容：
1. key_topics: 會談中討論的主要議題（最多5個）
2. progress_indicators: 客戶在會談中展現的進展（最多3個）
3. action_items: 客戶承諾的具體行動項目（包含描述和期限）

注意事項：
- 使用繁體中文
- 保持客觀和建設性
- 聚焦於客戶的成長和行動
"""
```

#### Feedback Prompt
```python
FEEDBACK_PROMPT_TEMPLATE = """
你是一位資深教練督導，專注於提供學習輔助和技能發展建議。請分析以下教練會談逐字稿，並提供建設性回饋。

逐字稿內容：
{transcript_content}

請以 JSON 格式提供以下內容：
1. skill_highlights: 教練展現良好的技巧（最多3個）
2. improvement_opportunities: 改進機會和具體建議（最多3個，每個包含 area, suggestion, examples）
3. learning_resources: 推薦的學習資源（最多2個）

重要原則：
- 使用繁體中文
- 學習輔助導向，非評分式回饋
- 避免「通過/未通過」、「好/不好」等評價性語言
- 提供具體、可操作的建議
- 保持鼓勵和支持的語調
"""
```

---

## ✅ 驗收標準

### 功能驗收
- [ ] AI 分析 tab 在會談詳情頁面正確顯示
- [ ] 「產生會談摘要」按鈕功能正常
- [ ] 「給予會談回饋」按鈕功能正常
- [ ] 支援中英文分析（至少支援繁體中文）
- [ ] 回應時間 < 30 秒
- [ ] 錯誤處理完善（API 失敗、timeout 等）

### 技術驗收
- [ ] API 端點符合 RESTful 規範
- [ ] 單元測試覆蓋率 ≥ 85%
- [ ] 整合測試覆蓋主要流程
- [ ] LLM 成本監控和限制機制
- [ ] 日誌記錄完整（包含 token 使用量）

### UX 驗收
- [ ] 載入狀態清晰（loading indicator）
- [ ] 結果顯示格式化且易讀
- [ ] 可複製或匯出結果
- [ ] 回饋語氣符合「學習輔助」定位
- [ ] 行動裝置顯示正常

---

## 📊 實施計劃

### Phase 1: 基礎架構 (2 天)
- [ ] 設計 API 端點規格
- [ ] 建立 LLM Provider 抽象層
- [ ] 實作基礎 prompt 模板
- [ ] 設置測試環境

### Phase 2: Summary 功能 (2-3 天)
- [ ] 實作摘要生成 API
- [ ] 設計 Summary prompt
- [ ] 開發前端 SummaryGenerator 組件
- [ ] 撰寫單元測試和整合測試

### Phase 3: Feedback 功能 (2-3 天)
- [ ] 實作回饋生成 API
- [ ] 設計 Feedback prompt (重點：學習輔助導向)
- [ ] 開發前端 FeedbackGenerator 組件
- [ ] 撰寫單元測試和整合測試

### Phase 4: 整合與優化 (2 天)
- [ ] 前端 AI 分析 tab 整合
- [ ] 錯誤處理和邊界案例
- [ ] 性能優化（快取、串流回應）
- [ ] 成本監控和限制
- [ ] 端到端測試

---

## ⚠️ 風險與挑戰

### 技術風險
| 風險 | 影響度 | 機率 | 緩解措施 |
|------|--------|------|----------|
| LLM API 不穩定 | 高 | 中 | 實作重試機制、fallback provider |
| 回應時間過長 | 中 | 中 | 串流回應、非同步處理、設定 timeout |
| 成本控制問題 | 高 | 中 | Token 限制、使用量監控、rate limiting |
| Prompt 品質不穩定 | 中 | 高 | A/B testing、收集用戶回饋、持續優化 |

### 產品風險
| 風險 | 影響度 | 機率 | 緩解措施 |
|------|--------|------|----------|
| 回饋語氣不符預期 | 中 | 中 | 詳細 prompt 指引、人工審核樣本 |
| 用戶隱私疑慮 | 高 | 低 | 明確隱私政策、資料加密、選擇性使用 |
| 繁中支援不佳 | 中 | 低 | 選擇繁中支援良好的 LLM、提供範例測試 |

---

## 💰 成本估算

### LLM API 成本
假設使用 GPT-4:
- 平均逐字稿長度: 3000 tokens
- 平均回應長度: 500 tokens
- 成本: ~$0.10 per request (input + output)

**月度估算** (假設 1000 個 active users, 每人 2 次/月):
- 總請求數: 2000 requests/month
- 總成本: ~$200/month

### 開發成本
- Backend 開發: 4-5 人天
- Frontend 開發: 3-4 人天
- 測試與優化: 1-2 人天
- **總計**: 8-10 人天

---

## 🔗 相關文檔

- [AI Coach 實施路線圖](./implementation-roadmap.md)
- [AI Coach 使用者故事](./user-stories.md)
- [客戶回饋改善清單](../customer-feedback/improvement-list.md)
- [客戶回饋實施時程](../customer-feedback/implementation-roadmap.md)

---

## 📝 更新紀錄

| 日期 | 版本 | 變更內容 | 作者 |
|------|------|----------|------|
| 2025-10-03 | 1.0 | 從 customer-feedback 移轉，新增詳細規格 | Claude |

---

*此文檔為客戶回饋項目 7 的詳細實施規格，移轉至 AI Coach 功能模組進行統一管理。*
