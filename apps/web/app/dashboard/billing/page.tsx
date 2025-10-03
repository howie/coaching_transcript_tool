'use client'

import { useState, useEffect } from 'react'
import { CreditCardIcon, ClockIcon, ChartBarIcon, CheckIcon, ArrowPathIcon, PresentationChartLineIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { useI18n } from '@/contexts/i18n-context'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import planService, { UsageStatus, PlanConfig, SubscriptionInfo } from '@/lib/services/plan.service'
import { UsageCard } from '@/components/billing/UsageCard'
import { PaymentSettings } from '@/components/billing/PaymentSettings'
import { ChangePlan } from '@/components/billing/ChangePlan'
import { SubscriptionStatusBanner } from '@/components/billing/SubscriptionStatusBanner'
import { SubscriptionDashboard } from '@/components/billing/SubscriptionDashboard'
import { ECPayStatus } from '@/components/billing/ECPayStatus'
import UsageHistory from '@/components/billing/UsageHistory'

export default function BillingPage() {
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  const [loading, setLoading] = useState(true)
  const [usageStatus, setUsageStatus] = useState<UsageStatus | null>(null)
  const [currentPlan, setCurrentPlan] = useState<PlanConfig | null>(null)
  const [subscriptionInfo, setSubscriptionInfo] = useState<SubscriptionInfo | null>(null)
  const [activeTab, setActiveTab] = useState<'overview' | 'usage' | 'payment' | 'plans'>('overview')

  // Check for tab parameter in URL
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search)
    const tabParam = urlParams.get('tab')
    if (tabParam && ['overview', 'usage', 'payment', 'plans'].includes(tabParam)) {
      setActiveTab(tabParam as 'overview' | 'usage' | 'payment' | 'plans')
    }
  }, [])

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
    setActiveTab('plans')
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
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <CreditCardIcon className="h-8 w-8 text-dashboard-accent" />
            <h1 className={`text-3xl font-bold ${themeClasses.textPrimary}`}>{t('billing.title')}</h1>
          </div>
          <ECPayStatus />
        </div>

        {/* Subscription Status Banner */}
        <SubscriptionStatusBanner />

        {/* Tabs */}
        <div className="flex space-x-1 mb-8 border-b border-gray-700">
          {[
            { id: 'overview', label: t('billing.overview'), icon: ChartBarIcon },
            { id: 'plans', label: t('billing.changePlan'), icon: ArrowPathIcon },
            { id: 'payment', label: t('billing.paymentSettings'), icon: CreditCardIcon },
            // Usage history tab - only visible in development
            ...(process.env.NODE_ENV === 'development' ? [{ id: 'usage', label: t('billing.usageHistory'), icon: ClockIcon, isDev: true }] : []),
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'overview' | 'usage' | 'payment' | 'plans')}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-dashboard-accent text-dashboard-accent'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
              {'isDev' in tab && tab.isDev && (
                <span className="ml-1 px-1.5 py-0.5 text-xs font-medium bg-yellow-500/20 text-yellow-500 rounded">
                  DEV
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-8">
          {activeTab === 'overview' && (
            <>
              
              {/* Current Usage as Main Content */}
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Main Usage Card - Takes most of the space */}
                <div className="flex-1">
                  {usageStatus ? (
                    <div className={`${themeClasses.card} p-8`}>
                      <div className="flex items-center justify-between mb-6">
                        <h2 className={`text-2xl font-bold ${themeClasses.textPrimary}`}>
                          {t('billing.currentUsage')}
                        </h2>
                        {/* Upgrade Button for Free Users */}
                        {currentPlan?.planName === 'free' && (
                          <button
                            onClick={handleUpgrade}
                            className="bg-dashboard-accent text-dashboard-bg px-4 py-2 rounded-lg font-semibold hover:bg-dashboard-accent-hover transition-colors flex items-center space-x-2"
                          >
                            <span>🚀</span>
                            <span>{t('billing.upgradeToPro')}</span>
                          </button>
                        )}
                      </div>
                      
                      {/* Phase 2: Minutes-Only Usage Metric */}
                      <div className="flex justify-center">
                        <div className="max-w-md w-full text-center p-6 bg-gray-50 dark:bg-gray-800 rounded-lg">
                          <div className="text-4xl font-bold text-dashboard-accent mb-3">
                            {usageStatus.currentUsage?.minutes || 0}
                          </div>
                          <div className="text-sm text-gray-500 mb-2">
                            / {usageStatus.planLimits?.maxTotalMinutes === -1 ? '∞' : (usageStatus.planLimits?.maxTotalMinutes || 0)} {t('billing.minutes')}
                          </div>
                          <div className="text-lg font-medium text-gray-700 dark:text-gray-300 mb-3">
                            {t('billing.audioMinutes')}
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-3 mb-2">
                            <div 
                              className="bg-dashboard-accent h-3 rounded-full transition-all duration-300" 
                              style={{ 
                                width: usageStatus.usagePercentages?.minutes 
                                  ? `${Math.min(100, usageStatus.usagePercentages.minutes)}%`
                                  : '0%'
                              }}
                            ></div>
                          </div>
                          <div className="text-sm text-gray-600 dark:text-gray-400">
                            {usageStatus.usagePercentages?.minutes 
                              ? `${Math.round(usageStatus.usagePercentages.minutes)}% ${t('billing.used')}`
                              : `0% ${t('billing.used')}`
                            }
                          </div>
                        </div>
                      </div>

                      {/* Reset Information */}
                      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="text-sm text-blue-700 dark:text-blue-300">
                            {t('billing.nextResetDate')}
                          </span>
                          <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                            {usageStatus.nextReset 
                              ? new Date(usageStatus.nextReset).toLocaleDateString()
                              : new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toLocaleDateString()
                            }
                          </span>
                        </div>
                      </div>

                      {/* Upgrade Benefits for Free Users */}
                      {currentPlan?.planName === 'free' && (
                        <div className="mt-6 p-5 bg-gradient-to-r from-dashboard-accent/10 to-yellow-500/10 border border-dashboard-accent/20 rounded-lg">
                          <h3 className="text-lg font-semibold text-dashboard-accent mb-3">
                            {t('billing.upgradeTitle')}
                          </h3>
                          <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
                            {t('billing.upgradeDescription')}
                          </p>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div className="flex items-center space-x-2">
                              <CheckIcon className="h-4 w-4 text-dashboard-accent flex-shrink-0" />
                              <span className="text-sm text-gray-700 dark:text-gray-300">
                                {t('billing.benefit.15xMinutes')}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <CheckIcon className="h-4 w-4 text-dashboard-accent flex-shrink-0" />
                              <span className="text-sm text-gray-700 dark:text-gray-300">
                                {t('billing.benefit.prioritySupport')}
                              </span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <CheckIcon className="h-4 w-4 text-dashboard-accent flex-shrink-0" />
                              <span className="text-sm text-gray-700 dark:text-gray-300">
                                {t('billing.benefit.allExportFormats')}
                              </span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className={`${themeClasses.card} p-8`}>
                      <div className="flex items-center justify-between mb-6">
                        <h2 className={`text-2xl font-bold ${themeClasses.textPrimary}`}>
                          {t('billing.currentUsage')}
                        </h2>
                        {/* Upgrade Button for Free Users */}
                        {currentPlan?.planName === 'free' && (
                          <button
                            onClick={handleUpgrade}
                            className="bg-dashboard-accent text-dashboard-bg px-4 py-2 rounded-lg font-semibold hover:bg-dashboard-accent-hover transition-colors flex items-center space-x-2"
                          >
                            <span>🚀</span>
                            <span>{t('billing.upgradeToPro')}</span>
                          </button>
                        )}
                      </div>
                      <p className="text-red-400 text-center py-8">{t('billing.errorLoadingUsage')}</p>
                    </div>
                  )}
                </div>

                {/* Sidebar - Plan Info (Smaller) */}
                <div className="w-full lg:w-80">
                  {currentPlan && subscriptionInfo ? (
                    <div className={`${themeClasses.card} p-6`}>
                      <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-4`}>
                        {t('billing.planDetails')}
                      </h3>
                      
                      <div className="space-y-3">
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">{t('billing.currentPlan')}:</span>
                          <span className="text-sm font-medium">{currentPlan.displayName}</span>
                        </div>
                        
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">{t('billing.status')}:</span>
                          <span className={`text-sm font-medium ${subscriptionInfo.active ? 'text-green-600' : 'text-red-600'}`}>
                            {subscriptionInfo.active ? t('billing.active') : t('billing.inactive')}
                          </span>
                        </div>
                        
                        {subscriptionInfo.endDate && (
                          <div className="flex justify-between">
                            <span className="text-sm text-gray-500">{t('billing.nextBilling')}:</span>
                            <span className="text-sm font-medium">
                              {new Date(subscriptionInfo.endDate).toLocaleDateString()}
                            </span>
                          </div>
                        )}
                        
                        <div className="flex justify-between">
                          <span className="text-sm text-gray-500">{t('billing.monthlyFee')}:</span>
                          <span className="text-sm font-medium">
                            {(() => {
                              if (!currentPlan || currentPlan.planName === 'free') {
                                return t('billing.free');
                              }

                              const pricing = currentPlan.pricing;
                              if (!pricing) {
                                return '—';
                              }

                              if (typeof pricing.monthlyTwd === 'number') {
                                return `NT$${pricing.monthlyTwd}`;
                              }

                              if (typeof pricing.monthlyUsd === 'number') {
                                return `NT$${Math.round(pricing.monthlyUsd * 31.5)}`;
                              }

                              return '—';
                            })()}
                          </span>
                        </div>
                      </div>

                      {currentPlan.planName !== 'business' && (
                        <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                          <button
                            onClick={() => setActiveTab('plans')}
                            className="w-full text-sm bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 py-2 px-3 rounded-md transition-colors"
                          >
                            {t('billing.changePlan')}
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className={`${themeClasses.card} p-6`}>
                      <h3 className={`text-lg font-semibold ${themeClasses.textPrimary} mb-2`}>
                        {t('billing.planDetails')}
                      </h3>
                      <p className="text-red-400 text-sm">{t('billing.errorLoadingPlan')}</p>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {activeTab === 'usage' && user && (
            <UsageHistory 
              userId={user.id}
              userPlan={currentPlan?.planName || 'free'}
              defaultPeriod="30d"
              showInsights={true}
              showPredictions={true}
            />
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
