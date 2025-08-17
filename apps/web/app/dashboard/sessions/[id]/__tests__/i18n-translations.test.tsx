import { translations } from '@/lib/i18n';

describe('Session Detail Page i18n Translations', () => {
  describe('Chinese translations', () => {
    it('should have all required session translation keys in Chinese', () => {
      const zh = translations.zh;
      
      // Basic session keys
      expect(zh['sessions.overview']).toBe('會談概覽');
      expect(zh['sessions.transcript']).toBe('逐字稿');
      expect(zh['sessions.aiAnalysis']).toBe('AI 分析');
      expect(zh['sessions.basicInfo']).toBe('基本資料');
      expect(zh['sessions.transcriptContent']).toBe('逐字稿內容');
      expect(zh['sessions.audioAnalysis']).toBe('音檔分析');
      
      // Export related keys
      expect(zh['sessions.exportFormat']).toBe('匯出格式:');
      expect(zh['sessions.exportTxt']).toBe('純文字 (.txt)');
      expect(zh['sessions.exportTranscript']).toBe('匯出逐字稿');
      
      // Speaking stats keys
      expect(zh['sessions.talkAnalysisResults']).toBe('談話分析結果');
      expect(zh['sessions.talkTimeDistribution']).toBe('談話時間分配');
      expect(zh['sessions.overallStats']).toBe('整體統計');
      expect(zh['sessions.totalDuration']).toBe('總時長');
      expect(zh['sessions.talkTime']).toBe('談話時間');
      expect(zh['sessions.silenceTime']).toBe('靜默時間');
      expect(zh['sessions.conversationSegments']).toBe('對話段數');
      
      // AI Analysis keys
      expect(zh['sessions.sessionSummary']).toBe('會談摘要');
      expect(zh['sessions.generateSummary']).toBe('產生摘要');
      expect(zh['sessions.aiChat']).toBe('AI 對話');
      expect(zh['sessions.generating']).toBe('產生中...');
      
      // Upload method keys
      expect(zh['sessions.selectUploadMethod']).toBe('請選擇上傳方式：');
      expect(zh['sessions.audioAnalysisTitle']).toBe('音檔分析');
      expect(zh['sessions.directUploadTitle']).toBe('直接上傳逐字稿');
      
      // Status and message keys
      expect(zh['sessions.noTranscriptUploaded']).toBe('此諮詢記錄尚未上傳音檔或逐字稿');
      expect(zh['sessions.processing']).toBe('處理中');
      expect(zh['sessions.processingCompleted']).toBe('已完成');
      expect(zh['sessions.comingSoon']).toBe('即將推出');
    });
  });

  describe('English translations', () => {
    it('should have all required session translation keys in English', () => {
      const en = translations.en;
      
      // Basic session keys
      expect(en['sessions.overview']).toBe('Overview');
      expect(en['sessions.transcript']).toBe('Transcript');
      expect(en['sessions.aiAnalysis']).toBe('AI Analysis');
      expect(en['sessions.basicInfo']).toBe('Basic Information');
      expect(en['sessions.transcriptContent']).toBe('Transcript Content');
      expect(en['sessions.audioAnalysis']).toBe('Audio Analysis');
      
      // Export related keys
      expect(en['sessions.exportFormat']).toBe('Export Format');
      expect(en['sessions.exportTxt']).toBe('Plain Text (.txt)');
      expect(en['sessions.exportTranscript']).toBe('Export Transcript');
      
      // Speaking stats keys
      expect(en['sessions.talkAnalysisResults']).toBe('Talk Analysis Results');
      expect(en['sessions.talkTimeDistribution']).toBe('Talk Time Distribution');
      expect(en['sessions.overallStats']).toBe('Overall Statistics');
      expect(en['sessions.totalDuration']).toBe('Total Duration');
      expect(en['sessions.talkTime']).toBe('Talk Time');
      expect(en['sessions.silenceTime']).toBe('Silence Time');
      expect(en['sessions.conversationSegments']).toBe('Conversation Segments');
      
      // AI Analysis keys
      expect(en['sessions.sessionSummary']).toBe('Session Summary');
      expect(en['sessions.generateSummary']).toBe('Generate Summary');
      expect(en['sessions.aiChat']).toBe('AI Chat');
      expect(en['sessions.generating']).toBe('Generating...');
      
      // Upload method keys
      expect(en['sessions.selectUploadMethod']).toBe('Please select upload method:');
      expect(en['sessions.audioAnalysisTitle']).toBe('Audio Analysis');
      expect(en['sessions.directUploadTitle']).toBe('Direct Upload Transcript');
      
      // Status and message keys
      expect(en['sessions.noTranscriptUploaded']).toBe('This consultation record has not uploaded audio or transcript file yet');
      expect(en['sessions.processing']).toBe('Processing');
      expect(en['sessions.processingCompleted']).toBe('Completed');
      expect(en['sessions.comingSoon']).toBe('Coming Soon');
    });
  });

  describe('Translation consistency', () => {
    it('should have matching keys for Chinese and English', () => {
      const zhKeys = Object.keys(translations.zh).filter(key => key.startsWith('sessions.'));
      const enKeys = Object.keys(translations.en).filter(key => key.startsWith('sessions.'));
      
      // Check that all Chinese session keys have English equivalents
      zhKeys.forEach(key => {
        expect(enKeys).toContain(key);
        expect(translations.en[key as keyof typeof translations.en]).toBeDefined();
        expect(translations.en[key as keyof typeof translations.en]).not.toBe('');
      });
      
      // Check that all English session keys have Chinese equivalents
      enKeys.forEach(key => {
        expect(zhKeys).toContain(key);
        expect(translations.zh[key as keyof typeof translations.zh]).toBeDefined();
        expect(translations.zh[key as keyof typeof translations.zh]).not.toBe('');
      });
    });

    it('should have specific interpolation keys working correctly', () => {
      // Test keys with parameter interpolation
      const zhParameterKeys = [
        'sessions.uploadSuccess',
        'sessions.segmentsCount', 
        'sessions.detectSpeakersMessage',
        'sessions.conversationSummary',
        'sessions.conversionStatus',
        'sessions.conversionId',
      ];

      const enParameterKeys = [
        'sessions.uploadSuccess',
        'sessions.segmentsCount',
        'sessions.detectSpeakersMessage', 
        'sessions.conversationSummary',
        'sessions.conversionStatus',
        'sessions.conversionId',
      ];

      zhParameterKeys.forEach(key => {
        expect(translations.zh[key as keyof typeof translations.zh]).toBeDefined();
        expect(translations.zh[key as keyof typeof translations.zh]).toContain('{');
      });

      enParameterKeys.forEach(key => {
        expect(translations.en[key as keyof typeof translations.en]).toBeDefined();
        expect(translations.en[key as keyof typeof translations.en]).toContain('{');
      });
    });
  });
});