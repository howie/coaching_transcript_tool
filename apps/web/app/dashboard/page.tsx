'use client'

import { useI18n } from '@/contexts/i18n-context'
import { DashboardStats } from '@/components/sections/dashboard-stats'
import { FeatureCards } from '@/components/sections/feature-cards'
import { GettingStarted } from '@/components/sections/getting-started'

export default function DashboardPage() {
  const { t } = useI18n()

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-dashboard-accent mb-2">
          {t('dashboard.title')}
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          {t('dashboard.subtitle')}
        </p>
      </div>

      {/* Dashboard Stats */}
      <DashboardStats />

      {/* Feature Cards */}
      <FeatureCards />

      {/* Getting Started Guide */}
      <GettingStarted />
    </div>
  )
}
