# Session ID 對應關係說明

## 問題描述
在實作 LeMUR 優化功能時發現了 Session ID 混淆問題，導致 API 404 錯誤。

## 兩種不同的 Session ID

### 1. 🎯 Coaching Session ID
- **表名**: `coaching_session`
- **用途**: 教練會談記錄
- **範例**: `7e5e120d-594b-472b-95cc-353f8ff50b72`
- **API 路徑**: `/api/v1/coaching-sessions/{id}`
- **頁面 URL**: `/dashboard/sessions/{id}` (實際上是 coaching session)

### 2. 📝 Transcript Session ID  
- **表名**: `session`
- **用途**: 語音轉錄記錄
- **範例**: `e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9`
- **API 路徑**: `/api/v1/sessions/{id}`
- **關聯**: 儲存在 `coaching_session.transcription_session_id`

## 關聯關係

```
CoachingSession
├── id: 7e5e120d-594b-472b-95cc-353f8ff50b72
├── user_id: 9b9f9bdc-7e3c-4a0d-a9c4-bb8456d7f8a6
├── transcription_session_id: e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9
└── ... (other fields)

Session (Transcript)  
├── id: e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9
├── user_id: 9b9f9bdc-7e3c-4a0d-a9c4-bb8456d7f8a6
└── segments: TranscriptSegment[]
```

## 實際案例
```
前端頁面: /dashboard/sessions/7e5e120d-594b-472b-95cc-353f8ff50b72
         ↓ (這是 coaching session ID)
API 查找: coaching_session.transcription_session_id 
         ↓ 
實際 transcript: e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9
         ↓
處理 segments: session.id = e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9
```

## 解決方案

### API 端點修正 (`transcript_smoothing.py`)
```python
# 🔍 智能 Session ID 識別
coaching_session = db.query(CoachingSession).filter(
    CoachingSession.id == session_id,
    CoachingSession.user_id == current_user.id
).first()

transcript_session_id = None
if coaching_session and coaching_session.transcription_session_id:
    # 找到關聯的 transcript session
    transcript_session_id = coaching_session.transcription_session_id
    logger.info(f"Found coaching session {session_id} with transcript session {transcript_session_id}")
else:
    # 直接作為 transcript session ID
    transcript_session_id = session_id
    logger.info(f"Treating {session_id} as direct transcript session ID")
```

## 識別方法

### 🔍 日誌識別
```bash
# Coaching Session 的日誌
GET /api/v1/coaching-sessions/7e5e120d-594b-472b-95cc-353f8ff50b72 HTTP/1.1" 200 OK

# Transcript Session 的日誌  
GET /api/v1/sessions/e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9 HTTP/1.1" 200 OK
```

### 🎯 API 端點區別
```
Coaching Session APIs:
- GET /api/v1/coaching-sessions/{id}
- POST /api/v1/coaching-sessions
- ...

Transcript Session APIs:  
- GET /api/v1/sessions/{id}
- GET /api/v1/sessions/{id}/transcript
- POST /api/v1/transcript/session/{id}/lemur-*
```

## 最佳實踐

### ✅ DO
1. **明確變數命名**:
   ```javascript
   const coachingSessionId = '7e5e120d-...'
   const transcriptSessionId = 'e7e1a9b2-...'
   ```

2. **API 設計時考慮兩種 ID**:
   ```python
   async def process_transcript(session_id: str):
       # 自動識別並轉換 session ID 類型
       transcript_session_id = resolve_transcript_session_id(session_id)
   ```

3. **日誌中標明類型**:
   ```python
   logger.info(f"Processing coaching session {coaching_id} -> transcript session {transcript_id}")
   ```

### ❌ DON'T  
1. **假設 session ID 類型**:
   ```python
   # ❌ 直接假設是 transcript session
   segments = get_segments(session_id)
   ```

2. **混用變數名**:
   ```javascript  
   // ❌ 不清楚是哪種 session
   const sessionId = getSessionIdFromUrl()
   ```

## 相關檔案
- `src/coaching_assistant/models/coaching_session.py` - CoachingSession 模型
- `src/coaching_assistant/models/session.py` - Session (Transcript) 模型  
- `src/coaching_assistant/api/transcript_smoothing.py` - LeMUR API (已修正)
- `apps/web/app/dashboard/sessions/[id]/page.tsx` - 前端頁面

## 測試驗證
```bash
# 驗證 coaching session 存在
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/coaching-sessions/7e5e120d-594b-472b-95cc-353f8ff50b72

# 驗證 transcript session 存在  
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/v1/sessions/e7e1a9b2-45a2-4cad-83ae-e2d4a5871bb9

# 測試 LeMUR API (會自動識別)
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_prompts": {"speakerPrompt": "test"}}' \
  http://localhost:8000/api/v1/transcript/session/7e5e120d-594b-472b-95cc-353f8ff50b72/lemur-speaker-identification
```