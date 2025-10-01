'use client'

import { useState, useEffect } from 'react'
import { useI18n } from '@/contexts/i18n-context'
import { XMarkIcon, ShieldCheckIcon } from '@heroicons/react/24/outline'
import { trackDashboard } from '@/lib/analytics'

export function PrivacyNotice() {
  const { t } = useI18n()
  const [isVisible, setIsVisible] = useState(true)

  // Check localStorage on mount to see if user has dismissed the notice
  useEffect(() => {
    const dismissed = localStorage.getItem('privacy_notice_dismissed')
    if (dismissed === 'true') {
      setIsVisible(false)
    } else {
      // Track privacy notice view
      trackDashboard.privacyNoticeView()
    }
  }, [])

  const handleDismiss = () => {
    setIsVisible(false)
    localStorage.setItem('privacy_notice_dismissed', 'true')
  }

  if (!isVisible) {
    return null
  }

  return (
    <div className="mb-8">
      <div className="relative bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-6 shadow-sm">
        {/* Close button */}
        <button
          onClick={handleDismiss}
          className="absolute top-4 right-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
          aria-label="Close privacy notice"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>

        {/* Header with icon */}
        <div className="flex items-start space-x-3 mb-4">
          <ShieldCheckIcon className="h-6 w-6 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('dashboard.privacy.title')}
          </h3>
        </div>

        {/* Content */}
        <div className="ml-9 space-y-3">
          <div className="flex items-start space-x-2">
            <span className="text-blue-600 dark:text-blue-400 mt-1">•</span>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {t('dashboard.privacy.audio_processing')}
            </p>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-blue-600 dark:text-blue-400 mt-1">•</span>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {t('dashboard.privacy.transcript_management')}
            </p>
          </div>
          <div className="flex items-start space-x-2">
            <span className="text-blue-600 dark:text-blue-400 mt-1">•</span>
            <p className="text-sm text-gray-700 dark:text-gray-300">
              {t('dashboard.privacy.record_retention')}
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}