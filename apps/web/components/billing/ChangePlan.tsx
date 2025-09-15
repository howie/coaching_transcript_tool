'use client'

import { useState, useEffect } from 'react'
import { CheckIcon } from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { apiClient } from '@/lib/api'
import { SubscriptionDashboard } from './SubscriptionDashboard'
import subscriptionService, { SubscriptionData, PlanData } from '@/lib/services/subscription.service'

export function ChangePlan() {
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const router = useRouter()
  
  // State management
  const [loading, setLoading] = useState(true)
  const [subscriptionData, setSubscriptionData] = useState<SubscriptionData | null>(null)
  const [availablePlans, setAvailablePlans] = useState<PlanData[]>([])
  const [activeView, setActiveView] = useState<'plans' | 'subscription'>('plans')
  
  // Determine current plan from subscription data
  const currentUserPlan = subscriptionData?.subscription?.plan_id?.toLowerCase() || 'free'

  // Load data on component mount
  useEffect(() => {
    if (user) {
      loadSubscriptionData()
    }
  }, [user])

  const loadSubscriptionData = async () => {
    try {
      setLoading(true)
      const [subscription, plans] = await Promise.all([
        subscriptionService.getCurrentSubscription(),
        subscriptionService.getAvailablePlans()
      ])
      
      setSubscriptionData(subscription)
      setAvailablePlans(plans)
    } catch (error) {
      console.error('Failed to load subscription data:', error)
    } finally {
      setLoading(false)
    }
  }

  const handlePlanSelect = async (planId: string, billingCycle: string) => {
    if (!user) return
    
    // Handle FREE plan selection as cancellation
    if (planId.toUpperCase() === 'FREE') {
      const hasExistingSubscription = subscriptionData?.subscription && subscriptionData.status !== 'no_subscription'
      if (hasExistingSubscription) {
        const confirmed = window.confirm(
          `確認降級至免費方案？\n\n` +
          `目前方案: ${subscriptionData.subscription?.plan_name}\n` +
          `降級至: 免費方案\n` +
          `將於帳單週期結束時生效`
        )
        
        if (!confirmed) return
        
        try {
          const data = await subscriptionService.downgradeSubscription('FREE', billingCycle)
          if (data.success) {
            alert(`✅ 降級至免費方案成功！\n${data.message}`)
            await loadSubscriptionData()
          } else {
            throw new Error(data.message || '降級失敗')
          }
        } catch (error) {
          console.error('💥 降級失敗:', error)
          const errorMessage = error instanceof Error ? error.message : String(error)
          alert(`降級過程中發生錯誤: ${errorMessage}`)
        }
      }
      return
    }
    
    // Map plan IDs to ECPay plan IDs - handle both upper and lower case
    const planMapping: Record<string, string> = {
      'student': 'STUDENT',
      'STUDENT': 'STUDENT',
      'pro': 'PRO',
      'PRO': 'PRO',
      'enterprise': 'ENTERPRISE',
      'ENTERPRISE': 'ENTERPRISE'
    }
    
    const ecpayPlanId = planMapping[planId] || planMapping[planId.toUpperCase()]
    if (!ecpayPlanId) {
      console.error('Invalid plan selection:', planId)
      return
    }
    
    try {
      console.log(`🔄 開始方案變更流程: ${ecpayPlanId} (${billingCycle})`)
      
      // Determine if this is a new subscription or plan change
      const hasExistingSubscription = subscriptionData?.subscription && subscriptionData.status !== 'no_subscription'
      const currentPlanId = subscriptionData?.subscription?.plan_id
      
      let data
      
      if (hasExistingSubscription && currentPlanId) {
        // User has existing subscription - use upgrade/downgrade flow
        const planChangeType = subscriptionService.getPlanChangeType(currentPlanId, ecpayPlanId)
        
        console.log(`📊 方案變更類型: ${planChangeType} (${currentPlanId} → ${ecpayPlanId})`)
        
        if (planChangeType === 'upgrade') {
          // Preview the upgrade cost first
          try {
            const preview = await subscriptionService.previewPlanChange(ecpayPlanId, billingCycle)
            console.log('💰 升級費用預覽:', preview)
            
            // Show upgrade confirmation
            const confirmed = window.confirm(
              `確認升級方案？\n\n` +
              `目前方案: ${currentPlanId}\n` +
              `升級至: ${ecpayPlanId}\n` +
              `額外費用: NT$${(preview.net_charge || 0) / 100}\n` +
              `立即生效`
            )
            
            if (!confirmed) return
            
            // Proceed with upgrade
            data = await subscriptionService.upgradeSubscription(ecpayPlanId, billingCycle)
          } catch (previewError) {
            console.error('升級預覽失敗:', previewError)
            // Fallback to direct upgrade
            data = await subscriptionService.upgradeSubscription(ecpayPlanId, billingCycle)
          }
        } else if (planChangeType === 'downgrade') {
          // Show downgrade confirmation
          const confirmed = window.confirm(
            `確認降級方案？\n\n` +
            `目前方案: ${currentPlanId}\n` +
            `降級至: ${ecpayPlanId}\n` +
            `將於帳單週期結束時生效`
          )
          
          if (!confirmed) return
          
          data = await subscriptionService.downgradeSubscription(ecpayPlanId, billingCycle)
        } else {
          console.log('相同方案，無需變更')
          return
        }
        
        // Handle upgrade/downgrade response
        if (data.success) {
          alert(`✅ 方案變更成功！\n${data.message}`)
          // Reload subscription data
          await loadSubscriptionData()
        } else {
          throw new Error(data.message || '方案變更失敗')
        }
        
      } else {
        // User has no subscription - create new authorization
        console.log('🆕 創建新訂閱授權')
        
        data = await apiClient.post('/api/v1/subscriptions/authorize', {
          plan_id: ecpayPlanId,
          billing_cycle: billingCycle
        })
        
        console.log('✅ 授權 API 回應成功:', data)
        
        // Show confirmation before redirecting to ECPay
        const confirmed = window.confirm(
          `即將跳轉至 ECPay 付款頁面\n\n` +
          `方案: ${ecpayPlanId}\n` +
          `週期: ${billingCycle === 'monthly' ? '月付' : '年付'}\n` +
          `確認繼續?`
        )
        
        if (confirmed && data.action_url && data.form_data) {
          // Create form and submit to ECPay
          const form = document.createElement('form')
          form.method = 'POST'
          form.action = data.action_url
          
          // Add form fields
          Object.entries(data.form_data).forEach(([key, value]) => {
            const input = document.createElement('input')
            input.type = 'hidden'
            input.name = key
            input.value = String(value)
            form.appendChild(input)
          })
          
          document.body.appendChild(form)
          form.submit();
        }
      }
      
    } catch (error) {
      console.error('💥 升級流程錯誤:', error)
      const errorMessage = error instanceof Error ? error.message : String(error)
      alert(`升級過程中發生錯誤: ${errorMessage}`)
    }
  };

  const submitECPayForm = async (data: any) => {
    // Create and submit form to ECPay
    const form = document.createElement('form')
    form.method = 'POST'
    form.action = data.action_url
    form.target = '_blank'
    
    // Add form data
    Object.entries(data.form_data).forEach(([key, value]) => {
      const input = document.createElement('input')
      input.type = 'hidden'
      input.name = key
      input.value = value === null || value === undefined ? '' : String(value).trim()
      form.appendChild(input)
    })
    
    document.body.appendChild(form)
    form.submit()
    document.body.removeChild(form)
    
    console.log('🚀 ECPay 付款表單已送出 (CheckMacValue 使用官方8步規範)')
    alert('ECPay 付款視窗已開啟，請在新視窗中完成付款')
  }

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-dashboard-accent"></div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* View Toggle */}
      <div className="flex justify-center mb-8">
        <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setActiveView('plans')}
            className={`px-6 py-3 rounded-md font-medium transition-all ${
              activeView === 'plans'
                ? 'bg-white dark:bg-gray-700 shadow-md text-dashboard-accent'
                : 'text-gray-600 dark:text-gray-400 hover:text-dashboard-accent'
            }`}
          >
            📋 查看方案
          </button>
          <button
            onClick={() => setActiveView('subscription')}
            className={`px-6 py-3 rounded-md font-medium transition-all ${
              activeView === 'subscription'
                ? 'bg-white dark:bg-gray-700 shadow-md text-dashboard-accent'
                : 'text-gray-600 dark:text-gray-400 hover:text-dashboard-accent'
            }`}
          >
            🔧 訂閱管理
          </button>
        </div>
      </div>

      {/* Content based on active view */}
      {activeView === 'plans' ? (
        <DatabasePricingDisplay 
          currentPlan={currentUserPlan}
          availablePlans={availablePlans}
          subscriptionData={subscriptionData}
          onSelectPlan={handlePlanSelect}
        />
      ) : (
        <SubscriptionDashboard />
      )}
    </div>
  )
}

// Database-driven pricing display component
function DatabasePricingDisplay({ 
  currentPlan, 
  availablePlans, 
  subscriptionData,
  onSelectPlan 
}: {
  currentPlan: string
  availablePlans: PlanData[]
  subscriptionData: SubscriptionData | null
  onSelectPlan: (planId: string, billingCycle: string) => void
}) {
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('annual')

  const formatPrice = (amountCents: number) => {
    // 防止 NaN 和無效值
    if (!amountCents || isNaN(amountCents) || amountCents <= 0) {
      return 'NT$0'
    }
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0
    }).format(amountCents / 100)
  }

  // 安全的月費計算函數，專門處理年繳方案的月均價格
  const calculateMonthlyEquivalent = (annualPriceCents: number) => {
    if (!annualPriceCents || isNaN(annualPriceCents) || annualPriceCents <= 0) {
      return null
    }
    return Math.round(annualPriceCents / 12)
  }

  const calculateSavings = (monthlyPrice: number, annualPrice: number) => {
    if (monthlyPrice === 0 || annualPrice === 0) return 0
    const monthlyCost = monthlyPrice * 12
    const savings = ((monthlyCost - annualPrice) / monthlyCost) * 100
    return Math.round(savings)
  }

  const getPlanStatus = (planId: string) => {
    const planIdUpper = planId.toUpperCase()
    const currentPlanUpper = currentPlan.toUpperCase()
    
    if (planIdUpper === currentPlanUpper) return 'current'
    
    const hierarchy: Record<string, number> = { 'FREE': 0, 'STUDENT': 1, 'PRO': 2, 'ENTERPRISE': 3 }
    const currentLevel = hierarchy[currentPlanUpper] || 0
    const targetLevel = hierarchy[planIdUpper] || 0
    
    if (targetLevel > currentLevel) return 'upgrade'
    if (targetLevel < currentLevel) return 'downgrade'
    return 'available'
  }

  const getButtonText = (planId: string) => {
    const status = getPlanStatus(planId)
    switch (status) {
      case 'current': return '目前方案'
      case 'upgrade': return '升級至此方案'
      case 'downgrade': return '降級至此方案'
      default: return planId === 'FREE' ? '免費使用' : '選擇此方案'
    }
  }

  const isButtonDisabled = (planId: string) => {
    return getPlanStatus(planId) === 'current'
  }

  return (
    <div className="space-y-12">
      {/* Subscription Info Header */}
      {subscriptionData?.subscription && (
        <div className={`${themeClasses.card} p-6`}>
          <div className="flex items-center justify-between">
            <div>
              <h3 className={`text-lg font-semibold ${themeClasses.textPrimary}`}>
                目前訂閱：{subscriptionData.subscription.plan_name}
              </h3>
              <p className={`text-sm ${themeClasses.textSecondary}`}>
                計費週期：{subscriptionData.subscription.billing_cycle === 'monthly' ? '月繳' : '年繳'} | 
                狀態：{subscriptionData.subscription.status === 'active' ? '使用中' : '非使用中'}
              </p>
            </div>
            <div className="text-right">
              <div className={`text-2xl font-bold ${themeClasses.textPrimary}`}>
                {formatPrice(subscriptionData.subscription.amount_twd)}
              </div>
              <div className="text-sm text-gray-500">
                /{subscriptionData.subscription.billing_cycle === 'monthly' ? '月' : '年'}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Billing Cycle Toggle */}
      <div className="flex justify-center">
        <div className="flex items-center bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-6 py-3 rounded-md font-medium transition-all ${
              billingCycle === 'monthly'
                ? 'bg-white dark:bg-gray-700 shadow-md text-dashboard-accent'
                : 'text-gray-600 dark:text-gray-400 hover:text-dashboard-accent'
            }`}
          >
            月繳方案
          </button>
          <button
            onClick={() => setBillingCycle('annual')}
            className={`px-6 py-3 rounded-md font-medium transition-all relative ${
              billingCycle === 'annual'
                ? 'bg-white dark:bg-gray-700 shadow-md text-dashboard-accent'
                : 'text-gray-600 dark:text-gray-400 hover:text-dashboard-accent'
            }`}
          >
            年繳方案
            <span className="ml-2 px-2 py-1 bg-green-500 text-white text-xs rounded-full">
              最高省 17%
            </span>
          </button>
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {availablePlans
          .filter(plan => plan.is_active)
          .sort((a, b) => a.sort_order - b.sort_order)
          .map((plan) => {
            const status = getPlanStatus(plan.id)
            const savings = calculateSavings(plan.pricing.monthly_twd, plan.pricing.annual_twd)
            const currentPrice = billingCycle === 'monthly' ? plan.pricing.monthly_twd : plan.pricing.annual_twd

            return (
              <div
                key={plan.id}
                className={`relative bg-white dark:bg-gray-800 rounded-2xl border-2 transition-all duration-300 hover:shadow-xl ${
                  plan.id === 'PRO' 
                    ? 'border-dashboard-accent shadow-lg scale-105' 
                    : 'border-gray-200 dark:border-gray-700 hover:border-dashboard-accent'
                } ${status === 'current' ? 'ring-2 ring-dashboard-accent' : ''}`}
              >
                {/* Popular Badge */}
                {plan.id === 'PRO' && (
                  <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                    <div className="flex items-center bg-dashboard-accent text-white px-4 py-2 rounded-full text-sm font-medium">
                      ⭐ 最受歡迎
                    </div>
                  </div>
                )}

                <div className="p-8">
                  {/* Plan Header */}
                  <div className="text-center mb-8">
                    <h3 className={`text-2xl font-bold ${themeClasses.textPrimary} mb-2`}>
                      {plan.display_name}
                    </h3>
                    <p className={`text-sm ${themeClasses.textSecondary} mb-6`}>
                      {plan.description}
                    </p>

                    {/* Pricing */}
                    <div className="space-y-2">
                      <div className="flex items-baseline justify-center">
                        <span className={`text-4xl font-bold ${themeClasses.textPrimary}`}>
                          {formatPrice(currentPrice)}
                        </span>
                        <span className={`text-sm ${themeClasses.textSecondary} ml-2`}>
                          /{billingCycle === 'monthly' ? '月' : '年'}
                        </span>
                      </div>

                      {billingCycle === 'annual' && plan.pricing.annual_twd > 0 && savings > 0 && (() => {
                        const monthlyEquivalent = calculateMonthlyEquivalent(plan.pricing.annual_twd)
                        return monthlyEquivalent && (
                          <div className="space-y-1">
                            <div className="text-sm text-gray-500">
                              相當於每月 {formatPrice(monthlyEquivalent)}
                            </div>
                            <div className="flex items-center justify-center space-x-2 text-sm">
                              <span className="line-through text-gray-400">
                                月繳全年 {formatPrice(plan.pricing.monthly_twd * 12)}
                              </span>
                              <span className="bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-300 px-2 py-1 rounded text-xs">
                                年繳省 {savings}%
                              </span>
                            </div>
                          </div>
                        )
                      })()}
                    </div>
                  </div>

                  {/* Features */}
                  <div className="space-y-4 mb-8">
                    {plan.features.map((feature, index) => (
                      <div key={index} className="flex items-center">
                        <CheckIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
                        <span className={`text-sm ${themeClasses.textSecondary}`}>
                          {feature}
                        </span>
                      </div>
                    ))}
                  </div>

                  {/* CTA Button */}
                  <button
                    onClick={() => !isButtonDisabled(plan.id) && onSelectPlan(plan.id, billingCycle)}
                    disabled={isButtonDisabled(plan.id)}
                    className={`w-full py-4 rounded-lg font-semibold text-sm transition-all duration-200 ${
                      plan.id === 'PRO'
                        ? 'bg-dashboard-accent text-white hover:bg-opacity-90 shadow-lg hover:shadow-xl'
                        : isButtonDisabled(plan.id)
                        ? 'bg-gray-100 dark:bg-gray-700 text-gray-500 cursor-not-allowed'
                        : 'border-2 border-dashboard-accent text-dashboard-accent hover:bg-dashboard-accent hover:text-white'
                    } ${isButtonDisabled(plan.id) ? 'opacity-60 cursor-not-allowed' : 'hover:scale-105'}`}
                  >
                    {getButtonText(plan.id)}
                  </button>
                </div>
              </div>
            )
          })}
      </div>

      {/* Features Comparison Table */}
      <div className="mt-16">
        <div className="text-center mb-8">
          <h3 className={`text-3xl font-bold ${themeClasses.textPrimary} mb-4`}>
            詳細功能比較
          </h3>
          <p className={`text-lg ${themeClasses.textSecondary}`}>
            選擇最適合您需求的方案
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <thead>
              <tr className="border-b border-gray-200 dark:border-gray-700">
                <th className="p-6 text-left font-semibold">功能項目</th>
                {availablePlans
                  .filter(plan => plan.is_active)
                  .sort((a, b) => a.sort_order - b.sort_order)
                  .map((plan) => (
                  <th key={plan.id} className="p-6 text-center font-semibold">
                    {plan.display_name}
                    {plan.id === 'PRO' && (
                      <div className="text-xs text-dashboard-accent mt-1">推薦</div>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <td className="p-6 font-medium">每月轉錄分鐘數</td>
                {availablePlans
                  .filter(plan => plan.is_active)
                  .sort((a, b) => a.sort_order - b.sort_order)
                  .map((plan) => (
                  <td key={plan.id} className="p-6 text-center">
                    {plan.limits.max_total_minutes === -1 ? '無限制' : `${plan.limits.max_total_minutes} 分鐘`}
                  </td>
                ))}
              </tr>
              <tr className="border-b border-gray-100 dark:border-gray-800">
                <td className="p-6 font-medium">檔案大小限制</td>
                {availablePlans
                  .filter(plan => plan.is_active)
                  .sort((a, b) => a.sort_order - b.sort_order)
                  .map((plan) => (
                  <td key={plan.id} className="p-6 text-center">
                    {plan.limits.max_file_size_mb} MB
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Pricing Note */}
      <div className="text-center space-y-4">
        <p className={`text-sm ${themeClasses.textTertiary}`}>
          * 所有價格以新台幣計算，包含稅金 | 數據直接來自資料庫
        </p>
        <div className="flex justify-center space-x-8 text-sm text-dashboard-accent">
          <span>✓ 隨時升級或降級</span>
          <span>✓ 隨時取消訂閱</span>
          <span>✓ 安全付款保護</span>
        </div>
      </div>
    </div>
  )
}

export default ChangePlan