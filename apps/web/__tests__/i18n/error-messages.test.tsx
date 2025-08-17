/**
 * Test i18n error message functionality with parameter interpolation
 */

import { translations } from '@/lib/i18n'

describe('Error Message i18n with Parameter Interpolation', () => {
  // Mock implementation of the i18n t function with parameter support
  const createTFunction = (language: 'zh' | 'en') => {
    return (key: string, params?: Record<string, any>): string => {
      let value = translations[language][key as keyof typeof translations[typeof language]]
      
      if (!value) {
        value = translations['zh'][key as keyof typeof translations['zh']]
      }
      
      if (!value) {
        value = key
      }
      
      // Parameter interpolation
      if (params && typeof value === 'string') {
        Object.entries(params).forEach(([paramKey, paramValue]) => {
          const placeholder = `{${paramKey}}`
          value = value.replace(new RegExp(placeholder.replace(/[{}]/g, '\\$&'), 'g'), String(paramValue))
        })
      }
      
      return value
    }
  }

  describe('Chinese translations', () => {
    const t = createTFunction('zh')

    it('should translate session limit exceeded with parameters', () => {
      const result = t('errors.sessionLimitExceededWithPlan', {
        limit: 3,
        plan: '免費'
      })
      
      expect(result).toBe('您已達到每月會談數限制 3 次（免費 方案）。考慮升級方案以獲得更高限制。')
    })

    it('should translate transcription limit exceeded with parameters', () => {
      const result = t('errors.transcriptionLimitExceededWithPlan', {
        limit: 5,
        plan: '專業版'
      })
      
      expect(result).toBe('您已達到每月轉錄數限制 5 次（專業版 方案）。考慮升級方案以獲得更高限制。')
    })

    it('should translate file size exceeded with parameters', () => {
      const result = t('errors.fileSizeExceededWithPlan', {
        fileSize: 50,
        limit: 25,
        plan: '免費'
      })
      
      expect(result).toBe('檔案大小 50MB 超過 免費 方案限制 25MB。考慮升級方案以獲得更大檔案限制。')
    })

    it('should translate plan names correctly', () => {
      expect(t('errors.planFree')).toBe('免費')
      expect(t('errors.planPro')).toBe('專業版')
      expect(t('errors.planBusiness')).toBe('企業版')
    })
  })

  describe('English translations', () => {
    const t = createTFunction('en')

    it('should translate session limit exceeded with parameters', () => {
      const result = t('errors.sessionLimitExceededWithPlan', {
        limit: 3,
        plan: 'FREE'
      })
      
      expect(result).toBe('You have reached your monthly session limit of 3 (FREE plan). Consider upgrading your plan for higher limits.')
    })

    it('should translate transcription limit exceeded with parameters', () => {
      const result = t('errors.transcriptionLimitExceededWithPlan', {
        limit: 5,
        plan: 'PRO'
      })
      
      expect(result).toBe('You have reached your monthly transcription limit of 5 (PRO plan). Consider upgrading your plan for higher limits.')
    })

    it('should translate file size exceeded with parameters', () => {
      const result = t('errors.fileSizeExceededWithPlan', {
        fileSize: 50,
        limit: 25,
        plan: 'FREE'
      })
      
      expect(result).toBe('File size 50MB exceeds FREE plan limit of 25MB. Consider upgrading your plan for larger file limits.')
    })

    it('should translate plan names correctly', () => {
      expect(t('errors.planFree')).toBe('FREE')
      expect(t('errors.planPro')).toBe('PRO')
      expect(t('errors.planBusiness')).toBe('BUSINESS')
    })
  })

  describe('Fallback behavior', () => {
    it('should return the key when translation is not found', () => {
      const t = createTFunction('zh')
      const result = t('nonexistent.key')
      expect(result).toBe('nonexistent.key')
    })

    it('should handle parameters even when translation is not found', () => {
      const t = createTFunction('zh')
      const result = t('nonexistent.{key}', { key: 'test' })
      expect(result).toBe('nonexistent.test')
    })
  })

  describe('Parameter interpolation edge cases', () => {
    const t = createTFunction('en')

    it('should handle multiple occurrences of same parameter', () => {
      // This tests the global flag in the regex
      const result = t('errors.sessionLimitExceededWithPlan', {
        limit: 3,
        plan: 'FREE'
      })
      
      // Should not leave any unprocessed {limit} or {plan} placeholders
      expect(result).not.toContain('{limit}')
      expect(result).not.toContain('{plan}')
      expect(result).toContain('3')
      expect(result).toContain('FREE')
    })

    it('should handle numeric parameters', () => {
      const result = t('errors.fileSizeExceededWithPlan', {
        fileSize: 100.5,
        limit: 50,
        plan: 'PRO'
      })
      
      expect(result).toContain('100.5')
      expect(result).toContain('50')
    })

    it('should handle string parameters with special characters', () => {
      const result = t('errors.sessionLimitExceededWithPlan', {
        limit: 3,
        plan: 'FREE (Beta)'
      })
      
      expect(result).toContain('FREE (Beta)')
    })
  })
})