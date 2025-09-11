'use client'

import { useState, useEffect, useCallback } from 'react'
import { 
  XMarkIcon,
  CheckIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CreditCardIcon
} from '@heroicons/react/24/outline'
import { useI18n } from '@/contexts/i18n-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { apiClient } from '@/lib/api'

interface PlanConfig {
  id: string
  name: string
  displayName: string
  price: {
    monthly: number
    annual: number
  }
  features: string[]
  isPopular?: boolean
}

interface PlanChangeModalProps {
  currentPlan: string
  currentBillingCycle: string
  changeType: 'upgrade' | 'downgrade'
  onClose: () => void
  onSuccess: () => void
}

interface ProrationPreview {
  current_plan_remaining_value: number
  new_plan_prorated_cost: number
  net_charge: number
  effective_date: string
}

export function PlanChangeModal({ 
  currentPlan, 
  currentBillingCycle,
  changeType, 
  onClose, 
  onSuccess 
}: PlanChangeModalProps) {
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const [selectedPlan, setSelectedPlan] = useState<string>('')
  const [selectedCycle, setSelectedCycle] = useState<'monthly' | 'annual'>(currentBillingCycle as 'monthly' | 'annual')
  const [prorationPreview, setProrationPreview] = useState<ProrationPreview | null>(null)
  const [loading, setLoading] = useState(false)
  const [confirming, setConfirming] = useState(false)

  const plans: PlanConfig[] = [
    {
      id: 'free',
      name: 'FREE',
      displayName: t('billing.planNameFree'),
      price: { monthly: 0, annual: 0 },
      features: [
        t('billing.feature.freeRecordings'),
        t('billing.feature.freeLinkedRecordings'),
        t('billing.feature.freeTranscriptionMinutes'),
        t('billing.feature.freeFileSize'),
        t('billing.feature.basicExportFormats'),
        t('billing.feature.emailSupport')
      ]
    },
    {
      id: 'student',
      name: 'STUDENT',
      displayName: t('billing.planNameStudent'),
      price: { monthly: 30000, annual: 30000 * 10 }, // TWD cents (300 TWD)
      features: [
        t('billing.feature.studentTranscriptionMinutes'),
        t('billing.feature.studentFileSize'), 
        t('billing.feature.studentRetention'),
        t('billing.feature.allExportFormats'),
        t('billing.feature.emailSupport')
      ]
    },
    {
      id: 'pro',
      name: 'PRO',
      displayName: t('billing.planNamePro'),
      price: { monthly: 89900, annual: 89900 * 10 }, // TWD cents
      features: [
        t('billing.feature.proTranscriptionMinutes'),
        t('billing.feature.proFileSize'),
        t('billing.feature.allExportFormats'),
        t('billing.feature.priorityEmailSupport'),
        t('billing.feature.advancedAnalytics')
      ],
      isPopular: true
    },
    {
      id: 'enterprise',
      name: 'ENTERPRISE',
      displayName: t('billing.planNameBusiness'),
      price: { monthly: 299900, annual: 299900 * 10 }, // TWD cents
      features: [
        t('billing.feature.businessSessions'),
        t('billing.feature.businessTranscriptions'),
        t('billing.feature.businessTranscriptionMinutes'),
        t('billing.feature.businessFileSize'),
        t('billing.feature.dedicatedSupport'),
        t('billing.feature.teamCollaboration'),
        t('billing.feature.apiAccess'),
        t('billing.feature.slaGuarantee')
      ]
    }
  ]

  const getAvailablePlans = () => {
    const planOrder: Record<string, number> = { 'free': 0, 'pro': 1, 'enterprise': 2 }
    const currentOrder = planOrder[currentPlan.toLowerCase()] || 0
    
    return plans.filter(plan => {
      const targetOrder = planOrder[plan.id] || 0
      return changeType === 'upgrade' ? targetOrder > currentOrder : targetOrder < currentOrder
    })
  }

  const formatTWD = (amount: number) => {
    return `NT$${(amount / 100).toLocaleString()}`
  }

  const calculateProration = useCallback(async () => {
    if (!selectedPlan || selectedPlan === currentPlan.toLowerCase()) {
      setProrationPreview(null)
      return
    }

    setLoading(true)
    try {
      const response = await apiClient.post('/api/v1/subscriptions/preview-change', {
        new_plan_id: selectedPlan.toUpperCase(),
        new_billing_cycle: selectedCycle
      })
      setProrationPreview(response)
    } catch (error) {
      console.error('Failed to calculate proration:', error)
      setProrationPreview(null)
    } finally {
      setLoading(false)
    }
  }, [selectedPlan, currentPlan, selectedCycle])

  useEffect(() => {
    if (selectedPlan) {
      calculateProration()
    }
  }, [selectedPlan, selectedCycle, calculateProration])

  const handleConfirm = async () => {
    if (!selectedPlan) return

    setConfirming(true)
    try {
      if (changeType === 'upgrade') {
        await apiClient.post('/api/v1/subscriptions/upgrade', {
          plan_id: selectedPlan.toUpperCase(),
          billing_cycle: selectedCycle
        })
        alert('方案升級成功！')
      } else {
        await apiClient.post('/api/v1/subscriptions/downgrade', {
          plan_id: selectedPlan.toUpperCase(),
          billing_cycle: selectedCycle
        })
        alert('方案降級已安排，將在當前週期結束後生效。')
      }
      
      onSuccess()
      onClose()
    } catch (error) {
      console.error(`Failed to ${changeType} subscription:`, error)
      const errorMessage = error instanceof Error ? error.message : String(error)
      alert(`${changeType === 'upgrade' ? '升級' : '降級'}失敗: ${errorMessage}`)
    } finally {
      setConfirming(false)
    }
  }

  const availablePlans = getAvailablePlans()

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className={`${themeClasses.card} w-full max-w-4xl max-h-[90vh] overflow-y-auto`}>
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <h2 className={`text-2xl font-bold ${themeClasses.textPrimary}`}>
            {changeType === 'upgrade' ? '升級方案' : '降級方案'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
          >
            <XMarkIcon className="h-6 w-6" />
          </button>
        </div>

        <div className="p-6">
          {/* Billing Cycle Selection */}
          <div className="mb-8">
            <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-4`}>計費週期</h3>
            <div className="flex space-x-4">
              <button
                onClick={() => setSelectedCycle('monthly')}
                className={`px-6 py-3 rounded-lg border transition-colors ${
                  selectedCycle === 'monthly'
                    ? 'border-dashboard-accent bg-dashboard-accent text-white'
                    : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                月繳
              </button>
              <button
                onClick={() => setSelectedCycle('annual')}
                className={`px-6 py-3 rounded-lg border transition-colors ${
                  selectedCycle === 'annual'
                    ? 'border-dashboard-accent bg-dashboard-accent text-white'
                    : 'border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
              >
                年繳 <span className="ml-2 px-2 py-1 bg-green-500 text-xs rounded-full">省 17%</span>
              </button>
            </div>
          </div>

          {/* Plan Selection */}
          <div className="mb-8">
            <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-4`}>選擇新方案</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {availablePlans.map((plan) => (
                <div
                  key={plan.id}
                  className={`border rounded-lg p-4 cursor-pointer transition-all ${
                    selectedPlan === plan.id
                      ? 'border-dashboard-accent bg-dashboard-accent/5'
                      : 'border-gray-200 dark:border-gray-700 hover:border-dashboard-accent/50'
                  } ${plan.isPopular ? 'relative' : ''}`}
                  onClick={() => setSelectedPlan(plan.id)}
                >
                  {plan.isPopular && (
                    <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                      <span className="px-2 py-1 bg-dashboard-accent text-white text-xs rounded-full">
                        推薦
                      </span>
                    </div>
                  )}

                  <div className="flex items-center justify-between mb-3">
                    <h4 className={`font-semibold ${themeClasses.textPrimary}`}>
                      {plan.displayName}
                    </h4>
                    {selectedPlan === plan.id && (
                      <CheckIcon className="h-5 w-5 text-dashboard-accent" />
                    )}
                  </div>

                  <div className="mb-4">
                    <div className={`text-2xl font-bold ${themeClasses.textPrimary}`}>
                      {formatTWD(selectedCycle === 'annual' ? plan.price.annual : plan.price.monthly)}
                    </div>
                    <div className={`text-sm ${themeClasses.textSecondary}`}>
                      /{selectedCycle === 'annual' ? '年' : '月'}
                    </div>
                  </div>

                  <div className="space-y-2">
                    {plan.features.slice(0, 3).map((feature, index) => (
                      <div key={index} className="flex items-start text-sm">
                        <CheckIcon className="h-4 w-4 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                        <span className={themeClasses.textSecondary}>{feature}</span>
                      </div>
                    ))}
                    {plan.features.length > 3 && (
                      <div className={`text-xs ${themeClasses.textTertiary}`}>
                        +{plan.features.length - 3} 項功能
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Proration Preview */}
          {changeType === 'upgrade' && prorationPreview && (
            <div className="mb-8 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="flex items-start">
                <InformationCircleIcon className="h-5 w-5 text-blue-500 mr-2 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-blue-700 dark:text-blue-300 mb-2">
                    按比例計費預覽
                  </h4>
                  <div className="space-y-2 text-sm text-blue-600 dark:text-blue-400">
                    <div className="flex justify-between">
                      <span>當前方案剩餘價值:</span>
                      <span>{formatTWD(prorationPreview.current_plan_remaining_value)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>新方案按比例費用:</span>
                      <span>{formatTWD(prorationPreview.new_plan_prorated_cost)}</span>
                    </div>
                    <hr className="border-blue-200 dark:border-blue-700" />
                    <div className="flex justify-between font-semibold">
                      <span>需要額外支付:</span>
                      <span>{formatTWD(prorationPreview.net_charge)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>生效日期:</span>
                      <span>{new Date(prorationPreview.effective_date).toLocaleDateString('zh-TW')}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Downgrade Warning */}
          {changeType === 'downgrade' && selectedPlan && (
            <div className="mb-8 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
              <div className="flex items-start">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500 mr-2 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h4 className="font-semibold text-yellow-700 dark:text-yellow-300 mb-2">
                    降級須知
                  </h4>
                  <div className="text-sm text-yellow-600 dark:text-yellow-400 space-y-1">
                    <p>• 降級將在當前計費週期結束後生效</p>
                    <p>• 您將繼續享有當前方案的功能直到期末</p>
                    <p>• 某些進階功能可能會被限制或移除</p>
                    <p>• 超出新方案限制的資料可能會被保留但無法存取</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4">
            <button
              onClick={onClose}
              className="px-6 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
            >
              取消
            </button>
            <button
              onClick={handleConfirm}
              disabled={!selectedPlan || confirming || loading}
              className="px-6 py-3 bg-dashboard-accent text-white rounded-lg font-semibold hover:bg-opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center"
            >
              {confirming ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-t-2 border-b-2 border-white mr-2"></div>
                  處理中...
                </>
              ) : (
                <>
                  <CreditCardIcon className="h-4 w-4 mr-2" />
                  確認{changeType === 'upgrade' ? '升級' : '降級'}
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}