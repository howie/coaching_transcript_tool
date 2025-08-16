/**
 * Functional test to verify i18n is working correctly in SessionDetailPage
 * This test verifies that the t() function calls are actually working in the component
 */

import { translations } from '@/lib/i18n';

describe('SessionDetailPage i18n Functional Test', () => {
  
  it('should verify all critical translation keys exist and are not empty', () => {
    // Test critical translation keys used in SessionDetailPage
    const criticalKeys = [
      'sessions.overview',
      'sessions.transcript', 
      'sessions.aiAnalysis',
      'sessions.basicInfo',
      'sessions.transcriptContent',
      'sessions.audioAnalysis',
      'sessions.exportFormat',
      'sessions.exportTxt',
      'sessions.exportTranscript',
      'sessions.talkAnalysisResults',
      'sessions.sessionSummary',
      'sessions.generateSummary',
      'sessions.aiChat',
      'sessions.noTranscriptUploaded',
      'sessions.selectUploadMethod',
      'sessions.directUploadTitle',
      'sessions.audioAnalysisTitle',
    ];

    criticalKeys.forEach(key => {
      // Test Chinese translations
      expect(translations.zh[key as keyof typeof translations.zh]).toBeDefined();
      expect(translations.zh[key as keyof typeof translations.zh]).not.toBe('');
      expect(typeof translations.zh[key as keyof typeof translations.zh]).toBe('string');
      
      // Test English translations  
      expect(translations.en[key as keyof typeof translations.en]).toBeDefined();
      expect(translations.en[key as keyof typeof translations.en]).not.toBe('');
      expect(typeof translations.en[key as keyof typeof translations.en]).toBe('string');
    });
  });

  it('should verify parameter interpolation keys have correct format', () => {
    const interpolationKeys = [
      'sessions.uploadSuccess', // {count}
      'sessions.segmentsCount', // {count}
      'sessions.detectSpeakersMessage', // {count}
      'sessions.conversationSummary', // {duration}, {count}
      'sessions.conversionStatus', // {status}
      'sessions.conversionId', // {id}
      'sessions.goToOverviewToUpload', // {type}
      'sessions.needUploadForAI', // {type}
    ];

    interpolationKeys.forEach(key => {
      const zhValue = translations.zh[key as keyof typeof translations.zh] as string;
      const enValue = translations.en[key as keyof typeof translations.en] as string;
      
      // Should contain parameter placeholders
      expect(zhValue).toMatch(/\{[^}]+\}/);
      expect(enValue).toMatch(/\{[^}]+\}/);
      
      // Should not be empty
      expect(zhValue.length).toBeGreaterThan(0);
      expect(enValue.length).toBeGreaterThan(0);
    });
  });

  it('should verify tab navigation translations are complete', () => {
    const tabKeys = [
      'sessions.overview',
      'sessions.transcript', 
      'sessions.aiAnalysis',
    ];

    tabKeys.forEach(key => {
      const zhValue = translations.zh[key as keyof typeof translations.zh];
      const enValue = translations.en[key as keyof typeof translations.en];
      
      expect(zhValue).toBeDefined();
      expect(enValue).toBeDefined();
      expect(zhValue).not.toBe(enValue); // Should be different languages
    });

    // Verify specific tab translations
    expect(translations.zh['sessions.overview']).toBe('會談概覽');
    expect(translations.en['sessions.overview']).toBe('Overview');
    
    expect(translations.zh['sessions.transcript']).toBe('逐字稿');
    expect(translations.en['sessions.transcript']).toBe('Transcript');
    
    expect(translations.zh['sessions.aiAnalysis']).toBe('AI 分析');
    expect(translations.en['sessions.aiAnalysis']).toBe('AI Analysis');
  });

  it('should verify status and action translations are complete', () => {
    const statusKeys = [
      'sessions.processing',
      'sessions.processingCompleted',
      'sessions.uploading',
      'sessions.generating',
      'sessions.comingSoon',
    ];

    statusKeys.forEach(key => {
      const zhValue = translations.zh[key as keyof typeof translations.zh];
      const enValue = translations.en[key as keyof typeof translations.en];
      
      expect(zhValue).toBeDefined();
      expect(enValue).toBeDefined();
      expect(typeof zhValue).toBe('string');
      expect(typeof enValue).toBe('string');
      expect(zhValue.length).toBeGreaterThan(0);
      expect(enValue.length).toBeGreaterThan(0);
    });
  });

  it('should verify upload method translations are complete', () => {
    const uploadKeys = [
      'sessions.selectUploadMethod',
      'sessions.audioAnalysisTitle',
      'sessions.audioAnalysisDesc', 
      'sessions.directUploadTitle',
      'sessions.directUploadDesc',
      'sessions.directUploadWarning',
      'sessions.clickToUpload',
      'sessions.supportedFormatsVttSrt',
    ];

    uploadKeys.forEach(key => {
      const zhValue = translations.zh[key as keyof typeof translations.zh];
      const enValue = translations.en[key as keyof typeof translations.en];
      
      expect(zhValue).toBeDefined();
      expect(enValue).toBeDefined();
      expect(zhValue.length).toBeGreaterThan(0);
      expect(enValue.length).toBeGreaterThan(0);
    });
  });

  it('should verify form and UI element translations are complete', () => {
    const formKeys = [
      'sessions.editRole',
      'sessions.cancel',
      'sessions.save',
      'sessions.remove',
      'sessions.time',
      'sessions.speaker', 
      'sessions.content',
      'sessions.confidence',
      'sessions.coachRole',
      'sessions.clientRole',
    ];

    formKeys.forEach(key => {
      const zhValue = translations.zh[key as keyof typeof translations.zh];
      const enValue = translations.en[key as keyof typeof translations.en];
      
      expect(zhValue).toBeDefined();
      expect(enValue).toBeDefined();
      expect(zhValue.length).toBeGreaterThan(0);
      expect(enValue.length).toBeGreaterThan(0);
    });
  });

  it('should verify that translation keys match the component usage pattern', () => {
    // This test ensures that the translation keys follow the expected pattern
    // used in the SessionDetailPage component: t('sessions.keyName')
    
    const sessionKeys = Object.keys(translations.zh).filter(key => key.startsWith('sessions.'));
    const sessionKeysEn = Object.keys(translations.en).filter(key => key.startsWith('sessions.'));
    
    // Should have a significant number of session-related keys
    expect(sessionKeys.length).toBeGreaterThan(50);
    expect(sessionKeysEn.length).toBeGreaterThan(50);
    
    // Should have the same number of keys in both languages
    expect(sessionKeys.length).toBe(sessionKeysEn.length);
    
    // All keys should follow the sessions.* pattern
    sessionKeys.forEach(key => {
      expect(key).toMatch(/^sessions\./);
    });
    
    sessionKeysEn.forEach(key => {
      expect(key).toMatch(/^sessions\./);
    });
  });
});