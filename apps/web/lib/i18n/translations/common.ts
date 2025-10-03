// Common/shared UI translations
export const commonTranslations = {
  zh: {
    'common.save': '儲存',
    'common.saving': '儲存中...',
    'common.loading': '載入中...',
    'common.cancel': '取消',
    'common.back': '返回',
    'common.edit': '編輯',
    'common.delete': '刪除',
    'common.updating': '更新中...',
    'common.confirmDelete': '確認刪除',
    'common.create': '建立',
    'common.creating': '建立中...',
    'common.createdAt': '建立時間',
    'common.updatedAt': '更新時間',
    'common.enterTagHint': '輸入後按 Enter 新增標籤',
    'common.note': '注意：',
    'common.noData': '無數據',
    'common.error': '錯誤',
    'common.failedToLoadData': '無法載入真實使用數據，顯示範例數據',

    // Error Messages with Plan Context
    'errors.sessionLimitExceededWithPlan': '您已達到每月會談數限制 {limit} 次（{plan} 方案）。考慮升級方案以獲得更高限制。',
    'errors.transcriptionLimitExceededWithPlan': '您已達到每月轉錄數限制 {limit} 次（{plan} 方案）。考慮升級方案以獲得更高限制。',
    'errors.fileSizeExceededWithPlan': '檔案大小 {fileSize}MB 超過 {plan} 方案限制 {limit}MB。考慮升級方案以獲得更大檔案限制。',
    'errors.planFree': '免費',
    'errors.planPro': '專業版',
    'errors.planBusiness': '企業版',
    'errors.considerUpgrade': '考慮升級方案以獲得更高限制。',
    
    // Usage Limits
    'limits.usageLimitReached': '使用量已達上限',
    'limits.sessionLimitReached': '您本月的會談數已達到方案上限',
    'limits.transcriptionLimitReached': '您本月的轉錄數已達到方案上限',
    'limits.minutesLimitReached': '您本月的音檔分鐘數已達到方案上限',
    'limits.sessions': '會談數',
    'limits.transcriptions': '轉錄數',
    'limits.minutes': '音檔分鐘數',
    'limits.upgradeNow': '立即升級',
    'limits.viewUsage': '查看使用量',
    
    // Feature Cards
    'feature.converter.title': 'Transcript Converter',
    'feature.converter.desc': '將您的教練對話逐字稿從 VTT 或 SRT 格式轉換為結構化的 Excel 檔案，便於分析和檢視。',
    'feature.converter.btn': '上傳逐字稿',
    'feature.analysis.title': '教練技巧分析',
    'feature.analysis.desc': '自動識別和分析您教練對話中的核心技巧和互動模式，提升專業水準。',
    'feature.insights.title': '你的 AI 督導',
    'feature.insights.desc': '透過 AI 深度分析獲得見解和建議，改善您的教練效能和客戶體驗。',
    
    // Coming Soon
    'coming_soon.message': '🚧 此功能即將推出，敬請期待！',
  },
  en: {
    'common.save': 'Save',
    'common.saving': 'Saving...',
    'common.loading': 'Loading...',
    'common.cancel': 'Cancel',
    'common.back': 'Back',
    'common.edit': 'Edit',
    'common.delete': 'Delete',
    'common.updating': 'Updating...',
    'common.confirmDelete': 'Confirm Delete',
    'common.create': 'Create',
    'common.creating': 'Creating...',
    'common.createdAt': 'Created At',
    'common.updatedAt': 'Updated At',
    'common.enterTagHint': 'Enter tag and press Enter to add',
    'common.note': 'Note:',
    'common.noData': 'No Data',
    'common.error': 'Error',
    'common.failedToLoadData': 'Failed to load real usage data, showing sample data',

    // Error Messages with Plan Context
    'errors.sessionLimitExceededWithPlan': 'You have reached your monthly session limit of {limit} ({plan} plan). Consider upgrading your plan for higher limits.',
    'errors.transcriptionLimitExceededWithPlan': 'You have reached your monthly transcription limit of {limit} ({plan} plan). Consider upgrading your plan for higher limits.',
    'errors.fileSizeExceededWithPlan': 'File size {fileSize}MB exceeds {plan} plan limit of {limit}MB. Consider upgrading your plan for larger file limits.',
    'errors.planFree': 'FREE',
    'errors.planPro': 'PRO',
    'errors.planBusiness': 'BUSINESS',
    'errors.considerUpgrade': 'Consider upgrading your plan for higher limits.',
    
    // Usage Limits
    'limits.usageLimitReached': 'Usage Limit Reached',
    'limits.sessionLimitReached': 'You have reached your monthly session limit',
    'limits.transcriptionLimitReached': 'You have reached your monthly transcription limit',
    'limits.minutesLimitReached': 'You have reached your monthly audio minutes limit',
    'limits.sessions': 'Sessions',
    'limits.transcriptions': 'Transcriptions',
    'limits.minutes': 'Audio Minutes',
    'limits.upgradeNow': 'Upgrade Now',
    'limits.viewUsage': 'View Usage',
    
    // Feature Cards
    'feature.converter.title': 'Transcript Converter',
    'feature.converter.desc': 'Convert your coaching session transcripts from VTT or SRT format to structured Excel files for analysis.',
    'feature.converter.btn': 'Upload Transcript',
    'feature.analysis.title': 'Coaching Skills Analysis',
    'feature.analysis.desc': 'Automatically identify and analyze coaching techniques and interaction patterns in your sessions.',
    'feature.insights.title': 'Your AI Supervisor',
    'feature.insights.desc': 'Get AI-powered insights and suggestions to improve your coaching effectiveness.',
    
    // Coming Soon
    'coming_soon.message': '🚧 This feature is coming soon. Stay tuned!',
  }
}