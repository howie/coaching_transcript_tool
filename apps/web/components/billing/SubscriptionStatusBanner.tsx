'use client'

import { useState, useEffect } from 'react'
import { 
  ExclamationTriangleIcon, 
  CheckCircleIcon, 
  XMarkIcon,
  CreditCardIcon,
  ClockIcon 
} from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'
import { apiClient } from '@/lib/api'

interface SubscriptionStatus {
  subscription?: {
    id: string
    plan_name: string
    status: string
    cancel_at_period_end: boolean
    cancellation_reason?: string
    current_period_end: string
    next_payment_date?: string
  }
  payment_method?: {
    card_last4: string
    card_brand: string
    auth_status: string
  }
  status: string
}

export function SubscriptionStatusBanner() {
  const { user } = useAuth()
  const { t } = useI18n()
  const [subscriptionStatus, setSubscriptionStatus] = useState<SubscriptionStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [dismissed, setDismissed] = useState(false)

  useEffect(() => {
    if (user) {
      loadSubscriptionStatus()
    }
  }, [user])

  const loadSubscriptionStatus = async () => {
    try {
      const data = await apiClient.get('/api/v1/subscriptions/current')
      setSubscriptionStatus(data)
    } catch (error) {
      console.error('Failed to load subscription status:', error)
    } finally {
      setLoading(false)
    }
  }

  const getDaysUntilExpiry = () => {
    if (!subscriptionStatus?.subscription?.current_period_end) return null
    
    const endDate = new Date(subscriptionStatus.subscription.current_period_end)
    const today = new Date()
    const timeDiff = endDate.getTime() - today.getTime()
    const daysDiff = Math.ceil(timeDiff / (1000 * 3600 * 24))
    
    return daysDiff
  }

  const getPlanDisplayName = (planId: string): string => {
    const planNames: Record<string, string> = {
      'FREE': t('billing.planNameFree'),
      'STUDENT': t('billing.planNameStudent'), 
      'PRO': t('billing.planNamePro'),
      'ENTERPRISE': t('billing.planNameEnterprise')
    }
    return planNames[planId.toUpperCase()] || planId
  }

  const parseDowngradeInfo = (cancellationReason: string): { planId: string; billingCycle: string } | null => {
    if (!cancellationReason?.startsWith('DOWNGRADE_TO:')) return null
    
    const parts = cancellationReason.split(':')
    if (parts.length !== 3) return null
    
    return {
      planId: parts[1],
      billingCycle: parts[2]
    }
  }

  const shouldShowBanner = () => {
    if (!subscriptionStatus || dismissed) return false

    // Show banner for various conditions
    const subscription = subscriptionStatus.subscription
    if (!subscription) return false

    // Past due subscription
    if (subscription.status === 'past_due') return true

    // Cancelled subscription
    if (subscription.cancel_at_period_end) return true

    // Subscription expiring soon (within 7 days)
    const daysUntilExpiry = getDaysUntilExpiry()
    if (daysUntilExpiry !== null && daysUntilExpiry <= 7 && daysUntilExpiry > 0) return true

    return false
  }

  const getBannerContent = () => {
    const subscription = subscriptionStatus?.subscription
    if (!subscription) return null

    const daysUntilExpiry = getDaysUntilExpiry()

    if (subscription.status === 'past_due') {
      return {
        type: 'error' as const,
        icon: <ExclamationTriangleIcon className="h-5 w-5" />,
        title: t('subscription.pastDueTitle'),
        message: t('subscription.pastDueMessage'),
        action: {
          text: t('subscription.updatePayment'),
          href: '/dashboard/billing?tab=payment'
        }
      }
    }

    if (subscription.cancel_at_period_end) {
      // Check if this is a downgrade or cancellation
      const downgradeInfo = parseDowngradeInfo(subscription.cancellation_reason || '')
      
      if (downgradeInfo) {
        // This is a plan downgrade
        const targetPlanName = getPlanDisplayName(downgradeInfo.planId)
        const endDate = new Date(subscription.current_period_end).toLocaleDateString()
        
        return {
          type: 'warning' as const,
          icon: <ClockIcon className="h-5 w-5" />,
          title: t('subscription.downgradingTitle'),
          message: downgradeInfo.planId === 'FREE' 
            ? t('subscription.downgradingToFreeMessage', { date: endDate })
            : t('subscription.downgradingMessage', { 
                date: endDate,
                planName: targetPlanName 
              }),
          action: {
            text: t('subscription.cancelPlanChange'),
            href: '/dashboard/billing?tab=payment'
          }
        }
      } else {
        // This is a regular cancellation
        return {
          type: 'warning' as const,
          icon: <ClockIcon className="h-5 w-5" />,
          title: t('subscription.cancelledTitle'),
          message: t('subscription.cancelledMessage', { 
            date: new Date(subscription.current_period_end).toLocaleDateString() 
          }),
          action: {
            text: t('billing.reactivateSubscription'),
            href: '/dashboard/billing?tab=payment'
          }
        }
      }
    }

    if (daysUntilExpiry !== null && daysUntilExpiry <= 7 && daysUntilExpiry > 0) {
      return {
        type: 'warning' as const,
        icon: <ClockIcon className="h-5 w-5" />,
        title: t('subscription.expiringTitle'),
        message: t('subscription.expiringMessage', { 
          days: daysUntilExpiry,
          date: new Date(subscription.current_period_end).toLocaleDateString() 
        }),
        action: {
          text: t('subscription.renewSubscription'),
          href: '/dashboard/billing?tab=plans'
        }
      }
    }

    return null
  }

  if (loading || !shouldShowBanner()) {
    return null
  }

  const bannerContent = getBannerContent()
  if (!bannerContent) return null

  const getBannerStyles = () => {
    switch (bannerContent.type) {
      case 'error':
        return 'bg-red-600 bg-opacity-10 border-red-600 text-red-400'
      case 'warning':
        return 'bg-yellow-600 bg-opacity-10 border-yellow-600 text-yellow-400'
      default:
        return 'bg-blue-600 bg-opacity-10 border-blue-600 text-blue-400'
    }
  }

  return (
    <div className={`border rounded-lg p-4 mb-6 ${getBannerStyles()}`}>
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-0.5">
          {bannerContent.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-sm font-semibold mb-1">
            {bannerContent.title}
          </h4>
          <p className="text-sm opacity-90 mb-3">
            {bannerContent.message}
          </p>
          <div className="flex items-center space-x-3">
            <button
              onClick={() => window.location.href = bannerContent.action.href}
              className="text-xs font-medium px-3 py-1.5 rounded-md bg-current bg-opacity-20 hover:bg-opacity-30 transition-colors"
            >
              {bannerContent.action.text}
            </button>
          </div>
        </div>
        <button
          onClick={() => setDismissed(true)}
          className="flex-shrink-0 ml-4 hover:opacity-70 transition-opacity"
        >
          <XMarkIcon className="h-5 w-5" />
        </button>
      </div>
    </div>
  )
}