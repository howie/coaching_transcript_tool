'use client'

import { useState, useEffect } from 'react'
import { CreditCardIcon, ClockIcon, ChartBarIcon, CheckIcon, ArrowPathIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { useI18n } from '@/contexts/i18n-context'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import planService, { UsageStatus, PlanConfig, SubscriptionInfo } from '@/lib/services/plan.service'
import { UsageCard } from '@/components/billing/UsageCard'
import { PaymentSettings } from '@/components/billing/PaymentSettings'
import { ChangePlan } from '@/components/billing/ChangePlan'

export default function BillingPage() {
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const [loading, setLoading] = useState(true)
  const [usageStatus, setUsageStatus] = useState<UsageStatus | null>(null)
  const [currentPlan, setCurrentPlan] = useState<PlanConfig | null>(null)
  const [subscriptionInfo, setSubscriptionInfo] = useState<SubscriptionInfo | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'usage' | 'payment' | 'plans'>('overview')

  useEffect(() => {
    loadPlanData()
  }, [])

  const loadPlanData = async () => {
    try {
      const data = await planService.getCurrentPlanStatus()
      setUsageStatus(data.usageStatus)
      setCurrentPlan(data.currentPlan)
      setSubscriptionInfo(data.subscriptionInfo)
    } catch (error) {
      console.error('Failed to load plan data:', error)
      // Show empty/error state instead of mock data
      setUsageStatus(null)
      setCurrentPlan(null)
      setSubscriptionInfo(null)
    } finally {
      setLoading(false)
    }
  }

  const handleUpgrade = () => {
    window.location.href = '/dashboard/billing/change-plan'
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-dashboard-accent"></div>
      </div>
    )
  }

  return (
    <div className={`min-h-screen ${themeClasses.dashboardBg} py-12`}>
      <div className="max-w-7xl mx-auto px-4">
        {/* Page Header */}
        <div className="flex items-center space-x-3 mb-8">
          <CreditCardIcon className="h-8 w-8 text-dashboard-accent" />
          <h1 className={`text-3xl font-bold ${themeClasses.textPrimary}`}>{t('billing.title')}</h1>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8 border-b border-gray-700">
          {[
            { id: 'overview', label: t('billing.overview'), icon: ChartBarIcon },
            { id: 'usage', label: t('billing.usageHistory'), icon: ClockIcon },
            { id: 'payment', label: t('billing.paymentSettings'), icon: CreditCardIcon },
            { id: 'plans', label: t('billing.changePlan'), icon: ArrowPathIcon },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-dashboard-accent text-dashboard-accent'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-8">
          {activeTab === 'overview' && (
            <>
              {/* Upgrade CTA for Free Users */}
              {currentPlan?.planName === 'free' && (
                <div className="mb-6 bg-gradient-to-r from-dashboard-accent to-yellow-600 p-6 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-dashboard-bg mb-2">
                        {t('billing.upgradeTitle')}
                      </h2>
                      <p className="text-dashboard-bg opacity-90">
                        {t('billing.upgradeDescription')}
                      </p>
                      <div className="flex items-center mt-3 space-x-4">
                        <div className="flex items-center">
                          <CheckIcon className="h-5 w-5 text-dashboard-bg mr-2" />
                          <span className="text-dashboard-bg font-medium">10x more sessions</span>
                        </div>
                        <div className="flex items-center">
                          <CheckIcon className="h-5 w-5 text-dashboard-bg mr-2" />
                          <span className="text-dashboard-bg font-medium">Priority support</span>
                        </div>
                        <div className="flex items-center">
                          <CheckIcon className="h-5 w-5 text-dashboard-bg mr-2" />
                          <span className="text-dashboard-bg font-medium">All export formats</span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={handleUpgrade}
                      className="px-6 py-3 bg-dashboard-bg text-dashboard-accent rounded-lg font-semibold hover:bg-opacity-90 transition-colors"
                    >
                      {t('billing.upgradeToPro')}
                    </button>
                  </div>
                </div>
              )}
              
              {/* Current Plan & Usage - 50/50 layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div>
                  {currentPlan && subscriptionInfo ? (
                    <CurrentPlanSummary 
                      plan={currentPlan}
                      subscriptionInfo={subscriptionInfo}
                    />
                  ) : (
                    <div className={`${themeClasses.card} p-6`}>
                      <h2 className={`text-xl font-semibold ${themeClasses.textPrimary} mb-2`}>
                        {t('billing.currentPlan')}
                      </h2>
                      <p className="text-red-400">{t('billing.errorLoadingPlan')}</p>
                    </div>
                  )}
                </div>
                <div>
                  {usageStatus ? (
                    <UsageCard 
                      usageStatus={usageStatus} 
                      onUpgrade={handleUpgrade}
                    />
                  ) : (
                    <div className={`${themeClasses.card} p-6`}>
                      <h2 className={`text-xl font-semibold ${themeClasses.textPrimary} mb-2`}>
                        {t('billing.currentUsage')}
                      </h2>
                      <p className="text-red-400">{t('billing.errorLoadingUsage')}</p>
                      <div className="mt-4 space-y-3">
                        <div className="flex justify-between">
                          <span className={themeClasses.textSecondary}>{t('billing.sessions')}</span>
                          <span className={themeClasses.textPrimary}>0 / -</span>
                        </div>
                        <div className="flex justify-between">
                          <span className={themeClasses.textSecondary}>{t('billing.audioMinutes')}</span>
                          <span className={themeClasses.textPrimary}>0 / -</span>
                        </div>
                        <div className="flex justify-between">
                          <span className={themeClasses.textSecondary}>{t('billing.transcriptions')}</span>
                          <span className={themeClasses.textPrimary}>0 / -</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {activeTab === 'usage' && (
            <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
              <h2 className={`text-xl font-semibold ${themeClasses.textPrimary} mb-4`}>
                {t('billing.usageHistory')}
              </h2>
              <p className="text-gray-400">Usage history coming soon...</p>
            </div>
          )}

          {activeTab === 'payment' && (
            <PaymentSettings />
          )}

          {activeTab === 'plans' && (
            <ChangePlan />
          )}
        </div>
      </div>
    </div>
  )
}

// Component for displaying current plan summary
function CurrentPlanSummary({ plan, subscriptionInfo }: { plan: PlanConfig; subscriptionInfo: SubscriptionInfo }) {
  const { t } = useI18n();
  const themeClasses = useThemeClasses();
  const router = useRouter();
  
  const isFreePlan = plan.planName === 'free';
  
  return (
    <div className={themeClasses.card}>
      <div className="p-6">
        <div className="flex justify-between items-start mb-4">
          <div>
            <h2 className={`text-xl font-semibold ${themeClasses.textPrimary}`}>
              {t('billing.currentPlan')}
            </h2>
            <div className="flex items-center mt-2">
              <p className="text-3xl font-bold text-dashboard-accent">
                {plan.displayName}
              </p>
              {isFreePlan && (
                <button
                  onClick={() => router.push('/dashboard/billing/change-plan')}
                  className="ml-4 px-3 py-1 bg-dashboard-accent text-dashboard-bg rounded-full text-sm font-medium hover:bg-dashboard-accent-hover transition-colors"
                >
                  {t('billing.upgrade')}
                </button>
              )}
            </div>
          </div>
          {subscriptionInfo.active && (
            <span className="px-3 py-1 bg-dashboard-accent bg-opacity-20 text-dashboard-accent rounded-full text-sm font-medium">
              {t('billing.active')}
            </span>
          )}
        </div>
        <div className={`space-y-2 text-sm ${themeClasses.textSecondary}`}>
          {subscriptionInfo.endDate && (
            <p>{t('billing.nextBilling')}: {new Date(subscriptionInfo.endDate).toLocaleDateString()}</p>
          )}
          <p>{isFreePlan ? t('billing.free') : `$${plan.pricing.monthlyUsd}/${t('billing.perMonth')}`}</p>
          {plan.features.prioritySupport && (
            <p className="text-green-400">✓ {t('billing.prioritySupport')}</p>
          )}
        </div>
        
        {isFreePlan && (
          <div className="mt-4 p-3 bg-dashboard-accent bg-opacity-10 rounded-lg border border-dashboard-accent border-opacity-30">
            <p className={`text-sm ${themeClasses.textSecondary}`}>
              {t('billing.freeTrialMessage')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
