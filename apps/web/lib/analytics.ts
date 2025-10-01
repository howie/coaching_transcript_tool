/**
 * Google Analytics 4 事件追蹤工具
 *
 * 使用方式：
 * import { trackEvent } from '@/lib/analytics'
 * trackEvent('user_signup_complete', { method: 'email' })
 */

// 擴展 Window 介面以支援 gtag
declare global {
  interface Window {
    gtag?: (
      command: 'event' | 'config' | 'set',
      targetId: string,
      config?: Record<string, any>
    ) => void
    dataLayer?: any[]
  }
}

/**
 * 追蹤自定義事件
 * @param eventName - GA4 事件名稱
 * @param params - 事件參數（選填）
 */
export const trackEvent = (eventName: string, params?: Record<string, any>) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', eventName, params || {})

    // Development mode logging
    if (process.env.NODE_ENV === 'development') {
      console.log('📊 GA Event Tracked:', eventName, params)
    }
  } else if (process.env.NODE_ENV === 'development') {
    console.warn('⚠️  GTM not loaded, event not tracked:', eventName, params)
  }
}

/**
 * 追蹤頁面瀏覽
 * @param path - 頁面路徑
 * @param title - 頁面標題（選填）
 */
export const trackPageView = (path: string, title?: string) => {
  trackEvent('page_view', {
    page_path: path,
    page_title: title || document.title,
  })
}

// === Onboarding 相關事件 ===

/**
 * 使用者註冊事件
 */
export const trackSignup = {
  start: () => trackEvent('user_signup_start'),
  complete: (method: 'email' | 'google') =>
    trackEvent('user_signup_complete', { method }),
}

/**
 * 使用者登入事件
 */
export const trackLogin = {
  start: () => trackEvent('user_login_start'),
  complete: (method: 'email' | 'google') =>
    trackEvent('user_login_complete', { method }),
}

/**
 * Dashboard 首次體驗事件
 */
export const trackDashboard = {
  firstView: (userId: string) =>
    trackEvent('dashboard_first_view', { user_id: userId }),
  quickStartView: () => trackEvent('quick_start_guide_view'),
  quickStartStepClick: (step: number) =>
    trackEvent('quick_start_step_click', { step }),
  privacyNoticeView: () => trackEvent('privacy_notice_view'),
  privacyNoticeClick: () => trackEvent('privacy_notice_click'),
}

/**
 * Coaching Session 事件
 */
export const trackSession = {
  createStart: () => trackEvent('session_create_start'),
  createComplete: (sessionId: string) =>
    trackEvent('session_create_complete', { session_id: sessionId }),
  createCancel: () => trackEvent('session_create_cancel'),
  view: (sessionId: string) =>
    trackEvent('session_view', { session_id: sessionId }),
}

/**
 * 錄音上傳與轉檔事件
 */
export const trackAudio = {
  uploadStart: (sessionId: string) =>
    trackEvent('audio_upload_start', { session_id: sessionId }),
  uploadComplete: (sessionId: string, fileSize: number, duration?: number) =>
    trackEvent('audio_upload_complete', {
      session_id: sessionId,
      file_size: fileSize,
      duration
    }),
  uploadFailed: (sessionId: string, errorType: string) =>
    trackEvent('audio_upload_failed', {
      session_id: sessionId,
      error_type: errorType
    }),
  transcriptProcessingStart: (sessionId: string) =>
    trackEvent('transcript_processing_start', { session_id: sessionId }),
  transcriptProcessingComplete: (sessionId: string, duration: number) =>
    trackEvent('transcript_processing_complete', {
      session_id: sessionId,
      duration
    }),
  transcriptProcessingFailed: (sessionId: string, errorType: string) =>
    trackEvent('transcript_processing_failed', {
      session_id: sessionId,
      error_type: errorType
    }),
  transcriptView: (sessionId: string) =>
    trackEvent('transcript_view', { session_id: sessionId }),
  transcriptDelete: (sessionId: string) =>
    trackEvent('transcript_delete', { session_id: sessionId }),
}

/**
 * AI Mentor 互動事件
 */
export const trackAIMentor = {
  firstInteraction: (sessionId: string) =>
    trackEvent('ai_mentor_first_interaction', { session_id: sessionId }),
  querySent: (sessionId: string, queryType?: string) =>
    trackEvent('ai_mentor_query_sent', {
      session_id: sessionId,
      query_type: queryType
    }),
  responseReceived: (sessionId: string, responseTime: number) =>
    trackEvent('ai_mentor_response_received', {
      session_id: sessionId,
      response_time: responseTime
    }),
}

/**
 * Onboarding 完成度事件
 */
export const trackOnboarding = {
  stepComplete: (step: number) =>
    trackEvent('onboarding_step_complete', { step }),
  allComplete: (completionTime: number) =>
    trackEvent('onboarding_all_complete', { completion_time: completionTime }),
  abandoned: (lastCompletedStep: number) =>
    trackEvent('onboarding_abandoned', { last_completed_step: lastCompletedStep }),
}
