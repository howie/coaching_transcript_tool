'use client'

import { useState } from 'react'
import { CheckIcon, CreditCardIcon, ClockIcon, DocumentTextIcon, ChartBarIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { useI18n } from '@/contexts/i18n-context'
import Link from 'next/link'

export default function BillingPage() {
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
  
  // Mock usage data - in real app would come from API
  const usage = {
    transcripts: {
      used: 3,
      limit: 5,
      percentage: 60
    },
    audioMinutes: {
      used: 45,
      limit: 150,
      percentage: 30
    }
  }

  return (
    <div className={`min-h-screen ${themeClasses.dashboardBg} py-12`}>
      <div className="max-w-6xl mx-auto px-4">
        {/* Page Header */}
        <div className="flex items-center space-x-3 mb-8">
          <CreditCardIcon className="h-8 w-8 text-dashboard-accent" />
          <h1 className={`text-3xl font-bold ${themeClasses.textPrimary}`}>{t('billing.title')}</h1>
        </div>

        {/* Current Plan & Usage */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
          {/* Current Plan Card */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className={`text-xl font-semibold ${themeClasses.textPrimary}`}>{t('billing.currentPlan')}</h2>
                <p className="text-3xl font-bold text-dashboard-accent mt-2">{user?.plan || 'Free'}</p>
              </div>
              <span className="px-3 py-1 bg-dashboard-accent bg-opacity-20 text-dashboard-accent rounded-full text-sm font-medium">
                {t('billing.active')}
              </span>
            </div>
            <div className={`space-y-2 text-sm ${themeClasses.textSecondary}`}>
              <p>{t('billing.nextBilling')}: January 15, 2025</p>
              <p>{t('billing.billingCycle')}: {t('billing.monthly')}</p>
            </div>
          </div>

          {/* Usage Summary Card */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <h2 className={`text-xl font-semibold ${themeClasses.textPrimary} mb-4`}>{t('billing.thisMonthUsage')}</h2>
            
            {/* Transcript Usage */}
            <div className="mb-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <DocumentTextIcon className="h-5 w-5 text-dashboard-accent" />
                  <span className={`text-sm font-medium ${themeClasses.textSecondary}`}>{t('billing.transcripts')}</span>
                </div>
                <span className={`text-sm ${themeClasses.textSecondary}`}>
                  {usage.transcripts.used} / {usage.transcripts.limit}
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-dashboard-accent h-2 rounded-full transition-all duration-300"
                  style={{ width: `${usage.transcripts.percentage}%` }}
                />
              </div>
            </div>

            {/* Audio Minutes Usage */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <ClockIcon className="h-5 w-5 text-dashboard-accent" />
                  <span className={`text-sm font-medium ${themeClasses.textSecondary}`}>{t('billing.audioMinutes')}</span>
                </div>
                <span className={`text-sm ${themeClasses.textSecondary}`}>
                  {usage.audioMinutes.used} / {usage.audioMinutes.limit} min
                </span>
              </div>
              <div className="w-full bg-gray-700 rounded-full h-2">
                <div 
                  className="bg-dashboard-accent h-2 rounded-full transition-all duration-300"
                  style={{ width: `${usage.audioMinutes.percentage}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Billing Actions */}
        <div className="flex flex-wrap gap-4 mb-12">
          <Link href="/dashboard/billing/change-plan" className={themeClasses.buttonPrimary}>
            {t('billing.changePlan')}
          </Link>
          <Link href="/dashboard/billing/payment-settings" className={themeClasses.buttonSecondary}>
            {t('billing.paymentSettings')}
          </Link>
          <button className={themeClasses.buttonSecondary}>
            {t('billing.usageHistory')}
          </button>
        </div>
      </div>
    </div>
  )
}
