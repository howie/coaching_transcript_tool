/**
 * Test i18n error message functionality
 */

import { render, screen } from '@testing-library/react'
import { I18nProvider } from '@/contexts/i18n-context'
import { translations } from '@/lib/translations'

// Mock API client with error simulation
class MockApiClient {
  private translateFn?: (key: string, params?: Record<string, any>) => string

  setTranslationFunction(t: (key: string, params?: Record<string, any>) => string) {
    this.translateFn = t
  }

  // Copy of parseErrorMessage function for testing
  parseErrorMessage(errorData: any, defaultMessage: string): string {
    const t = this.translateFn
    
    if (errorData.detail && typeof errorData.detail === 'object') {
      const baseMessage = errorData.detail.message || errorData.detail.error || defaultMessage
      
      // Add helpful context for plan limit errors with i18n
      if (t && (errorData.detail.error === 'session_limit_exceeded' || 
                errorData.detail.error === 'transcription_limit_exceeded' ||
                errorData.detail.error === 'file_size_exceeded')) {
        
        // Get localized plan name
        const planKey = errorData.detail.plan === 'free' ? 'errors.planFree' :
                       errorData.detail.plan === 'pro' ? 'errors.planPro' :
                       errorData.detail.plan === 'business' ? 'errors.planBusiness' :
                       errorData.detail.plan?.toUpperCase()
        
        const planName = planKey?.startsWith('errors.') ? t(planKey) : planKey
        
        // Use appropriate i18n message based on error type
        if (errorData.detail.error === 'session_limit_exceeded') {
          return t('errors.sessionLimitExceededWithPlan', {
            limit: errorData.detail.limit || errorData.detail.current_usage,
            plan: planName
          })
        } else if (errorData.detail.error === 'transcription_limit_exceeded') {
          return t('errors.transcriptionLimitExceededWithPlan', {
            limit: errorData.detail.limit || errorData.detail.current_usage,
            plan: planName
          })
        } else if (errorData.detail.error === 'file_size_exceeded') {
          return t('errors.fileSizeExceededWithPlan', {
            fileSize: errorData.detail.file_size_mb,
            limit: errorData.detail.limit_mb,
            plan: planName
          })
        }
      }
      
      // Fallback to original logic
      if (errorData.detail.error === 'session_limit_exceeded' || 
          errorData.detail.error === 'transcription_limit_exceeded' ||
          errorData.detail.error === 'file_size_exceeded') {
        const planType = errorData.detail.plan === 'free' ? 'FREE' : errorData.detail.plan?.toUpperCase()
        return `${baseMessage}${planType ? ` (${planType} plan)` : ''}. Consider upgrading your plan for higher limits.`
      }
      
      return baseMessage
    }
    return defaultMessage
  }
}

// Test component that displays error messages
function ErrorDisplay({ error }: { error: any }) {
  return <div data-testid="error-message">{error}</div>
}

describe('API Error Message i18n', () => {
  let mockApiClient: MockApiClient

  beforeEach(() => {
    mockApiClient = new MockApiClient()
  })

  describe('English translations', () => {
    const TestComponent = ({ errorData }: { errorData: any }) => {
      return (
        <I18nProvider>
          <TestWrapper errorData={errorData} />
        </I18nProvider>
      )
    }

    const TestWrapper = ({ errorData }: { errorData: any }) => {
      const t = (key: string, params?: Record<string, any>) => {
        let translation = translations.en[key] || key
        if (params) {
          Object.entries(params).forEach(([paramKey, value]) => {
            translation = translation.replace(`{${paramKey}}`, String(value))
          })
        }
        return translation
      }

      mockApiClient.setTranslationFunction(t)
      const errorMessage = mockApiClient.parseErrorMessage(errorData, 'Default error')
      
      return <ErrorDisplay error={errorMessage} />
    }

    it('should display English session limit exceeded message', () => {
      const errorData = {
        detail: {
          error: 'session_limit_exceeded',
          limit: 3,
          current_usage: 3,
          plan: 'free'
        }
      }

      render(<TestComponent errorData={errorData} />)
      
      const errorMessage = screen.getByTestId('error-message')
      expect(errorMessage.textContent).toBe(
        'You have reached your monthly session limit of 3 (FREE plan). Consider upgrading your plan for higher limits.'
      )
    })

    it('should display English file size exceeded message', () => {
      const errorData = {
        detail: {
          error: 'file_size_exceeded',
          file_size_mb: 50,
          limit_mb: 25,
          plan: 'free'
        }
      }

      render(<TestComponent errorData={errorData} />)
      
      const errorMessage = screen.getByTestId('error-message')
      expect(errorMessage.textContent).toBe(
        'File size 50MB exceeds FREE plan limit of 25MB. Consider upgrading your plan for larger file limits.'
      )
    })

    it('should display English transcription limit exceeded message', () => {
      const errorData = {
        detail: {
          error: 'transcription_limit_exceeded',
          limit: 5,
          current_usage: 5,
          plan: 'pro'
        }
      }

      render(<TestComponent errorData={errorData} />)
      
      const errorMessage = screen.getByTestId('error-message')
      expect(errorMessage.textContent).toBe(
        'You have reached your monthly transcription limit of 5 (PRO plan). Consider upgrading your plan for higher limits.'
      )
    })
  })

  describe('Chinese translations', () => {
    const TestComponent = ({ errorData }: { errorData: any }) => {
      return (
        <I18nProvider>
          <TestWrapper errorData={errorData} />
        </I18nProvider>
      )
    }

    const TestWrapper = ({ errorData }: { errorData: any }) => {
      const t = (key: string, params?: Record<string, any>) => {
        let translation = translations.zh[key] || key
        if (params) {
          Object.entries(params).forEach(([paramKey, value]) => {
            translation = translation.replace(`{${paramKey}}`, String(value))
          })
        }
        return translation
      }

      mockApiClient.setTranslationFunction(t)
      const errorMessage = mockApiClient.parseErrorMessage(errorData, '預設錯誤')
      
      return <ErrorDisplay error={errorMessage} />
    }

    it('should display Chinese session limit exceeded message', () => {
      const errorData = {
        detail: {
          error: 'session_limit_exceeded',
          limit: 3,
          current_usage: 3,
          plan: 'free'
        }
      }

      render(<TestComponent errorData={errorData} />)
      
      const errorMessage = screen.getByTestId('error-message')
      expect(errorMessage.textContent).toBe(
        '您已達到每月會談數限制 3 次（免費 方案）。考慮升級方案以獲得更高限制。'
      )
    })

    it('should display Chinese file size exceeded message', () => {
      const errorData = {
        detail: {
          error: 'file_size_exceeded',
          file_size_mb: 50,
          limit_mb: 25,
          plan: 'free'
        }
      }

      render(<TestComponent errorData={errorData} />)
      
      const errorMessage = screen.getByTestId('error-message')
      expect(errorMessage.textContent).toBe(
        '檔案大小 50MB 超過 免費 方案限制 25MB。考慮升級方案以獲得更大檔案限制。'
      )
    })

    it('should display Chinese transcription limit exceeded message', () => {
      const errorData = {
        detail: {
          error: 'transcription_limit_exceeded',
          limit: 5,
          current_usage: 5,
          plan: 'pro'
        }
      }

      render(<TestComponent errorData={errorData} />)
      
      const errorMessage = screen.getByTestId('error-message')
      expect(errorMessage.textContent).toBe(
        '您已達到每月轉錄數限制 5 次（專業版 方案）。考慮升級方案以獲得更高限制。'
      )
    })
  })

  describe('Fallback behavior', () => {
    it('should fallback to English when no translation function is provided', () => {
      const errorData = {
        detail: {
          error: 'session_limit_exceeded',
          limit: 3,
          current_usage: 3,
          plan: 'free'
        }
      }

      const errorMessage = mockApiClient.parseErrorMessage(errorData, 'Default error')
      
      expect(errorMessage).toBe(
        'session_limit_exceeded (FREE plan). Consider upgrading your plan for higher limits.'
      )
    })
  })
})