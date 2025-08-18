'use client'

import { useState } from 'react'
import { CheckIcon } from '@heroicons/react/24/outline'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { apiClient } from '@/lib/api'

export function ChangePlan() {
  const [billingCycle, setBillingCycle] = useState('annual')
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const router = useRouter()
  
  // Determine current plan from user data
  const currentUserPlan = user?.plan?.toLowerCase() || 'free'

  const plans = [
    {
      name: t('billing.planNameFree'),
      id: 'free',
      price: { monthly: 0, annual: 0 },
      description: t('billing.freeDescription'),
      features: [
        t('billing.feature.freeRecordings'),
        t('billing.feature.freeLinkedRecordings'),
        t('billing.feature.freeTranscriptionMinutes'),
        t('billing.feature.freeRecordingLength'),
        t('billing.feature.freeFileSize'),
        t('billing.feature.basicExportFormats'),
        t('billing.feature.emailSupport')
      ],
      isCurrent: currentUserPlan === 'free',
    },
    {
      name: t('billing.planNamePro'),
      id: 'pro',
      price: { monthly: 899, annual: 749 }, // Updated ECPay pricing (899.00 TWD monthly, 8999.00 TWD annual)
      description: t('billing.proDescription'),
      features: [
        t('billing.feature.proSessions'),
        t('billing.feature.proTranscriptions'),
        t('billing.feature.proTranscriptionMinutes'),
        t('billing.feature.proRecordingLength'),
        t('billing.feature.proFileSize'),
        t('billing.feature.allExportFormats'),
        t('billing.feature.priorityEmailSupport'),
        t('billing.feature.advancedAnalytics'),
        t('billing.feature.customBranding')
      ],
      isPopular: true,
      isCurrent: currentUserPlan === 'pro',
    },
    {
      name: t('billing.planNameBusiness'),
      id: 'enterprise',
      price: { monthly: 2999, annual: 2499 }, // Updated ECPay pricing (2999.00 TWD monthly, 2999.00 * 10 = 29999.00 TWD annual)
      description: t('billing.businessDescription'),
      features: [
        t('billing.feature.businessSessions'),
        t('billing.feature.businessTranscriptions'),
        t('billing.feature.businessTranscriptionMinutes'),
        t('billing.feature.businessRecordingLength'),
        t('billing.feature.businessFileSize'),
        t('billing.feature.allExportFormats'),
        t('billing.feature.dedicatedSupport'),
        t('billing.feature.teamCollaboration'),
        t('billing.feature.apiAccess'),
        t('billing.feature.customIntegrations'),
        t('billing.feature.slaGuarantee')
      ],
      isCurrent: currentUserPlan === 'business' || currentUserPlan === 'enterprise',
    },
  ]

  const handlePlanSelect = (planName: string) => {
    setSelectedPlan(planName)
  }

  const handleConfirmChange = async () => {
    if (!selectedPlan || !user) return
    
    // Map selected plan name to ECPay plan IDs
    const planMapping: Record<string, string> = {
      [t('billing.planNamePro')]: 'PRO',
      [t('billing.planNameBusiness')]: 'ENTERPRISE'
    }
    
    const ecpayPlanId = planMapping[selectedPlan]
    if (!ecpayPlanId) {
      console.error('Invalid plan selection:', selectedPlan)
      return
    }
    
    try {
      console.log(`🔄 開始升級流程: ${ecpayPlanId} (${billingCycle})`)
      
      // Call ECPay subscription API using apiClient
      const data = await apiClient.post('/api/v1/subscriptions/authorize', {
        plan_id: ecpayPlanId,
        billing_cycle: billingCycle
      })
      
      console.log('✅ API 回應成功:', data)
        
        // Show confirmation before redirecting to ECPay
        const confirmed = window.confirm(
          `即將跳轉至 ECPay 付款頁面\n\n` +
          `方案: ${selectedPlan}\n` +
          `計費週期: ${billingCycle}\n` +
          `付款網址: ${data.action_url}\n\n` +
          `確認要繼續嗎？`
        )
        
        if (!confirmed) {
          console.log('❌ 用戶取消付款流程')
          return
        }
        
        // Redirect to ECPay payment form
        const form = document.createElement('form')
        form.method = 'POST'
        form.action = data.action_url
        form.target = '_blank'
        
        // Add form data
        Object.entries(data.form_data).forEach(([key, value]) => {
          const input = document.createElement('input')
          input.type = 'hidden'
          input.name = key
          input.value = String(value)
          form.appendChild(input)
        })
        
        document.body.appendChild(form)
        form.submit()
        document.body.removeChild(form)
        
        console.log('🚀 ECPay 付款表單已送出')
        alert('ECPay 付款視窗已開啟，請在新視窗中完成付款')
    } catch (error) {
      console.error('💥 升級流程錯誤:', error)
      alert(`升級過程中發生錯誤: ${error.message}`)
    }
  }

  const renderPlanButton = (plan: any) => {
    const planOrder: Record<string, number> = { 'free': 0, 'pro': 1, 'business': 2 }
    const currentOrder = planOrder[currentUserPlan] || 0
    const targetOrder = planOrder[plan.id] || 0
    
    if (plan.isCurrent) {
      return (
        <div className="text-center py-2 px-4 rounded-lg bg-gray-600 text-gray-300">
          {t('billing.currentlyUsing')}
        </div>
      )
    } else if (targetOrder < currentOrder) {
      // Downgrade not allowed
      return (
        <div className="text-center py-2 px-4 rounded-lg border border-gray-600 text-gray-500 cursor-not-allowed">
          {t('billing.cannotDowngrade')}
        </div>
      )
    } else {
      // Upgrade available
      return (
        <button
          onClick={(e) => {
            e.stopPropagation()
            handlePlanSelect(plan.name)
          }}
          className="w-full py-2 px-4 rounded-lg font-medium transition-all hover:scale-105 border-2"
          style={{
            backgroundColor: selectedPlan === plan.name ? 'var(--accent-color)' : 'transparent',
            borderColor: 'var(--accent-color)',
            color: selectedPlan === plan.name ? 'var(--bg-primary)' : 'var(--accent-color)'
          }}
        >
          {selectedPlan === plan.name ? `✓ ${t('billing.selected')}` : `${t('billing.upgradeTo')} ${plan.name}`}
        </button>
      )
    }
  }

  return (
    <div className="space-y-8">
      {/* Billing Cycle Toggle */}
      <div className="flex items-center justify-center">
        <div className="flex items-center space-x-3 bg-dashboard-card rounded-lg p-1 border border-dashboard-accent border-opacity-20">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-4 py-2 rounded-md transition-all ${
              billingCycle === 'monthly'
                ? 'bg-dashboard-accent text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {t('billing.monthly')}
          </button>
          <button
            onClick={() => setBillingCycle('annual')}
            className={`px-4 py-2 rounded-md transition-all flex items-center ${
              billingCycle === 'annual'
                ? 'bg-dashboard-accent text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {t('billing.annual')}
            <span className="ml-2 px-2 py-1 bg-green-500 text-xs rounded-full">{t('billing.save31')}</span>
          </button>
        </div>
      </div>

      {/* Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <div
            key={plan.name}
            className={`bg-dashboard-card rounded-lg p-6 border ${
              plan.isCurrent
                ? 'border-gray-600'
                : selectedPlan === plan.name
                ? 'border-dashboard-accent'
                : 'border-dashboard-accent border-opacity-20'
            } ${plan.isPopular ? 'relative' : ''}`}
          >
            {plan.isPopular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="px-3 py-1 bg-dashboard-accent text-white text-sm rounded-full">
                  {t('billing.mostPopular')}
                </span>
              </div>
            )}

            <div className="mb-4">
              <h3 className={`text-xl font-bold ${themeClasses.textPrimary}`}>
                {plan.name}
              </h3>
              <p className={`text-sm mt-1 ${themeClasses.textSecondary}`}>
                {plan.description}
              </p>
            </div>

            <div className="mb-6">
              <div className="flex items-baseline">
                <span className="text-lg mr-1 text-gray-400">NT$</span>
                <span className={`text-3xl font-bold ${themeClasses.textPrimary}`}>
                  {billingCycle === 'annual' ? plan.price.annual : plan.price.monthly}
                </span>
                <span className={`ml-2 ${themeClasses.textTertiary}`}>
                  /{t('billing.perMonth')}
                </span>
              </div>
              {billingCycle === 'annual' && plan.price.annual > 0 && (
                <p className={`text-sm mt-1 ${themeClasses.textTertiary}`}>
                  {t('billing.perYear')}: NT${plan.price.annual * 12}
                </p>
              )}
            </div>

            <div className="mb-6">
              <ul className="space-y-2">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <CheckIcon className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                    <span className={`text-sm ${themeClasses.textSecondary}`}>
                      {feature}
                    </span>
                  </li>
                ))}
              </ul>
            </div>

            <div className="mt-8">
              {renderPlanButton(plan)}
            </div>
          </div>
        ))}
      </div>

      {/* Confirmation Section */}
      {selectedPlan && selectedPlan !== plans.find(p => p.isCurrent)?.name && (
        <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
          <h3 className={`text-xl font-semibold mb-4 ${themeClasses.textPrimary}`}>
            {t('billing.confirmUpgrade')}
          </h3>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div>
              <p className={`text-sm mb-1 ${themeClasses.textTertiary}`}>{t('billing.newPlan')}</p>
              <p className={`text-lg font-medium ${themeClasses.textPrimary}`}>{selectedPlan}</p>
            </div>
            <div>
              <p className={`text-sm mb-1 ${themeClasses.textTertiary}`}>{t('billing.billingCycle')}</p>
              <p className={`text-lg font-medium ${themeClasses.textPrimary}`}>
                {billingCycle === 'annual' ? t('billing.annual') : t('billing.monthly')} - NT$
                {plans.find(p => p.name === selectedPlan)?.price[billingCycle === 'annual' ? 'annual' : 'monthly']}
              </p>
            </div>
            <div>
              <p className={`text-sm mb-1 ${themeClasses.textTertiary}`}>{t('billing.effectiveDate')}</p>
              <p className={`text-lg font-medium ${themeClasses.textPrimary}`}>{t('billing.immediately')}</p>
            </div>
          </div>
          
          <div className="flex flex-col space-y-4">
            {/* Development Testing Info */}
            <div className="p-3 bg-blue-600 bg-opacity-10 border border-blue-600 border-opacity-20 rounded-lg">
              <p className="text-xs text-blue-400 mb-2">
                <strong>測試資訊:</strong> 點擊確認升級將會：
              </p>
              <ul className="text-xs text-blue-300 space-y-1 ml-4">
                <li>• 呼叫 /api/v1/subscriptions/authorize API</li>
                <li>• 生成 ECPay 付款表單</li>
                <li>• 在新視窗開啟 ECPay 付款頁面</li>
                <li>• 使用 ECPay 測試環境 (payment-stage.ecpay.com.tw)</li>
              </ul>
            </div>

            <div className="flex space-x-4">
              <button
                onClick={() => setSelectedPlan(null)}
                className={`flex-1 px-6 py-3 border rounded-lg transition-colors ${themeClasses.buttonSecondary}`}
              >
                {t('billing.cancel')}
              </button>
              <button
                onClick={handleConfirmChange}
                className="flex-1 px-6 py-3 rounded-lg transition-colors font-semibold bg-dashboard-accent text-white hover:bg-opacity-90"
              >
                {t('billing.confirmUpgrade')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}