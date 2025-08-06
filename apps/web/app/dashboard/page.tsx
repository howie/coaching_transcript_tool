'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useI18n } from '@/contexts/i18n-context'
import { useAuth } from '@/contexts/auth-context'
import { DashboardStats } from '@/components/sections/dashboard-stats'
import { GettingStarted } from '@/components/sections/getting-started'

function DashboardContent() {
  const { t } = useI18n()
  const { login, user } = useAuth()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Handle Google OAuth callback tokens from URL parameters
    const access_token = searchParams.get('access_token')
    const refresh_token = searchParams.get('refresh_token')
    
    console.log('Dashboard OAuth check:', { 
      access_token: access_token ? 'present' : 'missing',
      refresh_token: refresh_token ? 'present' : 'missing',
      currentUser: user?.name || 'none'
    })
    
    if (access_token && refresh_token) {
      console.log('Processing OAuth callback with tokens...')
      
      // Login with the access token
      login(access_token).then(() => {
        console.log('OAuth login successful, storing refresh token')
        // Store refresh token for later use
        try {
          if (typeof window !== 'undefined' && window.localStorage) {
            localStorage.setItem('refresh_token', refresh_token)
          }
        } catch (error) {
          console.error('Failed to store refresh token:', error)
        }
        
        // Clean up URL parameters
        window.history.replaceState({}, document.title, '/dashboard')
      }).catch((error) => {
        console.error('Failed to process OAuth callback:', error)
        console.error('OAuth error details:', error instanceof Error ? error.message : error)
      })
    } else if (!access_token && !refresh_token && !user) {
      console.log('No OAuth tokens and no user - checking for existing token in storage')
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          const existingToken = localStorage.getItem('token')
          console.log('Existing token in localStorage:', existingToken ? 'present' : 'missing')
        }
      } catch (error) {
        console.error('Failed to check localStorage for existing token:', error)
      }
    }
  }, [searchParams, login, user])

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-dashboard-accent mb-2">
          {t('dashboard.title').replace('{name}', user?.name || '')}
        </h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">
          {t('dashboard.subtitle')}
        </p>
      </div>

      {/* Dashboard Stats */}
      <DashboardStats />

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
