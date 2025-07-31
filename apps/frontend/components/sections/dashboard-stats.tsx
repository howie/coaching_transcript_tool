'use client'

import { useI18n } from '@/contexts/i18n-context'

interface StatCardProps {
  number: string
  label: string
}

function StatCard({ number, label }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center shadow-sm hover:shadow-md transition-shadow">
      <div className="text-3xl font-bold text-dashboard-stats-blue mb-2">
        {number}
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {label}
      </div>
    </div>
  )
}

export function DashboardStats() {
  const { t } = useI18n()

  const stats = [
    { number: '24', label: t('dashboard.stats.total_hours') },
    { number: '12', label: t('dashboard.stats.monthly_hours') },
    { number: '8', label: t('dashboard.stats.transcripts') },
    { number: '95%', label: t('dashboard.stats.icf_competency') }
  ]

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
      {stats.map((stat, index) => (
        <StatCard 
          key={index}
          number={stat.number}
          label={stat.label}
        />
      ))}
    </div>
  )
}
