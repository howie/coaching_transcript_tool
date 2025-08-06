'use client'

import { useEffect, useState } from 'react'
import { useI18n } from '@/contexts/i18n-context'
import { useAuth } from '@/contexts/auth-context'

interface StatCardProps {
  number: string
  label: string
  loading?: boolean
}

interface SummaryData {
  total_minutes: number
  current_month_minutes: number
  transcripts_converted_count: number
  current_month_revenue_by_currency: Record<string, number>
  unique_clients_total: number
}

function StatCard({ number, label, loading = false }: StatCardProps) {
  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center shadow-sm hover:shadow-md transition-shadow">
      <div className="text-3xl font-bold text-dashboard-stats-blue mb-2">
        {loading ? '...' : number}
      </div>
      <div className="text-sm text-gray-600 dark:text-gray-400">
        {label}
      </div>
    </div>
  )
}

export function DashboardStats() {
  const { t } = useI18n()
  const { user } = useAuth()
  const [summaryData, setSummaryData] = useState<SummaryData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (user) {
      fetchSummaryData()
    }
  }, [user])

  const fetchSummaryData = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/v1/dashboard/summary', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      })

      if (response.ok) {
        const data = await response.json()
        setSummaryData(data)
      }
    } catch (error) {
      console.error('Failed to fetch summary data:', error)
    } finally {
      setLoading(false)
    }
  }

  const formatRevenue = (revenue: Record<string, number>) => {
    const entries = Object.entries(revenue)
    if (entries.length === 0) return '0'
    if (entries.length === 1) {
      const [currency, amount] = entries[0]
      return `${currency} ${amount.toLocaleString()}`
    }
    // Multiple currencies, show primary one or total count
    return entries.map(([currency, amount]) => `${currency} ${amount.toLocaleString()}`).join(', ')
  }

  const stats = [
    { 
      number: summaryData ? Math.round(summaryData.total_minutes / 60).toString() : '0', 
      label: t('dashboard.stats.total_hours')
    },
    { 
      number: summaryData ? Math.round(summaryData.current_month_minutes / 60).toString() : '0', 
      label: t('dashboard.stats.monthly_hours')
    },
    { 
      number: summaryData ? summaryData.transcripts_converted_count.toString() : '0', 
      label: t('dashboard.stats.transcripts')
    },
    { 
      number: summaryData ? summaryData.unique_clients_total.toString() : '0', 
      label: t('dashboard.stats.total_clients')
    }
  ]

  // Add revenue stat if there's data
  if (summaryData && Object.keys(summaryData.current_month_revenue_by_currency).length > 0) {
    stats.splice(2, 0, {
      number: formatRevenue(summaryData.current_month_revenue_by_currency),
      label: t('dashboard.stats.monthly_revenue')
    })
  }

  return (
    <div className="grid grid-cols-2 lg:grid-cols-5 gap-4 mb-8">
      {stats.map((stat, index) => (
        <StatCard 
          key={index}
          number={stat.number}
          label={stat.label}
          loading={loading}
        />
      ))}
    </div>
  )
}
