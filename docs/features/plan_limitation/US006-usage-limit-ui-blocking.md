# US006: 使用量限制 UI 阻擋功能

## 使用者故事
作為一個免費或付費方案的使用者，
當我的使用量（會談數、錄音檔分鐘數、或轉錄數）達到方案上限時，
我希望在嘗試使用音檔分析功能時能看到清楚的限制提示，
並能方便地升級到更高的方案。

## 業務需求
- 防止超出方案限制的使用
- 引導使用者升級以獲得更多使用量
- 提供清晰的使用量狀態資訊

## 技術規格

### 1. 需要檢查的限制項目
- **會談數限制** (`session_count`)
  - Free: 10 sessions/月
  - Pro: 100 sessions/月
  - Enterprise: 無限制

- **音檔分鐘數限制** (`usage_minutes`)
  - Free: 120 分鐘/月 (2小時)
  - Pro: 1200 分鐘/月 (20小時)
  - Enterprise: 無限制

- **轉錄數限制** (`transcription_count`)
  - Free: 20 transcriptions/月
  - Pro: 200 transcriptions/月
  - Enterprise: 無限制

### 2. 實作位置

#### 2.1 會談詳情頁面 (`/app/dashboard/sessions/[id]/page.tsx`)

```typescript
// 導入必要的 hooks
import { usePlanLimits } from '@/hooks/usePlanLimits';

// 在元件中使用
const { canCreateSession, canTranscribe, validateAction } = usePlanLimits();

// 檢查是否可以使用音檔分析
const [canUseAudioAnalysis, setCanUseAudioAnalysis] = useState(true);
const [limitMessage, setLimitMessage] = useState<{
  type: string;
  current: number;
  limit: number;
  message: string;
} | null>(null);

useEffect(() => {
  checkUsageLimits();
}, []);

const checkUsageLimits = async () => {
  // 檢查會談數限制
  const sessionAllowed = await canCreateSession({ silent: true });
  if (!sessionAllowed) {
    const result = await validateAction('create_session', {}, { silent: true });
    setCanUseAudioAnalysis(false);
    setLimitMessage({
      type: 'sessions',
      current: result.limitInfo?.current || 0,
      limit: result.limitInfo?.limit || 0,
      message: t('limits.sessionLimitReached')
    });
    return;
  }

  // 檢查轉錄數限制
  const transcribeAllowed = await canTranscribe({ silent: true });
  if (!transcribeAllowed) {
    const result = await validateAction('transcribe', {}, { silent: true });
    setCanUseAudioAnalysis(false);
    setLimitMessage({
      type: 'transcriptions',
      current: result.limitInfo?.current || 0,
      limit: result.limitInfo?.limit || 0,
      message: t('limits.transcriptionLimitReached')
    });
    return;
  }

  // 檢查音檔分鐘數限制
  const minutesAllowed = await validateAction('check_minutes', {}, { silent: true });
  if (!minutesAllowed) {
    setCanUseAudioAnalysis(false);
    setLimitMessage({
      type: 'minutes',
      current: result.limitInfo?.current || 0,
      limit: result.limitInfo?.limit || 0,
      message: t('limits.minutesLimitReached')
    });
    return;
  }

  setCanUseAudioAnalysis(true);
};
```

#### 2.2 限制達到時的 UI 顯示

```tsx
{/* 音檔分析區塊 */}
{uploadMode === 'audio' && !canUseAudioAnalysis ? (
  {/* 使用量限制提示 */}
  <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-6">
    <div className="flex items-start gap-4">
      <ExclamationTriangleIcon className="h-6 w-6 text-red-600 dark:text-red-400 flex-shrink-0 mt-1" />
      <div className="flex-1">
        <h4 className="text-lg font-semibold text-red-900 dark:text-red-100 mb-2">
          {t('limits.usageLimitReached')}
        </h4>
        <p className="text-red-700 dark:text-red-300 mb-3">
          {limitMessage?.message}
        </p>
        {limitMessage && (
          <div className="bg-white dark:bg-gray-800 rounded-md p-3 mb-4">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600 dark:text-gray-400">
                {t(`limits.${limitMessage.type}`)}
              </span>
              <span className="text-sm font-medium text-red-600 dark:text-red-400">
                {limitMessage.current} / {limitMessage.limit}
              </span>
            </div>
            <div className="mt-2 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div 
                className="bg-red-600 h-2 rounded-full"
                style={{ width: '100%' }}
              />
            </div>
          </div>
        )}
        <div className="flex gap-3">
          <button
            onClick={() => router.push('/dashboard/billing?tab=plans')}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <ArrowUpIcon className="h-4 w-4 inline mr-2" />
            {t('limits.upgradeNow')}
          </button>
          <button
            onClick={() => router.push('/dashboard/billing?tab=overview')}
            className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
          >
            {t('limits.viewUsage')}
          </button>
        </div>
      </div>
    </div>
  </div>
) : uploadMode === 'audio' && (
  {/* 正常的 AudioUploader */}
  <AudioUploader ... />
)}
```

### 3. AudioUploader 元件更新

```typescript
// components/AudioUploader.tsx
import { usePlanLimits } from '@/hooks/usePlanLimits';

export function AudioUploader({ ... }) {
  const { checkBeforeAction } = usePlanLimits();
  
  const handleFileSelect = async (file: File) => {
    // 在上傳前檢查限制
    await checkBeforeAction('create_session', async () => {
      await checkBeforeAction('transcribe', async () => {
        // 繼續原本的上傳流程
        proceedWithUpload(file);
      });
    });
  };
}
```

### 4. 新增翻譯字串

```typescript
// lib/translations.ts
// 中文
'limits.usageLimitReached': '使用量已達上限',
'limits.sessionLimitReached': '您本月的會談數已達到方案上限',
'limits.transcriptionLimitReached': '您本月的轉錄數已達到方案上限',
'limits.minutesLimitReached': '您本月的音檔分鐘數已達到方案上限',
'limits.sessions': '會談數',
'limits.transcriptions': '轉錄數',
'limits.minutes': '音檔分鐘數',
'limits.upgradeNow': '立即升級',
'limits.viewUsage': '查看使用量',

// 英文
'limits.usageLimitReached': 'Usage Limit Reached',
'limits.sessionLimitReached': 'You have reached your monthly session limit',
'limits.transcriptionLimitReached': 'You have reached your monthly transcription limit',
'limits.minutesLimitReached': 'You have reached your monthly audio minutes limit',
'limits.sessions': 'Sessions',
'limits.transcriptions': 'Transcriptions',
'limits.minutes': 'Audio Minutes',
'limits.upgradeNow': 'Upgrade Now',
'limits.viewUsage': 'View Usage',
```

## 測試計畫

### 1. 單元測試

```typescript
// __tests__/sessions/usage-limits.test.tsx
describe('Session Detail Usage Limits', () => {
  it('should show limit message when session limit is reached', async () => {
    // Mock user with maxed out sessions
    mockUser({ session_count: 10, plan: 'FREE' });
    
    render(<SessionDetailPage />);
    
    // Click audio analysis
    fireEvent.click(screen.getByText('音檔分析'));
    
    // Should show limit message
    expect(screen.getByText('使用量已達上限')).toBeInTheDocument();
    expect(screen.getByText('10 / 10')).toBeInTheDocument();
    expect(screen.getByText('立即升級')).toBeInTheDocument();
  });

  it('should navigate to billing page when upgrade button is clicked', async () => {
    mockUser({ session_count: 10, plan: 'FREE' });
    
    render(<SessionDetailPage />);
    
    fireEvent.click(screen.getByText('音檔分析'));
    fireEvent.click(screen.getByText('立即升級'));
    
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/billing?tab=plans');
  });
});
```

### 2. 整合測試

```typescript
// e2e/usage-limits.spec.ts
test('Usage limit blocking flow', async ({ page }) => {
  // Setup: Login as user with maxed limits
  await loginAsUser(page, { plan: 'FREE', session_count: 10 });
  
  // Navigate to session detail
  await page.goto('/dashboard/sessions/test-session-id');
  
  // Try to use audio analysis
  await page.click('text=音檔分析');
  
  // Verify limit message is shown
  await expect(page.locator('text=使用量已達上限')).toBeVisible();
  await expect(page.locator('text=10 / 10')).toBeVisible();
  
  // Click upgrade button
  await page.click('text=立即升級');
  
  // Verify navigation to billing page
  await expect(page).toHaveURL(/.*\/dashboard\/billing\?tab=plans/);
});
```

### 3. 手動測試檢查清單

#### 測試場景 1: 會談數限制
1. 建立測試帳號，設定 FREE plan
2. 手動將 session_count 設為 10
3. 進入任一會談詳情頁
4. 點擊「音檔分析」
5. 確認顯示限制提示
6. 確認顯示 "10 / 10 會談數"
7. 點擊「立即升級」確認跳轉到計費頁面

#### 測試場景 2: 分鐘數限制
1. 建立測試帳號，設定 FREE plan
2. 手動將 usage_minutes 設為 120
3. 進入會談詳情頁
4. 點擊「音檔分析」
5. 確認顯示分鐘數限制提示
6. 確認顯示 "120 / 120 分鐘"

#### 測試場景 3: 多重限制
1. 設定多個限制都達到上限
2. 確認優先顯示會談數限制（因為這是第一個檢查的）

#### 測試場景 4: 升級後解除限制
1. 從 FREE 升級到 PRO
2. 確認可以正常使用音檔分析功能
3. 確認限制提示不再顯示

## 驗收標準

- [ ] 當會談數達到上限時，音檔分析功能顯示限制提示
- [ ] 當分鐘數達到上限時，音檔分析功能顯示限制提示
- [ ] 當轉錄數達到上限時，音檔分析功能顯示限制提示
- [ ] 限制提示清楚顯示目前使用量和上限
- [ ] 提供明顯的「立即升級」按鈕
- [ ] 點擊升級按鈕跳轉到計費頁面的方案選擇標籤
- [ ] 提供「查看使用量」選項跳轉到計費概覽
- [ ] 支援中英文顯示
- [ ] 深色模式下顏色對比度適當

## 實作優先級
1. **P0**: 基本限制檢查和阻擋功能
2. **P1**: 優雅的 UI 提示和升級引導
3. **P2**: 詳細的使用量顯示和進度條
4. **P3**: 預警提示（接近限制時的提醒）

## 相關文件
- [US001: 方案限制基礎架構](./US001-plan-limits-infrastructure.md)
- [US002: API 端點限制檢查](./US002-api-validation.md)
- [US003: 前端限制檢查 Hook](./US003-frontend-hooks.md)
- [US004: 使用量追蹤服務](./US004-usage-tracking.md)
- [US005: 計費頁面整合](./US005-billing-page.md)