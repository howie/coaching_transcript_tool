'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { 
  CreditCardIcon, 
  ClockIcon, 
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowPathIcon,
  XMarkIcon,
  PlusIcon,
  CalendarIcon
} from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { apiClient } from '@/lib/api'

interface Subscription {
  id: string
  plan_id: string
  plan_name: string
  billing_cycle: 'monthly' | 'annual'
  amount_twd: number
  status: 'active' | 'cancelled' | 'past_due' | 'unpaid'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  next_payment_date?: string
}

interface PaymentMethod {
  card_last4: string
  card_brand: string
  auth_status: string
}

interface SubscriptionData {
  subscription?: Subscription
  payment_method?: PaymentMethod
  status: 'no_subscription' | 'active' | 'cancelled' | 'past_due'
}

interface Payment {
  id: string
  amount: number
  currency: string
  status: 'success' | 'failed' | 'pending'
  period_start: string
  period_end: string
  processed_at?: string
  failure_reason?: string
}

export function SubscriptionDashboard() {
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const router = useRouter()
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null)
  const [billingHistory, setBillingHistory] = useState<Payment[]>([])
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState<string | null>(null)

  useEffect(() => {
    if (user) {
      loadSubscriptionData()
      loadBillingHistory()
    }
  }, [user])

  const loadSubscriptionData = async () => {
    try {
      const data = await apiClient.get('/api/v1/subscriptions/current')
      setSubscriptionData(data)
    } catch (error) {
      console.error('Failed to load subscription data:', error)
      setSubscriptionData({ status: 'no_subscription' })
    }
  }

  const loadBillingHistory = async () => {
    try {
      const data = await apiClient.get('/api/v1/subscriptions/billing-history')
      setBillingHistory(data.payments || [])
    } catch (error) {
      console.error('Failed to load billing history:', error)
      setBillingHistory([])
    } finally {
      setLoading(false)
    }
  }

  const handleCancelSubscription = async (immediate: boolean = false) => {
    if (!subscriptionData?.subscription) return

    const confirmMessage = immediate 
      ? '確定要立即取消訂閱嗎？您將立即失去進階功能的存取權限。'
      : '確定要在期末取消訂閱嗎？您可以使用進階功能直到當前計費週期結束。'

    if (!window.confirm(confirmMessage)) return

    setActionLoading('cancel')
    try {
      await apiClient.post('/api/v1/subscriptions/cancel', { 
        immediate,
        reason: '用戶主動取消' 
      })
      
      alert(immediate ? '訂閱已立即取消' : '訂閱將在期末取消')
      await loadSubscriptionData()
    } catch (error) {
      console.error('Failed to cancel subscription:', error)
      const errorMessage = error instanceof Error ? error.message : String(error)
      alert(`取消訂閱失敗: ${errorMessage}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleReactivateSubscription = async () => {
    if (!subscriptionData?.subscription) return

    if (!window.confirm('確定要重新啟用訂閱嗎？自動扣款將會恢復。')) return

    setActionLoading('reactivate')
    try {
      await apiClient.post('/api/v1/subscriptions/reactivate')
      alert('訂閱已重新啟用')
      await loadSubscriptionData()
    } catch (error) {
      console.error('Failed to reactivate subscription:', error)
      const errorMessage = error instanceof Error ? error.message : String(error)
      alert(`重新啟用失敗: ${errorMessage}`)
    } finally {
      setActionLoading(null)
    }
  }

  const handleUpgradePlan = () => {
    router.push('/dashboard/billing?tab=plans')
  }

  const handleUpdatePaymentMethod = () => {
    // Trigger ECPay re-authorization flow to update payment method
    const confirmed = window.confirm(
      '更新付款方式需要重新進行綠界 ECPay 授權流程。\n' +
      '您將被導向到綠界頁面進行新的信用卡授權。\n\n' +
      '確定要繼續嗎？'
    )
    
    if (confirmed) {
      // This would call backend API to initiate ECPay re-authorization
      alert('即將導向綠界授權頁面更新付款方式（功能開發中）')
    }
  }

  const formatTWD = (amount: number) => {
    return `NT$${(amount / 100).toLocaleString()}`
  }

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('zh-TW')
  }

  const getStatusBadge = (status: string) => {
    const statusConfig: Record<string, { color: string; bg: string; text: string }> = {
      active: { color: 'text-green-400', bg: 'bg-green-400/10', text: '使用中' },
      cancelled: { color: 'text-red-400', bg: 'bg-red-400/10', text: '已取消' },
      past_due: { color: 'text-yellow-400', bg: 'bg-yellow-400/10', text: '逾期' },
      unpaid: { color: 'text-red-400', bg: 'bg-red-400/10', text: '未付款' }
    }

    const config = statusConfig[status] || statusConfig.cancelled
    return (
      <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${config.color} ${config.bg}`}>
        {config.text}
      </span>
    )
  }

  const getPaymentStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-400" />
      case 'failed':
        return <XMarkIcon className="h-5 w-5 text-red-400" />
      case 'pending':
        return <ClockIcon className="h-5 w-5 text-yellow-400" />
      default:
        return <ClockIcon className="h-5 w-5 text-gray-400" />
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-dashboard-accent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Current Subscription Card */}
      <div className={`${themeClasses.card} p-6`}>
        <div className="flex items-center justify-between mb-6">
          <h2 className={`text-2xl font-bold ${themeClasses.textPrimary} flex items-center`}>
            <CreditCardIcon className="h-6 w-6 mr-2 text-dashboard-accent" />
            {t('billing.currentSubscription')}
          </h2>
          {subscriptionData?.subscription && (
            <div className="flex items-center space-x-2">
              {getStatusBadge(subscriptionData.subscription.status)}
            </div>
          )}
        </div>

        {subscriptionData?.status === 'no_subscription' ? (
          <div className="text-center py-12">
            <ExclamationTriangleIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-2`}>
              {t('billing.noActiveSubscription')}
            </h3>
            <p className={`text-sm ${themeClasses.textSecondary} mb-6`}>
              {t('billing.noSubscriptionDescription')}
            </p>
            <button
              onClick={handleUpgradePlan}
              className="bg-dashboard-accent text-white px-6 py-3 rounded-lg font-semibold hover:bg-opacity-90 transition-colors"
            >
              {t('billing.viewPlans')}
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Subscription Details */}
            <div>
              <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-4`}>方案詳情</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">方案名稱:</span>
                  <span className={`font-medium ${themeClasses.textPrimary}`}>
                    {subscriptionData?.subscription?.plan_name}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">計費週期:</span>
                  <span className={`font-medium ${themeClasses.textPrimary}`}>
                    {subscriptionData?.subscription?.billing_cycle === 'monthly' ? '月繳' : '年繳'}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">金額:</span>
                  <span className={`font-medium ${themeClasses.textPrimary}`}>
                    {subscriptionData?.subscription && formatTWD(subscriptionData.subscription.amount_twd)}
                  </span>
                </div>
                
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">當前週期:</span>
                  <span className={`font-medium ${themeClasses.textPrimary}`}>
                    {subscriptionData?.subscription && 
                      `${formatDate(subscriptionData.subscription.current_period_start)} - ${formatDate(subscriptionData.subscription.current_period_end)}`
                    }
                  </span>
                </div>
                
                {subscriptionData?.subscription?.next_payment_date && (
                  <div className="flex justify-between items-center">
                    <span className="text-gray-400">下次付款日期:</span>
                    <span className={`font-medium ${themeClasses.textPrimary} flex items-center`}>
                      <CalendarIcon className="h-4 w-4 mr-1" />
                      {formatDate(subscriptionData.subscription.next_payment_date)}
                    </span>
                  </div>
                )}

                {subscriptionData?.subscription?.cancel_at_period_end && (
                  <div className="p-3 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400 mr-2" />
                      <span className="text-sm text-yellow-400">
                        訂閱將於 {formatDate(subscriptionData.subscription.current_period_end)} 取消
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Payment Method */}
            <div>
              <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-4`}>付款方式</h3>
              {subscriptionData?.payment_method ? (
                <div className="space-y-4">
                  <div className="flex items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                    <CreditCardIcon className="h-8 w-8 text-gray-400 mr-3" />
                    <div className="flex-1">
                      <div className={`font-medium ${themeClasses.textPrimary}`}>
                        {subscriptionData.payment_method.card_brand} •••• {subscriptionData.payment_method.card_last4}
                      </div>
                      <div className="text-sm text-gray-400">
                        狀態: {subscriptionData.payment_method.auth_status === 'active' ? '已授權 (由綠界管理)' : '未授權'}
                      </div>
                    </div>
                  </div>
                  
                  <button
                    onClick={handleUpdatePaymentMethod}
                    className="w-full py-2 px-4 border border-gray-300 dark:border-gray-600 rounded-lg text-sm hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  >
                    重新授權付款方式 (綠界)
                  </button>
                </div>
              ) : (
                <div className="text-center py-6">
                  <CreditCardIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-400 text-sm mb-4">尚未進行綠界授權</p>
                  <button
                    onClick={handleUpdatePaymentMethod}
                    className="flex items-center mx-auto px-4 py-2 bg-dashboard-accent text-white rounded-lg text-sm hover:bg-opacity-90 transition-colors"
                  >
                    <PlusIcon className="h-4 w-4 mr-1" />
                    前往綠界授權付款
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Subscription Actions */}
        {subscriptionData?.subscription && (
          <div className="mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
            <div className="flex flex-wrap gap-3">
              {subscriptionData.subscription.status === 'active' && !subscriptionData.subscription.cancel_at_period_end && (
                <>
                  <button
                    onClick={handleUpgradePlan}
                    className="px-4 py-2 bg-dashboard-accent text-white rounded-lg text-sm font-medium hover:bg-opacity-90 transition-colors flex items-center"
                  >
                    <ArrowPathIcon className="h-4 w-4 mr-1" />
                    升級方案
                  </button>
                  
                  <button
                    onClick={() => handleCancelSubscription(false)}
                    disabled={actionLoading === 'cancel'}
                    className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg text-sm font-medium hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
                  >
                    {actionLoading === 'cancel' ? '處理中...' : '期末取消'}
                  </button>
                  
                  <button
                    onClick={() => handleCancelSubscription(true)}
                    disabled={actionLoading === 'cancel'}
                    className="px-4 py-2 border border-red-300 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors disabled:opacity-50"
                  >
                    {actionLoading === 'cancel' ? '處理中...' : '立即取消'}
                  </button>
                </>
              )}
              
              {subscriptionData.subscription.cancel_at_period_end && (
                <button
                  onClick={handleReactivateSubscription}
                  disabled={actionLoading === 'reactivate'}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors disabled:opacity-50"
                >
                  {actionLoading === 'reactivate' ? '處理中...' : '重新啟用訂閱'}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Billing History */}
      <div className={`${themeClasses.card} p-6`}>
        <h2 className={`text-2xl font-bold ${themeClasses.textPrimary} mb-6`}>
          帳單歷史
        </h2>
        
        {billingHistory.length === 0 ? (
          <div className="text-center py-12">
            <ClockIcon className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-2`}>
              尚無帳單記錄
            </h3>
            <p className={`text-sm ${themeClasses.textSecondary}`}>
              當您的訂閱開始計費時，帳單記錄將會顯示在這裡
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700">
                  <th className={`text-left py-3 px-4 font-medium ${themeClasses.textSecondary}`}>日期</th>
                  <th className={`text-left py-3 px-4 font-medium ${themeClasses.textSecondary}`}>金額</th>
                  <th className={`text-left py-3 px-4 font-medium ${themeClasses.textSecondary}`}>計費期間</th>
                  <th className={`text-left py-3 px-4 font-medium ${themeClasses.textSecondary}`}>狀態</th>
                  <th className={`text-left py-3 px-4 font-medium ${themeClasses.textSecondary}`}>操作</th>
                </tr>
              </thead>
              <tbody>
                {billingHistory.map((payment) => (
                  <tr key={payment.id} className="border-b border-gray-100 dark:border-gray-800 hover:bg-gray-50 dark:hover:bg-gray-800/50">
                    <td className={`py-3 px-4 ${themeClasses.textPrimary}`}>
                      {payment.processed_at ? formatDate(payment.processed_at) : '-'}
                    </td>
                    <td className={`py-3 px-4 ${themeClasses.textPrimary} font-medium`}>
                      {formatTWD(payment.amount)}
                    </td>
                    <td className={`py-3 px-4 ${themeClasses.textSecondary} text-sm`}>
                      {formatDate(payment.period_start)} - {formatDate(payment.period_end)}
                    </td>
                    <td className="py-3 px-4">
                      <div className="flex items-center">
                        {getPaymentStatusIcon(payment.status)}
                        <span className={`ml-2 text-sm ${
                          payment.status === 'success' ? 'text-green-400' : 
                          payment.status === 'failed' ? 'text-red-400' : 
                          'text-yellow-400'
                        }`}>
                          {payment.status === 'success' ? '成功' : 
                           payment.status === 'failed' ? '失敗' : '處理中'}
                        </span>
                      </div>
                      {payment.failure_reason && (
                        <div className="text-xs text-red-400 mt-1">
                          {payment.failure_reason}
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {payment.status === 'success' && (
                        <button className="text-sm text-dashboard-accent hover:underline">
                          下載收據
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}