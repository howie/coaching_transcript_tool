'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useI18n } from '@/contexts/i18n-context'
import { useAuth } from '@/contexts/auth-context'
import { DashboardStats } from '@/components/sections/dashboard-stats'
import { FeatureCards } from '@/components/sections/feature-cards'
import { GettingStarted } from '@/components/sections/getting-started'

function DashboardContent() {
  const { t } = useI18n()
  const { login } = useAuth()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Handle Google OAuth callback tokens from URL parameters
    const access_token = searchParams.get('access_token')
    const refresh_token = searchParams.get('refresh_token')
    
    if (access_token && refresh_token) {
      // Login with the access token
      login(access_token).then(() => {
        // Store refresh token for later use
        localStorage.setItem('refresh_token', refresh_token)
        
        // Clean up URL parameters
        window.history.replaceState({}, document.title, '/dashboard')
      }).catch((error) => {
        console.error('Failed to process OAuth callback:', error)
      })
    }
  }, [searchParams, login])

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

export default function DashboardPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DashboardContent />
    </Suspense>
  )
}
