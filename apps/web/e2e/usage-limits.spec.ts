import { test, expect, Page } from '@playwright/test';

// Mock API responses for testing
const mockValidationResponse = (allowed: boolean, limitInfo: any) => ({
  allowed,
  message: allowed ? null : 'You have reached your limit',
  limit_info: limitInfo,
  upgrade_suggestion: !allowed ? {
    plan_id: 'PRO',
    display_name: 'Pro Plan',
    benefits: ['100 sessions/month', '1200 minutes/month', '200 transcriptions/month']
  } : null
});

/**
 * Helper function to login as a user with specific plan and usage
 */
async function loginAsUser(page: Page, options: {
  plan: 'FREE' | 'PRO' | 'ENTERPRISE',
  session_count?: number,
  transcription_count?: number,
  usage_minutes?: number
}) {
  // Mock the authentication and user data
  // In a real test environment, this would set up the test user in the database
  await page.goto('/login');
  
  // Mock Google SSO login
  await page.evaluate((opts) => {
    // Set mock user data in localStorage or session storage
    localStorage.setItem('mockUser', JSON.stringify({
      id: 'test-user-id',
      name: 'Test User',
      email: 'test@example.com',
      plan: opts.plan,
      usage: {
        session_count: opts.session_count || 0,
        transcription_count: opts.transcription_count || 0,
        usage_minutes: opts.usage_minutes || 0
      }
    }));
  }, options);
  
  // Navigate to dashboard
  await page.goto('/dashboard');
  await expect(page).toHaveURL(/.*\/dashboard/);
}

test.describe('Usage Limit Blocking Flow', () => {
  test('should block audio analysis when session limit is reached', async ({ page }) => {
    // Setup: Login as user with maxed session limit
    await loginAsUser(page, { 
      plan: 'FREE', 
      session_count: 10 // FREE plan limit
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('會談詳情');
    
    // Click on audio analysis tab/section
    await page.click('text=音檔分析');
    
    // Verify limit message is shown
    await expect(page.locator('text=使用量已達上限')).toBeVisible();
    await expect(page.locator('text=您本月的會談數已達到方案上限')).toBeVisible();
    await expect(page.locator('text=10 / 10')).toBeVisible();
    
    // Verify upgrade button is present
    await expect(page.locator('text=立即升級')).toBeVisible();
    
    // Click upgrade button
    await page.click('text=立即升級');
    
    // Verify navigation to billing page with plans tab
    await expect(page).toHaveURL(/.*\/dashboard\/billing\?tab=plans/);
  });

  test('should block audio analysis when transcription limit is reached', async ({ page }) => {
    // Setup: Login as user with maxed transcription limit
    await loginAsUser(page, { 
      plan: 'FREE', 
      session_count: 5,
      transcription_count: 20 // FREE plan limit
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('會談詳情');
    
    // Click on audio analysis
    await page.click('text=音檔分析');
    
    // Verify transcription limit message is shown
    await expect(page.locator('text=使用量已達上限')).toBeVisible();
    await expect(page.locator('text=您本月的轉錄數已達到方案上限')).toBeVisible();
    await expect(page.locator('text=20 / 20')).toBeVisible();
  });

  test('should block audio analysis when minutes limit is reached', async ({ page }) => {
    // Setup: Login as user with maxed minutes limit
    await loginAsUser(page, { 
      plan: 'FREE', 
      session_count: 5,
      transcription_count: 10,
      usage_minutes: 120 // FREE plan limit (2 hours)
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('會談詳情');
    
    // Click on audio analysis
    await page.click('text=音檔分析');
    
    // Verify minutes limit message is shown
    await expect(page.locator('text=使用量已達上限')).toBeVisible();
    await expect(page.locator('text=您本月的音檔分鐘數已達到方案上限')).toBeVisible();
    await expect(page.locator('text=120 / 120')).toBeVisible();
  });

  test('should allow audio analysis when limits are not reached', async ({ page }) => {
    // Setup: Login as user with available quota
    await loginAsUser(page, { 
      plan: 'FREE', 
      session_count: 3,
      transcription_count: 5,
      usage_minutes: 30
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Wait for page to load
    await expect(page.locator('h1')).toContainText('會談詳情');
    
    // Click on audio analysis
    await page.click('text=音檔分析');
    
    // Verify limit message is NOT shown
    await expect(page.locator('text=使用量已達上限')).not.toBeVisible();
    
    // Verify audio upload interface is shown
    await expect(page.locator('text=上傳音檔進行轉錄')).toBeVisible();
  });

  test('should navigate to usage overview when clicking view usage', async ({ page }) => {
    // Setup: Login as user with maxed limits
    await loginAsUser(page, { 
      plan: 'FREE', 
      session_count: 10
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Click on audio analysis
    await page.click('text=音檔分析');
    
    // Wait for limit message
    await expect(page.locator('text=使用量已達上限')).toBeVisible();
    
    // Click view usage button
    await page.click('text=查看使用量');
    
    // Verify navigation to billing overview
    await expect(page).toHaveURL(/.*\/dashboard\/billing\?tab=overview/);
  });

  test('should block file selection in AudioUploader when limits reached', async ({ page }) => {
    // Setup: Login as user with maxed limits
    await loginAsUser(page, { 
      plan: 'FREE', 
      session_count: 10
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Try to upload a file through the file input
    const fileInput = page.locator('input[type="file"]');
    
    // Check if file input is disabled or hidden when limits are reached
    await expect(fileInput).not.toBeVisible();
  });

  test('should show limit message immediately after upgrade expiry', async ({ page }) => {
    // Setup: Login as PRO user who just hit their limit
    await loginAsUser(page, { 
      plan: 'PRO', 
      session_count: 100 // PRO plan limit
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Click on audio analysis
    await page.click('text=音檔分析');
    
    // Verify limit message for PRO plan
    await expect(page.locator('text=使用量已達上限')).toBeVisible();
    await expect(page.locator('text=100 / 100')).toBeVisible();
    
    // Verify upgrade suggestion (to Enterprise)
    await expect(page.locator('text=立即升級')).toBeVisible();
  });

  test('should not show limit message for Enterprise users', async ({ page }) => {
    // Setup: Login as Enterprise user with high usage
    await loginAsUser(page, { 
      plan: 'ENTERPRISE', 
      session_count: 500,
      transcription_count: 1000,
      usage_minutes: 5000
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Click on audio analysis
    await page.click('text=音檔分析');
    
    // Verify NO limit message is shown (Enterprise has unlimited)
    await expect(page.locator('text=使用量已達上限')).not.toBeVisible();
    
    // Verify audio upload interface is available
    await expect(page.locator('text=上傳音檔進行轉錄')).toBeVisible();
  });
});

test.describe('API Integration Tests', () => {
  test('should handle API validation response correctly', async ({ page }) => {
    // Mock API endpoint
    await page.route('**/api/v1/plan/validate-action', async route => {
      const request = route.request();
      const postData = request.postDataJSON();
      
      if (postData.action === 'create_session') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockValidationResponse(false, {
            type: 'sessions',
            current: 10,
            limit: 10,
            reset_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
          }))
        });
      }
    });

    await loginAsUser(page, { plan: 'FREE', session_count: 10 });
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Click audio analysis to trigger validation
    await page.click('text=音檔分析');
    
    // Verify API was called
    await expect(page.locator('text=使用量已達上限')).toBeVisible();
  });

  test('should retry validation on network failure', async ({ page }) => {
    let callCount = 0;
    
    await page.route('**/api/v1/plan/validate-action', async route => {
      callCount++;
      
      if (callCount === 1) {
        // First call fails
        await route.abort('failed');
      } else {
        // Second call succeeds
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockValidationResponse(true, {
            type: 'sessions',
            current: 5,
            limit: 10,
            reset_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
          }))
        });
      }
    });

    await loginAsUser(page, { plan: 'FREE', session_count: 5 });
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Should retry and eventually show upload interface
    await page.click('text=音檔分析');
    await expect(page.locator('text=上傳音檔進行轉錄')).toBeVisible({ timeout: 10000 });
  });

  test('should cache validation results', async ({ page }) => {
    let apiCallCount = 0;
    
    await page.route('**/api/v1/plan/validate-action', async route => {
      apiCallCount++;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockValidationResponse(true, {
          type: 'sessions',
          current: 3,
          limit: 10,
          reset_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
        }))
      });
    });

    await loginAsUser(page, { plan: 'FREE', session_count: 3 });
    await page.goto('/dashboard/sessions/test-session-id');
    
    // First click - should call API
    await page.click('text=音檔分析');
    await expect(page.locator('text=上傳音檔進行轉錄')).toBeVisible();
    const firstCallCount = apiCallCount;
    
    // Navigate away and back
    await page.click('text=會談概覽');
    await page.click('text=音檔分析');
    
    // Should use cached result (no additional API call)
    expect(apiCallCount).toBe(firstCallCount);
  });
});

test.describe('Real-time Usage Updates', () => {
  test('should update UI when usage changes', async ({ page }) => {
    await loginAsUser(page, { plan: 'FREE', session_count: 9 });
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Initially allowed
    await page.click('text=音檔分析');
    await expect(page.locator('text=上傳音檔進行轉錄')).toBeVisible();
    
    // Simulate usage increase via WebSocket or polling
    await page.evaluate(() => {
      // Emit custom event to simulate usage update
      window.dispatchEvent(new CustomEvent('usage-updated', {
        detail: { session_count: 10 }
      }));
    });
    
    // Should now show limit reached
    await expect(page.locator('text=使用量已達上限')).toBeVisible({ timeout: 5000 });
  });

  test('should show countdown to reset date', async ({ page }) => {
    const resetDate = new Date(Date.now() + 5 * 24 * 60 * 60 * 1000); // 5 days from now
    
    await page.route('**/api/v1/plan/validate-action', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockValidationResponse(false, {
          type: 'sessions',
          current: 10,
          limit: 10,
          reset_date: resetDate.toISOString()
        }))
      });
    });

    await loginAsUser(page, { plan: 'FREE', session_count: 10 });
    await page.goto('/dashboard/sessions/test-session-id');
    await page.click('text=音檔分析');
    
    // Should show days until reset
    await expect(page.locator('text=/重置於 \\d+ 天後/')).toBeVisible();
  });
});

test.describe('Upload Flow with Limits', () => {
  test('should block file selection when limits reached', async ({ page }) => {
    await loginAsUser(page, { plan: 'FREE', session_count: 10 });
    await page.goto('/dashboard/sessions/test-session-id');
    await page.click('text=音檔分析');
    
    // File input should not be available
    const fileInput = page.locator('input[type="file"]');
    await expect(fileInput).not.toBeVisible();
    
    // Drag and drop should show warning
    const dropZone = page.locator('[data-testid="drop-zone"]');
    if (await dropZone.isVisible()) {
      const file = {
        name: 'test-audio.mp3',
        mimeType: 'audio/mp3',
        buffer: Buffer.from('test audio content')
      };
      
      await dropZone.dispatchEvent('drop', {
        dataTransfer: {
          files: [file],
          types: ['Files']
        }
      });
      
      // Should show limit message, not process file
      await expect(page.locator('text=使用量已達上限')).toBeVisible();
    }
  });

  test('should validate before starting upload', async ({ page }) => {
    let validationCalled = false;
    
    await page.route('**/api/v1/plan/validate-action', async route => {
      validationCalled = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockValidationResponse(true, {
          type: 'sessions',
          current: 5,
          limit: 10,
          reset_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString()
        }))
      });
    });

    await loginAsUser(page, { plan: 'FREE', session_count: 5 });
    await page.goto('/dashboard/sessions/test-session-id');
    await page.click('text=音檔分析');
    
    // Select a file
    const fileInput = page.locator('input[type="file"]');
    await fileInput.setInputFiles({
      name: 'test-audio.mp3',
      mimeType: 'audio/mp3',
      buffer: Buffer.from('test audio content')
    });
    
    // Click upload button
    await page.click('text=開始處理音檔');
    
    // Validation should have been called
    expect(validationCalled).toBe(true);
  });
});

test.describe('Plan Upgrade Flow', () => {
  test('should navigate to correct billing tab', async ({ page }) => {
    await loginAsUser(page, { plan: 'FREE', session_count: 10 });
    await page.goto('/dashboard/sessions/test-session-id');
    await page.click('text=音檔分析');
    
    // Click upgrade button
    await page.click('text=立即升級');
    
    // Should navigate to billing page with plans tab
    await expect(page).toHaveURL(/.*\/dashboard\/billing\?tab=plans/);
    
    // Plans tab should be active
    await expect(page.locator('[data-tab="plans"].active')).toBeVisible();
    
    // PRO plan should be highlighted
    await expect(page.locator('[data-plan="PRO"].recommended')).toBeVisible();
  });

  test('should show comparison with current plan', async ({ page }) => {
    await loginAsUser(page, { plan: 'FREE', session_count: 10 });
    await page.goto('/dashboard/sessions/test-session-id');
    await page.click('text=音檔分析');
    await page.click('text=立即升級');
    
    // Should show plan comparison
    await expect(page.locator('text=目前方案: Free')).toBeVisible();
    await expect(page.locator('text=建議方案: Pro')).toBeVisible();
    
    // Should highlight the specific limit that was exceeded
    await expect(page.locator('[data-limit="sessions"].exceeded')).toBeVisible();
  });
});

test.describe('Multi-language Support', () => {
  test('should display limit messages in English', async ({ page }) => {
    // Set language to English
    await page.goto('/dashboard/settings');
    await page.selectOption('select[name="language"]', 'en');
    
    // Login as user with maxed limits
    await loginAsUser(page, { 
      plan: 'FREE', 
      session_count: 10
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Click on audio analysis
    await page.click('text=Audio Analysis');
    
    // Verify English limit messages
    await expect(page.locator('text=Usage Limit Reached')).toBeVisible();
    await expect(page.locator('text=You have reached your monthly session limit')).toBeVisible();
    await expect(page.locator('text=Upgrade Now')).toBeVisible();
    await expect(page.locator('text=View Usage')).toBeVisible();
  });

  test('should display limit messages in Traditional Chinese', async ({ page }) => {
    // Set language to Traditional Chinese
    await page.goto('/dashboard/settings');
    await page.selectOption('select[name="language"]', 'zh');
    
    // Login as user with maxed limits
    await loginAsUser(page, { 
      plan: 'FREE', 
      transcription_count: 20
    });
    
    // Navigate to session detail page
    await page.goto('/dashboard/sessions/test-session-id');
    
    // Click on audio analysis
    await page.click('text=音檔分析');
    
    // Verify Chinese limit messages
    await expect(page.locator('text=使用量已達上限')).toBeVisible();
    await expect(page.locator('text=您本月的轉錄數已達到方案上限')).toBeVisible();
    await expect(page.locator('text=立即升級')).toBeVisible();
    await expect(page.locator('text=查看使用量')).toBeVisible();
  });
});