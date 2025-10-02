# Coachly Onboarding 改善計畫

## 核心目標
改善登入 Dashboard 後的新手引導體驗，讓使用者快速了解核心功能，並透過 GA 事件追蹤優化流程。

---

## 一、Dashboard 快速開始指南改善

### 現況分析

**組件位置**：
- [apps/web/components/sections/getting-started.tsx](apps/web/components/sections/getting-started.tsx)
- [apps/web/lib/i18n/translations/dashboard.ts](apps/web/lib/i18n/translations/dashboard.ts)

**現有步驟 (3 步)**：
1. **新增客戶** → `/dashboard/clients/new`
   - 創建並管理您的客戶資料，為教練會談做好準備
2. **新增教練 session** → `/dashboard/sessions`
   - 記錄您的教練會談，包含時間、收費和詳細備註
3. **上傳逐字稿** → `/dashboard/transcript-converter`
   - ❌ 問題：描述不準確，應該是「上傳錄音檔轉成逐字稿」而非「上傳逐字稿檔案」

**現況問題**：
- ❌ 步驟 3 的描述不正確（說上傳逐字稿，實際是上傳錄音檔）
- ❌ 缺少步驟 4：與 AI Mentor 互動
- ❌ 沒有隱私和資料保密說明

### 改善方案

#### 1.1 更新快速開始步驟

**步驟 1: 新增客戶** (維持不變)
- 路徑：`/dashboard/clients/new`
- 中文：創建並管理您的客戶資料，為教練會談做好準備
- 英文：Create and manage your client profiles to prepare for coaching sessions

**步驟 2: 新增教練 session** (維持不變)
- 路徑：`/dashboard/sessions`
- 中文：記錄您的教練會談，包含時間、收費和詳細備註
- 英文：Record your coaching sessions including time, fees, and detailed notes

**步驟 3: 上傳錄音檔** (更新描述)
- 路徑：`/dashboard/transcript-converter`
- 中文：上傳教練會談的錄音檔，系統會自動轉成逐字稿
- 英文：Upload session audio recordings to automatically convert them into transcripts

**步驟 4: 與 AI Mentor 互動** (新增)
- 路徑：`/dashboard/sessions/[id]` (session 詳情頁面)
- 中文：使用 AI 分析逐字稿，獲得教練技巧洞察和改進建議
- 英文：Use AI to analyze transcripts and get coaching insights and improvement suggestions

#### 1.2 隱私提示區塊

在快速開始指南下方新增「隱私與資料保密」提示卡片：

**設計規格**：
- 淺色背景卡片（bg-blue-50 dark:bg-blue-900/20）
- 包含 icon + 標題 + 3 個要點
- 可摺疊設計（預設展開，可關閉後儲存狀態到 localStorage）

**內容結構**：

```
🔐 您的隱私與資料安全

• 錄音檔處理：上傳的錄音檔在轉檔完成後會立即刪除
• 逐字稿管理：您可以隨時刪除教練 session 內的逐字稿內容
• 保留記錄：刪除逐字稿後仍會保留教練 session 和時數記錄

[了解更多隱私政策]
```

**中英文版本**：
- 中文：`您的隱私與資料安全`
- 英文：`Your Privacy & Data Security`

**實作位置**：
- 新增組件：`apps/web/components/sections/privacy-notice.tsx` ✅ 已完成
- 引用位置：`apps/web/app/dashboard/page.tsx` (在 GettingStarted 組件下方) ✅ 已完成

**注意**：
- ~~原規劃的「了解更多隱私政策」連結已移除~~（避免 404 錯誤）
- 隱私提示只顯示 3 個要點，簡潔明瞭

---

## 二、Google Analytics 事件追蹤規劃

### 目標
追蹤使用者在 onboarding 流程中的行為，找出卡點並優化體驗。

### 2.1 GTM (Google Tag Manager) 設定

**需要追蹤的頁面**：
- 註冊頁面 ([/signup](apps/web/app/signup/page.tsx))
- 登入頁面 ([/login](apps/web/app/login/page.tsx))
- Dashboard 主頁 ([/dashboard](apps/web/app/dashboard/page.tsx))
- 新增 Session 頁面 ([/dashboard/sessions/new](apps/web/app/dashboard/sessions/new/page.tsx))
- Session 詳情頁 ([/dashboard/sessions/[id]](apps/web/app/dashboard/sessions/[id]/page.tsx))
- 上傳轉檔頁面 ([/dashboard/transcript-converter](apps/web/app/dashboard/transcript-converter/page.tsx))

### 2.2 GA 事件追蹤清單

#### A. 使用者註冊與登入
| 事件名稱 | 觸發時機 | 參數 |
|---------|---------|------|
| `user_signup_start` | 進入註冊頁面 | - |
| `user_signup_complete` | 註冊成功 | `method`: 'email'/'google' |
| `user_login_start` | 進入登入頁面 | - |
| `user_login_complete` | 登入成功 | `method`: 'email'/'google' |

#### B. Dashboard 首次體驗
| 事件名稱 | 觸發時機 | 參數 |
|---------|---------|------|
| `dashboard_first_view` | 首次登入 Dashboard | `user_id` |
| `quick_start_guide_view` | 查看快速開始指南 | - |
| `quick_start_step_click` | 點擊快速開始步驟 | `step`: 1/2/3/4 |
| `privacy_notice_view` | 查看隱私提示 | - |
| `privacy_notice_click` | 點擊隱私提示連結 | - |

#### C. 建立 Coaching Session
| 事件名稱 | 觸發時機 | 參數 |
|---------|---------|------|
| `session_create_start` | 進入新增 session 頁面 | - |
| `session_create_complete` | 成功建立 session | `session_id` |
| `session_create_cancel` | 取消建立 session | - |
| `session_view` | 查看 session 詳情 | `session_id` |

#### D. 上傳錄音與轉檔
| 事件名稱 | 觸發時機 | 參數 |
|---------|---------|------|
| `audio_upload_start` | 開始上傳錄音檔 | `session_id` |
| `audio_upload_complete` | 上傳成功 | `session_id`, `file_size`, `duration` |
| `audio_upload_failed` | 上傳失敗 | `session_id`, `error_type` |
| `transcript_processing_start` | 開始轉檔 | `session_id` |
| `transcript_processing_complete` | 轉檔完成 | `session_id`, `duration` |
| `transcript_processing_failed` | 轉檔失敗 | `session_id`, `error_type` |
| `transcript_view` | 查看逐字稿 | `session_id` |
| `transcript_delete` | 刪除逐字稿 | `session_id` |

#### E. AI Mentor 互動
| 事件名稱 | 觸發時機 | 參數 |
|---------|---------|------|
| `ai_mentor_first_interaction` | 首次與 AI Mentor 互動 | `session_id` |
| `ai_mentor_query_sent` | 發送 AI 查詢 | `session_id`, `query_type` |
| `ai_mentor_response_received` | 收到 AI 回應 | `session_id`, `response_time` |

#### F. Onboarding 完成度
| 事件名稱 | 觸發時機 | 參數 |
|---------|---------|------|
| `onboarding_step_complete` | 完成任一 onboarding 步驟 | `step`: 1/2/3/4 |
| `onboarding_all_complete` | 完成所有 onboarding 步驟 | `completion_time` |
| `onboarding_abandoned` | 超過 7 天未完成 onboarding | `last_completed_step` |

### 2.3 漏斗分析 (Funnel Analysis)

追蹤使用者從註冊到完成 onboarding 的流程：

```
註冊完成
  ↓ (預期流失率 < 10%)
首次登入 Dashboard
  ↓ (預期流失率 < 20%)
建立第一個 Session
  ↓ (預期流失率 < 30%)
上傳第一個錄音檔
  ↓ (預期流失率 < 20%)
查看第一個逐字稿
  ↓ (預期流失率 < 30%)
首次使用 AI Mentor
```

---

## 三、實作優先順序與技術細節

### Phase 1: Dashboard 改善 ✅ 已完成 (2025-10-01)

#### 1.1 更新翻譯檔案 ✅
**檔案**: `apps/web/lib/i18n/translations/dashboard.ts`

已修改/新增的 translation keys：
```typescript
// ✅ 已修改
'dashboard.step3.title': '上傳錄音檔',  // 原: '上傳逐字稿'
'dashboard.step3.desc': '上傳教練會談的錄音檔，系統會自動轉成逐字稿。',

// ✅ 已新增步驟 4
'dashboard.step4.title': '與 AI Mentor 互動',
'dashboard.step4.desc': '使用 AI 分析逐字稿，獲得教練技巧洞察和改進建議。',

// ✅ 已新增隱私提示
'dashboard.privacy.title': '您的隱私與資料安全',
'dashboard.privacy.audio_processing': '錄音檔處理：上傳的錄音檔在轉檔完成後會立即刪除',
'dashboard.privacy.transcript_management': '逐字稿管理：您可以隨時刪除教練 session 內的逐字稿內容',
'dashboard.privacy.record_retention': '保留記錄：刪除逐字稿後仍會保留教練 session 和時數記錄',
```

#### 1.2 更新 GettingStarted 組件 ✅
**檔案**: `apps/web/components/sections/getting-started.tsx`

- ✅ 新增第 4 步
- ✅ 調整 grid layout 為 `md:grid-cols-2 lg:grid-cols-4`
- ✅ 加入步驟點擊事件追蹤

#### 1.3 新增 PrivacyNotice 組件 ✅
**檔案**: `apps/web/components/sections/privacy-notice.tsx` (新建)

已實作功能：
- ✅ 淡藍色背景卡片設計（bg-blue-50 dark:bg-blue-900/20）
- ✅ 可關閉功能（localStorage: `privacy_notice_dismissed`）
- ✅ ShieldCheck icon
- ✅ 3 個隱私要點
- ✅ 響應式設計 + 深色模式
- ✅ GA 事件追蹤（view + click）

#### 1.4 整合到 Dashboard ✅
**檔案**: `apps/web/app/dashboard/page.tsx`

- ✅ 引入 PrivacyNotice 組件
- ✅ 放置在 GettingStarted 下方
- ✅ 加入 Dashboard 首次瀏覽追蹤

#### 1.5 修復逐字稿刪除後的狀態顯示 ✅ (2025-10-02)
**問題**：刪除逐字稿後重新進入頁面，前端顯示「未上傳」而非「已刪除」，無法區分「從未上傳」vs「已刪除」狀態。

**解決方案**：
- ✅ 後端新增欄位：`transcript_deleted_at` (TIMESTAMP) 和 `saved_speaking_stats` (JSON)
  - 檔案：`alembic/versions/01dcbada3129_*.py`
  - 檔案：`src/coaching_assistant/core/models/coaching_session.py`
  - 檔案：`src/coaching_assistant/models/coaching_session.py`
- ✅ 更新刪除 API：保存統計資料和刪除時間戳
  - 檔案：`src/coaching_assistant/api/v1/coaching_sessions.py`
  - 接受 `speaking_stats` 參數
  - 設定 `transcript_deleted_at` 和 `saved_speaking_stats`
- ✅ 前端更新
  - 檔案：`apps/web/app/dashboard/sessions/[id]/page.tsx`
  - 更新 Session interface 包含新欄位
  - fetchSession 時初始化 `transcriptDeleted` 和 `savedSpeakingStats` state
  - 顯示三種狀態：
    1. 從未上傳：顯示上傳 UI
    2. 已刪除：顯示黃色提示卡片 + 保留統計資料
    3. 有逐字稿：正常顯示
- ✅ 更新 API client：`apps/web/lib/api.ts`
  - `deleteSessionTranscript()` 接受 `speakingStats` 參數
- ✅ 新增翻譯：`apps/web/lib/i18n/translations/sessions.ts`
  - `sessions.transcriptDeleted`: "逐字稿已刪除"
  - `sessions.transcriptDeletedDesc`: 描述文字
  - `sessions.savedStatistics`: "已保存的統計資料"

### Phase 2: GA 事件埋點 🔄 核心完成 (2025-10-01)

#### 2.1 設定 GTM 容器 ✅
**檔案**: `apps/web/app/layout.tsx`

- ✅ GTM 已存在（GTM-PX4SL4ZQ）
- ✅ GA4 已存在（G-859X61KC45）
- ✅ dataLayer 已初始化

#### 2.2 建立 Analytics Utility ✅
**檔案**: `apps/web/lib/analytics.ts` (新建)

已實作功能：
- ✅ `trackEvent` 基礎函數
- ✅ `trackPageView` 函數
- ✅ Development mode logging
- ✅ 8 個事件群組：
  - `trackSignup` - 註冊事件
  - `trackLogin` - 登入事件
  - `trackDashboard` - Dashboard 事件
  - `trackSession` - Session 事件
  - `trackAudio` - 錄音上傳事件
  - `trackAIMentor` - AI Mentor 事件
  - `trackOnboarding` - Onboarding 完成度事件

#### 2.3 實作核心事件追蹤 🔄
**已完成的事件追蹤**：
- ✅ `apps/web/app/dashboard/page.tsx`
  - dashboard_first_view
  - quick_start_guide_view
- ✅ `apps/web/components/sections/getting-started.tsx`
  - quick_start_step_click (1-4)
- ✅ `apps/web/components/sections/privacy-notice.tsx`
  - privacy_notice_view
  - privacy_notice_click

**待實作的事件追蹤**：
- ⏳ `apps/web/app/signup/page.tsx` → user_signup 事件
- ⏳ `apps/web/app/login/page.tsx` → user_login 事件
- ⏳ `apps/web/app/dashboard/sessions/new/page.tsx` → session_create 事件
- ⏳ `apps/web/app/dashboard/transcript-converter/page.tsx` → audio_upload 事件

### Phase 3: 進階追蹤與優化 (1 週)
1. 實作 AI Mentor 互動追蹤（E 類別）
2. 實作 Onboarding 完成度追蹤（F 類別）
3. 設定 GA4 漏斗分析報表
4. 設定自動化週報

---

## 四、成功指標

### 短期指標 (1-3 個月)
- 新使用者完成所有 onboarding 步驟：≥ 50%
- 首次上傳錄音檔成功率：≥ 80%
- 首次使用 AI Mentor：≥ 40%

### 中期指標 (3-6 個月)
- 註冊後 7 天留存率：≥ 60%
- 註冊後 30 天留存率：≥ 40%
- 平均完成 onboarding 時間：≤ 20 分鐘
