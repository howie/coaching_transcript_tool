# Claude 智能系統狀況查詢 Agent 🤖

Claude 智能助理，當您需要查詢系統最新狀況時，它會自動幫您分析和報告各種系統指標。

## 🎯 核心功能

### ✨ 智能特性
- **自然語言理解**: 支援中英文混合查詢，智能識別用戶意圖
- **多模式查詢**: 總覽、用戶、會話、性能、活動、告警六大查詢類型
- **人性化回應**: 友好的人類可讀格式，配有表情符號和結構化展示
- **即時數據**: 直接從 production 資料庫獲取最新狀況
- **智能洞察**: 基於數據自動生成分析建議和趨勢洞察

### 🔍 查詢類型

#### 1. 系統總覽 (overview)
**觸發詞**: 查詢最新狀況、系統怎麼樣、目前情況、overall
```
🎯 系統總覽
🟢 優秀 | 👥 8 用戶 | 📊 7 今日會話 | ✅ 85.7% 成功率

📊 核心指標
• 👥 用戶: 8 總計 (0 今日新增)  
• 🔄 會話: 7 今日總計 (6 已完成)
• ✅ 成功率: 85.7%
• 🔄 處理中: 1 個

💡 智能洞察
• 系統處理性能良好，成功率較高
• 目前有 1 個會話在處理，系統正常
```

#### 2. 用戶指標 (users)
**觸發詞**: 用戶情況、新增用戶、用戶增長、多少用戶
```
👥 用戶指標分析
📈 增長趨勢
• 總用戶: 8
• 本週新增: 2 (+33.3%)
• 本月新增: 8

🎯 活躍度  
• 今日活躍: 3/8 (37.5%)
• 本週活躍: 5

💼 方案分佈
• FREE: 8 (100.0%)
• PRO: 0 (0.0%)
• ENTERPRISE: 0 (0.0%)
```

#### 3. 會話狀況 (sessions)
**觸發詞**: 會話處理、轉錄狀態、處理進度、session status
```
🔄 會話處理狀況
🟢 良好 | 今日 7 個會話 | 成功率 85.7%

⚡ 最近完成
• 商業會議錄音.mp3 (12.3分鐘, 14:32)
• 客戶訪談記錄.wav (8.7分鐘, 15:15)

🔄 處理中
• 培訓會議音檔.mp3 (已處理 00:03:45)

💡 狀況分析
• 今日總會話數: 7
• 成功率: 85.7%
• 主要使用 Google STT 服務
```

#### 4. 性能指標 (performance)
**觸發詞**: 系統性能、效能、速度、響應時間、處理時間
```
⚡ 系統性能指標
🟢 優秀 | 性能分數: 92/100

📊 處理性能
• 平均處理時間: 2.3 分鐘
• 今日已處理: 6 個會話
• 總處理時長: 89.4 分鐘

🖥️ 系統性能
• 資料庫響應: 12.5ms
• 最近1小時活動: 2 個新會話
```

#### 5. 最近活動 (recent)
**觸發詞**: 最近活動、剛才發生、最新動態、近期情況
```
🕐 最近活動
🔥 活躍 | 2 新會話, 1 完成

👥 最近用戶 (24小時內)
• user@example.com (PRO, 2小時前)
• newbie@test.com (FREE, 5小時前)

🔄 最近會話 (1小時內)
• 產品討論會議 (completed, 15分鐘前)
• 客戶需求訪談 (processing, 剛才)
```

#### 6. 系統告警 (alerts)
**觸發詞**: 有問題嗎、告警、異常、錯誤、需要注意
```
⚠️ 系統告警
🟡 正常但有警告 | 健康狀況: healthy

⚠️ 警告信息
• 錯誤率略高: 14.3% (總會話: 7, 失敗: 1)

💡 建議措施
• 監控錯誤日誌
• 檢查 STT 服務狀態
• 系統整體運行良好
```

## 🚀 API 端點

### 1. 智能查詢端點
```http
POST /claude/ask
Content-Type: application/json

{
  "query": "查詢最新狀況",
  "format": "human"  // 或 "json"
}
```

**回應範例**:
```json
{
  "status": "success",
  "understood": true,
  "query_type": "overview",
  "confidence": 1.0,
  "response": "🎯 系統總覽...",
  "data": { /* 詳細結構化數據 */ }
}
```

### 2. 對話模式
```http  
POST /claude/chat
Content-Type: application/json

{
  "query": "系統現在怎麼樣？",
  "format": "human"
}
```

### 3. 快捷查詢
```http
GET /claude/quick/status     # 系統總覽
GET /claude/quick/alerts     # 告警檢查  
GET /claude/quick/users      # 用戶指標
GET /claude/quick/sessions   # 會話狀況
GET /claude/quick/performance # 性能指標
GET /claude/quick/recent     # 最近活動
```

### 4. 幫助和建議
```http
GET /claude/help        # 使用說明
GET /claude/suggestions # 建議指令
```

### 5. 系統健康檢查 (無需認證)
```http
GET /system/status/health
```

## 💬 使用範例

### 自然語言查詢
Claude 支援各種自然語言表達方式：

**系統總覽**:
- "查詢最新狀況"
- "系統現在怎麼樣？"
- "給我看看系統總體情況"
- "目前運行狀況如何？"

**問題檢查**:
- "有沒有問題？"
- "系統正常嗎？" 
- "需要注意什麼？"
- "有什麼異常嗎？"

**用戶分析**:
- "用戶情況如何？"
- "最近多少新用戶？"
- "用戶增長趨勢怎樣？"
- "活躍用戶有多少？"

**會話狀況**:
- "會話處理狀況"
- "轉錄進度如何？"
- "處理了多少會話？"
- "有會話在處理嗎？"

**性能指標**:
- "系統性能怎樣？"
- "響應時間正常嗎？"
- "處理速度如何？"
- "性能表現好嗎？"

**最近活動**:
- "最近有什麼活動？"
- "剛才發生什麼？"
- "近期有什麼動態？"
- "最新情況如何？"

### 程式化調用
```python
import httpx

async def query_system_status():
    async with httpx.AsyncClient() as client:
        # 智能查詢
        response = await client.post(
            "https://your-api.com/claude/ask",
            json={"query": "查詢最新狀況"},
            headers={"Authorization": "Bearer YOUR_TOKEN"}
        )
        
        data = response.json()
        if data["understood"]:
            print(data["response"])
        else:
            print("Claude 無法理解查詢，請嘗試其他表達方式")
```

### 前端整合範例
```javascript
// React Hook
const useClaudeQuery = () => {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState('');
  
  const askClaude = async (query) => {
    setLoading(true);
    try {
      const res = await fetch('/claude/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query, format: 'human' })
      });
      
      const data = await res.json();
      setResponse(data.response);
    } catch (error) {
      setResponse('查詢失敗，請稍後重試');
    } finally {
      setLoading(false);
    }
  };
  
  return { askClaude, loading, response };
};

// 使用組件
function SystemStatusChat() {
  const { askClaude, loading, response } = useClaudeQuery();
  const [query, setQuery] = useState('');
  
  return (
    <div className="claude-chat">
      <div className="response">
        {loading ? '🤖 Claude 正在分析...' : response}
      </div>
      
      <input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="問問 Claude 系統狀況..."
        onKeyPress={(e) => e.key === 'Enter' && askClaude(query)}
      />
      
      <div className="quick-buttons">
        <button onClick={() => askClaude('查詢最新狀況')}>
          📊 系統總覽
        </button>
        <button onClick={() => askClaude('有沒有問題？')}>
          ⚠️ 檢查告警
        </button>
        <button onClick={() => askClaude('用戶情況如何？')}>
          👥 用戶指標
        </button>
      </div>
    </div>
  );
}
```

## 🔧 技術架構

### 核心組件
```
Claude System Status Agent
├── SystemStatusAgent          # 主要狀況查詢服務
│   ├── get_current_status()   # 統一查詢入口
│   ├── _get_user_metrics()    # 用戶指標分析
│   ├── _get_session_status()  # 會話狀況分析  
│   ├── _get_performance_metrics() # 性能指標分析
│   ├── _get_recent_activity() # 最近活動分析
│   ├── _get_system_alerts()   # 系統告警檢查
│   └── format_response_for_human() # 人性化格式輸出
├── ClaudeCommandParser        # 自然語言指令解析
│   ├── parse_command()        # 指令解析和意圖識別
│   ├── _detect_query_type()   # 查詢類型檢測
│   ├── _detect_urgency()      # 緊急程度判斷
│   └── suggest_commands()     # 建議指令生成
└── API Endpoints              # RESTful API 介面
    ├── /claude/ask           # 智能查詢
    ├── /claude/chat          # 對話模式
    ├── /claude/quick/*       # 快捷查詢
    └── /system/status/*      # 直接狀況查詢
```

### 智能解析引擎
```python
# 指令模式匹配
command_patterns = {
    "overview": [
        r"查詢?最新狀況", r"系統狀況", r"目前狀況",
        r"overall|overview|總覽", r"系統怎麼樣"
    ],
    "users": [
        r"用戶.*(?:數量|統計|情況)", r"(?:新增|註冊).*用戶",
        r"用戶增長", r"多少用戶"
    ],
    "alerts": [
        r"(?:告警|警報|問題|錯誤)", r"有.*(?:問題|錯誤|異常)",
        r"系統.*(?:正常|異常)", r"有沒有問題"
    ]
    # ... 更多模式
}

# 緊急程度檢測
urgency_keywords = {
    "high": ["緊急", "立即", "馬上", "urgent", "critical"],
    "medium": ["重要", "需要", "important", "priority"],
    "low": ["看看", "檢查", "查詢", "check", "view"]
}
```

## 🎨 回應格式設計

### 人性化格式特點
1. **表情符號**: 使用直觀的 emoji 增強視覺效果
2. **結構化布局**: 清晰的標題、項目符號、分隔線
3. **數據可視化**: 百分比、分數、狀態指示器
4. **友好語言**: 避免技術術語，使用平易近人的描述
5. **行動建議**: 基於分析結果提供實用建議

### 狀態指示系統
```
🟢 優秀   - 90+ 分
🟡 良好   - 80-89 分  
🟠 一般   - 60-79 分
🔴 需要關注 - < 60 分

🔥 活躍   - 高活躍度
📊 正常   - 中等活躍度
😴 安靜   - 低活躍度
```

## 🚦 權限和安全

### 存取權限
- **基本查詢**: 需要登入用戶 (任何角色)
- **健康檢查**: 無需認證 (供監控系統使用)
- **詳細數據**: 自動過濾敏感信息

### 資料隱私
- 用戶郵箱自動截斷顯示
- 會話標題智能縮短
- 錯誤信息安全過濾
- 不暴露系統內部路徑或配置

## 📈 使用場景

### 1. 日常運營監控
```
管理員: "查詢最新狀況"
Claude: 🎯 系統總覽顯示一切正常，今日處理了15個會話...

管理員: "有什麼需要注意的嗎？"  
Claude: ⚠️ 發現1個會話處理時間較長，建議檢查...
```

### 2. 故障排查
```
技術人員: "系統有問題嗎？"
Claude: 🔴 發現問題！錯誤率達到25%，3個會話處理失敗...

技術人員: "性能怎樣？"
Claude: ⚡ 資料庫響應時間1.2秒，明顯偏慢，建議檢查...
```

### 3. 業務分析
```
產品經理: "用戶增長如何？"
Claude: 👥 本週新增12位用戶，增長率33%，PRO用戶佔比提升...

產品經理: "最近活動情況？"
Claude: 🕐 過去24小時活躍度很高，處理了28個會話...
```

### 4. 定期報告
```
# 自動化腳本
curl -X POST /claude/ask \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "系統總體狀況如何？"}' \
  | jq -r '.response' \
  | mail -s "每日系統狀況" admin@company.com
```

## 🔮 未來增強

### 計畫功能
- [ ] **趨勢分析**: 歷史數據對比和趨勢預測
- [ ] **智能告警**: 主動發現異常並推送通知
- [ ] **對話記憶**: 記住上下文，支援連續對話
- [ ] **多語言支援**: 英文、日文等多語言查詢
- [ ] **語音交互**: 支援語音查詢和回應
- [ ] **自訂報表**: 用戶自定義查詢和報表格式
- [ ] **預測分析**: 基於 AI 的系統負載和問題預測

### 技術優化
- [ ] **快取機制**: 熱點查詢結果快取
- [ ] **並發優化**: 支援高並發查詢請求
- [ ] **分散式部署**: 多實例負載均衡
- [ ] **指標儲存**: 時序資料庫整合
- [ ] **實時更新**: WebSocket 推送即時狀況

---

**建立日期**: 2025-01-24  
**版本**: 1.0.0  
**維護者**: Claude System Team

🤖 **Claude 說**: 隨時問我系統狀況，我會用最友好的方式為您分析和報告！