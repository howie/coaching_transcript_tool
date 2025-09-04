'use client'

import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CheckCircleIcon, XCircleIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'
import { useThemeClasses } from '@/lib/theme-utils'

type PaymentResult = 'success' | 'failed' | 'pending' | 'processing'

export default function SubscriptionResultPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const [result, setResult] = useState<PaymentResult>('processing')
  const [message, setMessage] = useState('')
  const [subscriptionId, setSubscriptionId] = useState<string | null>(null)

  useEffect(() => {
    const checkPaymentResult = () => {
      // Get URL parameters from ECPay callback
      const rtnCode = searchParams.get('RtnCode')
      const rtnMsg = searchParams.get('RtnMsg')
      const merchantMemberId = searchParams.get('MerchantMemberID')
      
      if (rtnCode === '1') {
        setResult('success')
        setMessage(t('subscription.paymentSuccess'))
        
        // Set a timer to redirect to billing page
        setTimeout(() => {
          router.push('/dashboard/billing?tab=payment')
        }, 3000)
        
      } else if (rtnCode === '0' || rtnCode) {
        setResult('failed')
        setMessage(rtnMsg || t('subscription.paymentFailed'))
        
      } else {
        // No specific result yet, keep checking
        setResult('pending')
        setMessage(t('subscription.paymentProcessing'))
        
        // Poll for result if needed
        setTimeout(checkPaymentResult, 2000)
      }
    }

    checkPaymentResult()
  }, [searchParams, router, t])

  const getResultIcon = () => {
    switch (result) {
      case 'success':
        return <CheckCircleIcon className="h-16 w-16 text-green-500 mx-auto" />
      case 'failed':
        return <XCircleIcon className="h-16 w-16 text-red-500 mx-auto" />
      case 'pending':
        return <ExclamationTriangleIcon className="h-16 w-16 text-yellow-500 mx-auto" />
      default:
        return (
          <div className="animate-spin rounded-full h-16 w-16 border-t-2 border-b-2 border-dashboard-accent mx-auto"></div>
        )
    }
  }

  const getResultTitle = () => {
    switch (result) {
      case 'success':
        return t('subscription.successTitle')
      case 'failed':
        return t('subscription.failedTitle')
      case 'pending':
        return t('subscription.pendingTitle')
      default:
        return t('subscription.processingTitle')
    }
  }

  const getResultDescription = () => {
    switch (result) {
      case 'success':
        return t('subscription.successDescription')
      case 'failed':
        return t('subscription.failedDescription')
      case 'pending':
        return t('subscription.pendingDescription')
      default:
        return t('subscription.processingDescription')
    }
  }

  return (
    <div className={`min-h-screen ${themeClasses.dashboardBg} py-12`}>
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-dashboard-card rounded-lg p-8 border border-dashboard-accent border-opacity-20 text-center">
          {getResultIcon()}
          
          <h1 className={`text-3xl font-bold mt-6 mb-4 ${themeClasses.textPrimary}`}>
            {getResultTitle()}
          </h1>
          
          <p className={`text-lg mb-6 ${themeClasses.textSecondary}`}>
            {getResultDescription()}
          </p>

          {message && (
            <div className={`p-4 rounded-lg mb-6 ${
              result === 'success' 
                ? 'bg-green-600 bg-opacity-20 text-green-400'
                : result === 'failed'
                ? 'bg-red-600 bg-opacity-20 text-red-400'
                : 'bg-yellow-600 bg-opacity-20 text-yellow-400'
            }`}>
              <p className="text-sm">{message}</p>
            </div>
          )}

          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            {result === 'success' && (
              <button
                onClick={() => router.push('/dashboard/billing?tab=payment')}
                className="px-6 py-3 bg-dashboard-accent text-white rounded-lg hover:bg-opacity-90 transition-colors"
              >
                {t('subscription.viewSubscription')}
              </button>
            )}
            
            {result === 'failed' && (
              <button
                onClick={() => router.push('/dashboard/billing?tab=plans')}
                className="px-6 py-3 bg-dashboard-accent text-white rounded-lg hover:bg-opacity-90 transition-colors"
              >
                {t('subscription.tryAgain')}
              </button>
            )}
            
            <button
              onClick={() => router.push('/dashboard')}
              className={`px-6 py-3 border rounded-lg transition-colors ${themeClasses.buttonSecondary}`}
            >
              {t('subscription.returnToDashboard')}
            </button>
          </div>

          {result === 'success' && (
            <p className={`text-sm mt-4 ${themeClasses.textTertiary}`}>
              {t('subscription.redirectingIn')} 3 {t('subscription.seconds')}...
            </p>
          )}
        </div>
      </div>
    </div>
  )
}