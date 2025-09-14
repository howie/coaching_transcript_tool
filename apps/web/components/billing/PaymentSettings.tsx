'use client'

import { useState, useEffect } from 'react'
import { 
  CreditCardIcon, 
  CalendarIcon, 
  DocumentTextIcon,
  BellIcon,
  CheckIcon,
  XMarkIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { apiClient } from '@/lib/api'

interface SubscriptionData {
  subscription?: {
    id: string
    plan_id: string
    plan_name: string
    billing_cycle: string
    amount: number
    currency: string
    status: string
    current_period_start: string
    current_period_end: string
    cancel_at_period_end: boolean
    cancellation_reason?: string
    next_payment_date?: string
  }
  payment_method?: {
    card_last4: string
    card_brand: string
    auth_status: string
  }
  status: string
}

export function PaymentSettings() {
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const [loading, setLoading] = useState(true)
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    loadSubscriptionData()
  }, [])

  const loadSubscriptionData = async () => {
    try {
      const data = await apiClient.get('/api/v1/subscriptions/current')
      setSubscriptionData(data)
      console.log('Subscription data loaded:', data) // Debug log
    } catch (error) {
      console.error('Failed to load subscription data:', error)
      // Set empty state on error to show "no subscription" message
      setSubscriptionData({ status: 'no_subscription' })
    } finally {
      setLoading(false)
    }
  }

  const handleCancelSubscription = async () => {
    if (!subscriptionData?.subscription?.id || actionLoading) return

    setActionLoading(true)
    try {
      await apiClient.post(`/api/v1/subscriptions/cancel/${subscriptionData.subscription.id}`)
      await loadSubscriptionData() // Refresh data
      console.log('Subscription cancelled successfully')
    } catch (error) {
      console.error('Error cancelling subscription:', error)
    } finally {
      setActionLoading(false)
    }
  }

  const handleReactivateSubscription = async () => {
    if (!subscriptionData?.subscription?.id || actionLoading) return

    setActionLoading(true)
    try {
      await apiClient.post(`/api/v1/subscriptions/reactivate/${subscriptionData.subscription.id}`)
      await loadSubscriptionData() // Refresh data
      console.log('Subscription reactivated successfully')
    } catch (error) {
      console.error('Error reactivating subscription:', error)
    } finally {
      setActionLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-dashboard-accent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Payment Settings Header */}
      <div className="flex items-center space-x-3">
        <h2 className={`text-xl font-semibold ${themeClasses.textPrimary}`}>
          {t('billing.paymentSettings')}
        </h2>
        {subscriptionData?.status === 'no_subscription' && (
          <span className="px-2 py-1 bg-gray-500 bg-opacity-20 text-gray-400 rounded-full text-xs font-medium">
            {t('billing.noActiveSubscription')}
          </span>
        )}
      </div>

      {/* Current Subscription */}
      {subscriptionData?.subscription && (
        <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
          <div className="flex items-center space-x-3 mb-6">
            <DocumentTextIcon className="h-6 w-6 text-dashboard-accent" />
            <h3 className="text-lg font-semibold" style={{color: 'var(--text-primary)'}}>
              {t('billing.currentSubscription')}
            </h3>
          </div>
          
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                <h4 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>
                  {subscriptionData.subscription.plan_name}
                </h4>
                <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>
                  NT${(subscriptionData.subscription.amount / 100).toLocaleString()} / {subscriptionData.subscription.billing_cycle}
                </p>
              </div>
              <div className="p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                <h4 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>
                  {t('billing.status')}
                </h4>
                <div className="flex items-center space-x-2">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    subscriptionData.subscription.status === 'active' 
                      ? 'bg-green-600 bg-opacity-20 text-green-400'
                      : subscriptionData.subscription.status === 'past_due'
                      ? 'bg-yellow-600 bg-opacity-20 text-yellow-400'
                      : 'bg-red-600 bg-opacity-20 text-red-400'
                  }`}>
                    {subscriptionData.subscription.status}
                  </span>
                  {subscriptionData.subscription.cancel_at_period_end && (
                    <span className="px-2 py-1 bg-orange-600 bg-opacity-20 text-orange-400 rounded-full text-xs font-medium">
                      {t('billing.cancellingAtPeriodEnd')}
                    </span>
                  )}
                </div>
              </div>
            </div>

            {subscriptionData.subscription.next_payment_date && (
              <div className="p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                <h4 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>
                  {t('billing.nextPayment')}
                </h4>
                <p className="text-sm" style={{color: 'var(--text-secondary)'}}>
                  {new Date(subscriptionData.subscription.next_payment_date).toLocaleDateString()}
                </p>
              </div>
            )}

            <div className="flex space-x-4">
              {subscriptionData.subscription.cancel_at_period_end ? (
                <button
                  onClick={handleReactivateSubscription}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading ? t('billing.processing') : t('billing.reactivateSubscription')}
                </button>
              ) : (
                <button
                  onClick={handleCancelSubscription}
                  disabled={actionLoading}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {actionLoading ? t('billing.processing') : t('billing.cancelSubscription')}
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Payment Method */}
      {subscriptionData?.payment_method && (
        <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
          <div className="flex items-center space-x-3 mb-6">
            <CreditCardIcon className="h-6 w-6 text-dashboard-accent" />
            <h3 className="text-lg font-semibold" style={{color: 'var(--text-primary)'}}>
              {t('billing.paymentMethod')}
            </h3>
          </div>
          
          <div className="space-y-4">
            <div className="p-4 rounded-lg flex items-center justify-between" style={{backgroundColor: 'var(--card-bg)'}}>
              <div className="flex items-center space-x-4">
                <div className={`w-12 h-8 rounded flex items-center justify-center ${
                  subscriptionData.payment_method.card_brand === 'VISA' 
                    ? 'bg-gradient-to-r from-blue-600 to-blue-400'
                    : subscriptionData.payment_method.card_brand === 'MASTERCARD'
                    ? 'bg-gradient-to-r from-red-600 to-red-400'
                    : 'bg-gradient-to-r from-gray-600 to-gray-400'
                }`}>
                  <span className="text-white text-xs font-bold">
                    {subscriptionData.payment_method.card_brand || 'CARD'}
                  </span>
                </div>
                <div>
                  <p className="font-medium" style={{color: 'var(--text-primary)'}}>
                    {t('billing.cardEnding')} {subscriptionData.payment_method.card_last4}
                  </p>
                  <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>
                    {t('billing.authStatus')}: {subscriptionData.payment_method.auth_status}
                  </p>
                </div>
              </div>
              <span className="px-3 py-1 bg-green-600 bg-opacity-20 text-green-400 rounded-full text-sm font-medium">
                {t('billing.authorized')}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* No Subscription Message */}
      {(!subscriptionData || subscriptionData?.status === 'no_subscription') && (
        <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20 text-center">
          <ExclamationTriangleIcon className="h-12 w-12 text-yellow-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2" style={{color: 'var(--text-primary)'}}>
            {t('billing.noActiveSubscription')}
          </h3>
          <p className="text-sm mb-4" style={{color: 'var(--text-tertiary)'}}>
            {t('billing.noSubscriptionDescription')}
          </p>
          <div className="space-y-4">
            <button
              onClick={() => window.location.href = '/dashboard/billing?tab=plans'}
              className="px-6 py-3 bg-dashboard-accent text-white rounded-lg hover:bg-opacity-90 transition-colors"
            >
              {t('billing.viewPlans')}
            </button>
            
            {/* Test Subscription Data Button for Development */}
            <div className="border-t pt-4 mt-4">
              <p className="text-xs text-gray-500 mb-2">測試功能 (開發用)</p>
              <button
                onClick={() => setSubscriptionData({
                  subscription: {
                    id: '550e8400-e29b-41d4-a716-446655440000', // Valid UUID for testing
                    plan_id: 'PRO',
                    plan_name: '專業方案',
                    billing_cycle: 'monthly',
                    amount: 89900,
                    currency: 'TWD',
                    status: 'active',
                    current_period_start: '2025-01-01',
                    current_period_end: '2025-02-01',
                    cancel_at_period_end: false,
                    next_payment_date: '2025-02-01'
                  },
                  payment_method: {
                    card_last4: '4242',
                    card_brand: 'VISA',
                    auth_status: 'active'
                  },
                  status: 'active'
                })}
                className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors text-sm"
              >
                模擬訂閱資料
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  )
}