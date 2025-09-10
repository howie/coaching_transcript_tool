# UI 改善技術規格

## 📋 前端 UI 改善詳細技術規格

此文檔包含項目 1-6 和項目 8 的詳細技術實施規格，提供開發人員完整的實作指南。

---

## 🎯 項目 1: 移除逐字稿 tab 的 beta 字樣

### 技術分析

**影響範圍**:
- Tab 組件標題顯示
- i18n 翻譯檔案
- 可能的 CSS 樣式

**實施步驟**:

#### 1.1 識別相關檔案
```bash
# 搜尋包含 "beta" 字樣的檔案
grep -r "beta" apps/web/components/
grep -r "beta" apps/web/lib/i18n/
grep -r "Beta" apps/web/
```

#### 1.2 預期檔案位置
```
apps/web/components/transcript/
├── TranscriptTab.tsx
├── TranscriptView.tsx
└── TranscriptHeader.tsx

apps/web/lib/i18n/translations/
├── sessions.ts
├── common.ts
└── nav.ts
```

#### 1.3 程式碼修改範例
```typescript
// 修改前
<Tab.List>
  <Tab>逐字稿 (Beta)</Tab>
  <Tab>分析結果</Tab>
</Tab.List>

// 修改後
<Tab.List>
  <Tab>逐字稿</Tab>
  <Tab>分析結果</Tab>
</Tab.List>
```

#### 1.4 i18n 翻譯更新
```typescript
// apps/web/lib/i18n/translations/sessions.ts
export const sessionsTranslations = {
  zh: {
    // 修改前
    'sessions.transcriptTab': '逐字稿 (Beta)',
    // 修改後
    'sessions.transcriptTab': '逐字稿',
  },
  en: {
    // 修改前
    'sessions.transcriptTab': 'Transcript (Beta)',
    // 修改後
    'sessions.transcriptTab': 'Transcript',
  }
}
```

### 驗收測試
```bash
# 檢查是否還有 beta 相關文字
npm run build
npm run test
grep -r -i "beta" apps/web/components/transcript/
```

**工作量**: 0.5 人天  
**風險等級**: 低

---

## 🔍 項目 2: 移除逐字稿信心度顯示

### 技術分析

**背景**: 語音轉文字服務通常會提供信心度分數 (confidence score)，表示轉錄準確性的信心程度。

**影響範圍**:
- 逐字稿顯示組件
- 資料模型介面定義
- 樣式檔案

#### 2.1 資料結構分析
```typescript
// 現有的 transcript segment 結構
interface TranscriptSegment {
  id: string;
  speaker: 'coach' | 'client';
  text: string;
  start_time: number;
  end_time: number;
  confidence?: number; // 0.0 - 1.0
}
```

#### 2.2 識別顯示組件
```bash
# 搜尋包含 confidence 相關的組件
grep -r "confidence" apps/web/components/
grep -r "信心度" apps/web/
grep -r "準確度" apps/web/
```

#### 2.3 預期修改檔案
```
apps/web/components/transcript/
├── TranscriptSegment.tsx      # 主要修改
├── TranscriptDisplay.tsx      # 可能需要修改
└── SegmentConfidence.tsx      # 可能需要移除

apps/web/types/
└── transcript.ts              # 保留後端資料結構
```

#### 2.4 程式碼修改範例
```typescript
// 修改前: TranscriptSegment.tsx
const TranscriptSegment = ({ segment }: { segment: TranscriptSegment }) => {
  return (
    <div className="transcript-segment">
      <div className="speaker">{segment.speaker}</div>
      <div className="text">{segment.text}</div>
      {segment.confidence && (
        <div className="confidence">
          信心度: {(segment.confidence * 100).toFixed(1)}%
        </div>
      )}
    </div>
  );
};

// 修改後: TranscriptSegment.tsx
const TranscriptSegment = ({ segment }: { segment: TranscriptSegment }) => {
  return (
    <div className="transcript-segment">
      <div className="speaker">{segment.speaker}</div>
      <div className="text">{segment.text}</div>
      {/* 移除信心度顯示 */}
    </div>
  );
};
```

#### 2.5 樣式調整
```css
/* 移除或註解相關 CSS */
.transcript-segment .confidence {
  /* display: none; */
  /* 或直接刪除此樣式 */
}
```

### 注意事項
- **保留後端資料**: 信心度資料仍應保留在 API 回應中，用於內部分析
- **向下相容**: 確保移除顯示不會破壞現有功能
- **測試覆蓋**: 確認移除後不影響其他組件

**工作量**: 1 人天  
**風險等級**: 低

---

## ✏️ 項目 3: 編輯角色擴展為編輯逐字稿

### 技術分析

**功能擴展**:
- 現有: 僅能編輯說話者角色 (coach/client)
- 新增: 可編輯對話內容文字
- 新增: inline 編輯體驗

#### 3.1 架構設計

**前端架構**:
```
TranscriptEditor (容器組件)
├── EditableSegment (編輯單元)
│   ├── SpeakerSelector (角色選擇)
│   ├── ContentEditor (內容編輯)
│   └── SegmentActions (操作按鈕)
├── EditHistory (編輯歷史)
└── SaveManager (保存管理)
```

**狀態管理**:
```typescript
interface EditState {
  originalSegments: TranscriptSegment[];
  editedSegments: TranscriptSegment[];
  unsavedChanges: boolean;
  editingSegmentId: string | null;
}
```

#### 3.2 組件實作規格

**EditableSegment 組件**:
```typescript
interface EditableSegmentProps {
  segment: TranscriptSegment;
  isEditing: boolean;
  onEdit: (segmentId: string) => void;
  onSave: (segment: TranscriptSegment) => void;
  onCancel: () => void;
}

const EditableSegment: React.FC<EditableSegmentProps> = ({
  segment,
  isEditing,
  onEdit,
  onSave,
  onCancel
}) => {
  const [localText, setLocalText] = useState(segment.text);
  const [localSpeaker, setLocalSpeaker] = useState(segment.speaker);

  if (isEditing) {
    return (
      <div className="editable-segment editing">
        <SpeakerSelector 
          value={localSpeaker}
          onChange={setLocalSpeaker}
        />
        <ContentEditor
          value={localText}
          onChange={setLocalText}
          onKeyDown={handleKeyDown} // Enter to save, Esc to cancel
        />
        <SegmentActions
          onSave={() => onSave({ ...segment, text: localText, speaker: localSpeaker })}
          onCancel={onCancel}
        />
      </div>
    );
  }

  return (
    <div className="editable-segment" onClick={() => onEdit(segment.id)}>
      <div className="speaker">{localSpeaker}</div>
      <div className="text">{localText}</div>
      <div className="edit-hint">點擊編輯</div>
    </div>
  );
};
```

#### 3.3 API 設計

**更新 API 端點**:
```
PATCH /sessions/{session_id}/transcript
Content-Type: application/json

{
  "segments": [
    {
      "id": "segment_1",
      "speaker": "coach",
      "text": "更新後的對話內容",
      "start_time": 1.5,
      "end_time": 5.2
    }
  ]
}

Response: 200 OK
{
  "success": true,
  "updated_segments": 1,
  "message": "逐字稿更新成功"
}
```

#### 3.4 後端實作需求
```python
# src/coaching_assistant/api/v1/sessions.py
@router.patch("/{session_id}/transcript")
async def update_transcript_segments(
    session_id: str,
    segments_update: TranscriptSegmentsUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 驗證權限
    session = await get_user_session(db, session_id, current_user.id)
    
    # 更新 segments
    for segment_data in segments_update.segments:
        await update_transcript_segment(db, segment_data)
    
    # 記錄編輯歷史
    await create_edit_history_entry(db, session_id, current_user.id, segments_update)
    
    return {"success": True, "updated_segments": len(segments_update.segments)}
```

#### 3.5 資料庫考量
```sql
-- 可能需要新增編輯歷史表
CREATE TABLE transcript_edit_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES session(id),
    user_id UUID REFERENCES "user"(id),
    original_text TEXT NOT NULL,
    edited_text TEXT NOT NULL,
    original_speaker VARCHAR(50),
    edited_speaker VARCHAR(50),
    segment_id VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### 用戶體驗設計

#### 3.6 交互設計
1. **進入編輯模式**: 點擊任意 segment
2. **編輯內容**: inline 文字編輯器
3. **角色切換**: 下拉選單或切換按鈕
4. **保存方式**: Enter 鍵 / 保存按鈕
5. **取消編輯**: Esc 鍵 / 取消按鈕
6. **自動保存**: 可選功能，離開編輯時提示

#### 3.7 錯誤處理
```typescript
const handleSaveError = (error: ApiError) => {
  switch (error.code) {
    case 'SEGMENT_NOT_FOUND':
      toast.error('段落不存在，請重新整理頁面');
      break;
    case 'PERMISSION_DENIED':
      toast.error('沒有編輯權限');
      break;
    case 'VALIDATION_ERROR':
      toast.error('內容格式不正確');
      break;
    default:
      toast.error('保存失敗，請稍後重試');
  }
};
```

**工作量**: 3-4 人天  
**風險等級**: 中

---

## 🧠 項目 4: AI 優化功能重新配置

### 技術分析

**目標**: 將現有的「🧠 AI 逐字稿優化 (Dev Only)」功能移至獨立 tab

#### 4.1 現有結構分析
```bash
# 查找現有 AI 優化功能位置
grep -r "AI.*優化" apps/web/
grep -r "lemur" apps/web/
grep -r "optimization" apps/web/
```

#### 4.2 新架構設計
```
原有位置: SessionDetail > 某個 tab 內的功能
新位置: SessionDetail > AI 優化 tab

TabBar
├── 逐字稿 tab
├── 分析結果 tab  
├── AI 優化 tab (新增)
└── 其他 tabs
```

#### 4.3 組件重構
```typescript
// 新增 AI 優化 tab
const AIOptimizationTab = () => {
  return (
    <div className="ai-optimization-tab">
      <div className="optimization-header">
        <h3>🧠 AI 逐字稿優化</h3>
        <p>使用 AI 技術改善逐字稿品質</p>
      </div>
      
      <div className="optimization-tools">
        <SpeakerIdentification />
        <PunctuationOptimization />
        <ContentEnhancement />
      </div>
    </div>
  );
};

// 更新主 tab 結構
const SessionTabs = () => {
  return (
    <Tabs>
      <TabList>
        <Tab>逐字稿</Tab>
        <Tab>分析結果</Tab>
        <Tab>AI 優化</Tab>
      </TabList>
      
      <TabPanels>
        <TabPanel><TranscriptTab /></TabPanel>
        <TabPanel><AnalysisTab /></TabPanel>
        <TabPanel><AIOptimizationTab /></TabPanel>
      </TabPanels>
    </Tabs>
  );
};
```

#### 4.4 路由更新
```typescript
// 更新路由結構支援 tab 參數
/sessions/[sessionId]?tab=transcript
/sessions/[sessionId]?tab=analysis  
/sessions/[sessionId]?tab=ai-optimization
```

#### 4.5 權限控制
```typescript
// 如果是 Dev Only 功能，需要權限檢查
const AIOptimizationTab = () => {
  const { user } = useAuth();
  
  if (!user.isDeveloper) {
    return (
      <div className="permission-required">
        <p>此功能目前僅供開發人員使用</p>
      </div>
    );
  }
  
  return <AIOptimizationContent />;
};
```

**工作量**: 1-2 人天  
**風險等級**: 低

---

## 📊 項目 5: 會談概覽位置調整

### 技術分析

**變更**: 將「會談概覽」→「談話分析結果」移動到逐字稿頁面的上方

#### 5.1 現有佈局分析
```
當前佈局:
├── 分析結果 tab
│   └── 談話分析結果 (在這裡)
└── 逐字稿 tab
    └── 逐字稿內容

目標佈局:
└── 逐字稿 tab
    ├── 談話分析結果 (移動到這裡)
    └── 逐字稿內容
```

#### 5.2 組件重構
```typescript
// 修改前: 分離的 tab 結構
const AnalysisTab = () => (
  <div>
    <SessionOverview />
    <AnalysisResults />
  </div>
);

const TranscriptTab = () => (
  <div>
    <TranscriptContent />
  </div>
);

// 修改後: 整合到逐字稿 tab
const TranscriptTab = () => (
  <div className="transcript-tab">
    <div className="analysis-summary">
      <SessionOverview />
      <AnalysisResults />
    </div>
    <div className="transcript-content">
      <TranscriptContent />
    </div>
  </div>
);
```

#### 5.3 樣式調整
```css
.transcript-tab {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.analysis-summary {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 1rem;
  border-left: 4px solid #007bff;
}

.transcript-content {
  flex: 1;
}

/* 響應式設計 */
@media (max-width: 768px) {
  .analysis-summary {
    margin-bottom: 1rem;
  }
}
```

#### 5.4 資料載入優化
```typescript
// 確保分析結果和逐字稿一起載入
const useTranscriptData = (sessionId: string) => {
  const { data: session } = useQuery(['session', sessionId], 
    () => fetchSession(sessionId)
  );
  
  const { data: analysis } = useQuery(['analysis', sessionId],
    () => fetchAnalysis(sessionId),
    { enabled: !!sessionId }
  );
  
  const { data: transcript } = useQuery(['transcript', sessionId],
    () => fetchTranscript(sessionId),
    { enabled: !!sessionId }
  );
  
  return { session, analysis, transcript };
};
```

**工作量**: 1 人天  
**風險等級**: 低

---

## ⏱️ 項目 6: 修正總時長計算錯誤

### 技術分析

**問題**: 逐字稿對話紀錄的「總時長: 0:00」顯示錯誤  
**目標**: 正確計算並顯示教練時間 + 客戶時間

#### 6.1 問題診斷
```typescript
// 可能的問題原因
1. 時間計算邏輯錯誤
2. 資料格式問題 (seconds vs milliseconds)
3. Speaker 角色識別錯誤
4. 前端顯示邏輯問題
```

#### 6.2 時間計算邏輯修正
```typescript
// 正確的時間計算實作
interface TranscriptSegment {
  id: string;
  speaker: 'coach' | 'client';
  start_time: number; // seconds
  end_time: number;   // seconds
  text: string;
}

const calculateSpeakingTime = (segments: TranscriptSegment[]) => {
  const timeStats = {
    coach_time: 0,
    client_time: 0,
    total_time: 0
  };
  
  segments.forEach(segment => {
    const duration = segment.end_time - segment.start_time;
    
    if (segment.speaker === 'coach') {
      timeStats.coach_time += duration;
    } else if (segment.speaker === 'client') {
      timeStats.client_time += duration;
    }
  });
  
  timeStats.total_time = timeStats.coach_time + timeStats.client_time;
  
  return timeStats;
};
```

#### 6.3 時間格式化函數
```typescript
const formatDuration = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  } else {
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  }
};

// 使用範例
const timeStats = calculateSpeakingTime(segments);
console.log(`總時長: ${formatDuration(timeStats.total_time)}`);
console.log(`教練時間: ${formatDuration(timeStats.coach_time)}`);
console.log(`客戶時間: ${formatDuration(timeStats.client_time)}`);
```

#### 6.4 UI 顯示組件
```typescript
const TranscriptStats = ({ segments }: { segments: TranscriptSegment[] }) => {
  const timeStats = useMemo(() => calculateSpeakingTime(segments), [segments]);
  
  return (
    <div className="transcript-stats">
      <div className="stat-item">
        <label>總時長:</label>
        <span>{formatDuration(timeStats.total_time)}</span>
      </div>
      <div className="stat-item">
        <label>教練時間:</label>
        <span>{formatDuration(timeStats.coach_time)}</span>
      </div>
      <div className="stat-item">
        <label>客戶時間:</label>
        <span>{formatDuration(timeStats.client_time)}</span>
      </div>
      <div className="stat-item">
        <label>對話段數:</label>
        <span>{segments.length}</span>
      </div>
    </div>
  );
};
```

#### 6.5 後端驗證
```python
# 確保後端也有正確的時間計算
def calculate_speaking_time(segments: List[TranscriptSegment]) -> Dict[str, float]:
    coach_time = 0.0
    client_time = 0.0
    
    for segment in segments:
        duration = segment.end_time - segment.start_time
        
        if segment.speaker == "coach":
            coach_time += duration
        elif segment.speaker == "client":
            client_time += duration
    
    return {
        "coach_time": coach_time,
        "client_time": client_time,
        "total_time": coach_time + client_time,
        "segment_count": len(segments)
    }
```

#### 6.6 測試案例
```typescript
describe('時間計算功能', () => {
  test('正確計算總時長', () => {
    const segments: TranscriptSegment[] = [
      { id: '1', speaker: 'coach', start_time: 0, end_time: 10, text: '...' },
      { id: '2', speaker: 'client', start_time: 10, end_time: 25, text: '...' },
      { id: '3', speaker: 'coach', start_time: 25, end_time: 30, text: '...' }
    ];
    
    const stats = calculateSpeakingTime(segments);
    expect(stats.coach_time).toBe(15); // 10 + 5
    expect(stats.client_time).toBe(15); // 15
    expect(stats.total_time).toBe(30);
  });
  
  test('時間格式化正確', () => {
    expect(formatDuration(90)).toBe('1:30');
    expect(formatDuration(3661)).toBe('1:01:01');
    expect(formatDuration(0)).toBe('0:00');
  });
});
```

**工作量**: 1-2 人天  
**風險等級**: 低

---

## 🧭 項目 8: 移除 dashboard 左側選單項目

### 技術分析

**移除項目**:
- ICF 分析
- 你的 AI 督導

#### 8.1 檔案位置識別
```bash
# 查找側邊欄組件
find apps/web -name "*sidebar*" -type f
find apps/web -name "*nav*" -type f
grep -r "ICF.*分析" apps/web/
grep -r "AI.*督導" apps/web/
```

#### 8.2 預期檔案
```
apps/web/components/layout/
├── DashboardSidebar.tsx    # 主要修改
├── Navigation.tsx          # 可能需要修改
└── MenuItems.tsx           # 可能需要修改

apps/web/lib/i18n/translations/
├── nav.ts                  # 翻譯更新
└── menu.ts                 # 可能需要更新
```

#### 8.3 選單項目移除
```typescript
// 修改前
const menuItems = [
  { href: '/dashboard', label: '儀表板', icon: Dashboard },
  { href: '/sessions', label: '會談記錄', icon: Sessions },
  { href: '/clients', label: '客戶管理', icon: Clients },
  { href: '/icf-analysis', label: 'ICF 分析', icon: Analysis },     // 移除
  { href: '/ai-supervisor', label: '你的 AI 督導', icon: AI },      // 移除
  { href: '/settings', label: '設定', icon: Settings },
];

// 修改後
const menuItems = [
  { href: '/dashboard', label: '儀表板', icon: Dashboard },
  { href: '/sessions', label: '會談記錄', icon: Sessions },
  { href: '/clients', label: '客戶管理', icon: Clients },
  { href: '/settings', label: '設定', icon: Settings },
];
```

#### 8.4 路由清理
```typescript
// 移除相關路由配置
// pages/icf-analysis.tsx - 刪除或重定向
// pages/ai-supervisor.tsx - 刪除或重定向

// 如果需要重定向
// next.config.js
module.exports = {
  async redirects() {
    return [
      {
        source: '/icf-analysis',
        destination: '/dashboard',
        permanent: true,
      },
      {
        source: '/ai-supervisor',
        destination: '/dashboard',
        permanent: true,
      },
    ];
  },
};
```

#### 8.5 清理未使用檔案
```bash
# 移除相關頁面檔案（如果不再需要）
rm apps/web/app/icf-analysis/page.tsx
rm apps/web/app/ai-supervisor/page.tsx

# 移除相關組件（如果不再需要）
rm -rf apps/web/components/icf-analysis/
rm -rf apps/web/components/ai-supervisor/
```

**工作量**: 0.5-1 人天  
**風險等級**: 低

---

## 🧪 測試策略

### 單元測試
```typescript
// 針對各個修改的組件
describe('UI 改善測試', () => {
  test('移除 beta 字樣', () => {
    render(<TranscriptTab />);
    expect(screen.queryByText(/beta/i)).toBeNull();
  });
  
  test('不顯示信心度', () => {
    const segments = [{ confidence: 0.95, text: 'test' }];
    render(<TranscriptDisplay segments={segments} />);
    expect(screen.queryByText(/信心度/)).toBeNull();
  });
  
  test('時間計算正確', () => {
    const segments = mockSegments;
    const stats = calculateSpeakingTime(segments);
    expect(stats.total_time).toBeGreaterThan(0);
  });
});
```

### 整合測試
```typescript
// 端到端測試
describe('逐字稿頁面整合測試', () => {
  test('編輯功能完整流程', () => {
    // 1. 載入逐字稿
    // 2. 點擊編輯
    // 3. 修改內容
    // 4. 保存
    // 5. 驗證更新
  });
});
```

### 視覺回歸測試
```bash
# 使用 Chromatic 或類似工具
npm run chromatic
```

---

## 📋 部署檢查清單

### 部署前確認
- [ ] 所有單元測試通過
- [ ] 整合測試通過
- [ ] 視覺測試通過
- [ ] 無 console 錯誤
- [ ] 響應式設計正常
- [ ] i18n 翻譯完整
- [ ] 性能指標正常

### 部署後驗證
- [ ] 所有修改功能正常運作
- [ ] 無 404 錯誤
- [ ] 時間計算正確
- [ ] 編輯功能穩定
- [ ] 用戶回饋收集

---

*此技術規格將隨開發進度持續更新，確保實作與設計保持一致。*