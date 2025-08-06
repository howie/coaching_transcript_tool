'use client'

import { useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useI18n } from '@/contexts/i18n-context'
import { useAuth } from '@/contexts/auth-context'
import { DashboardStats } from '@/components/sections/dashboard-stats'
import { GettingStarted } from '@/components/sections/getting-started'
import { AuthDiagnostics } from '@/components/debug/auth-diagnostics'
import { AuthResetButton } from '@/components/debug/auth-reset-button'

function DashboardContent() {
  const { t } = useI18n()
  const { login, user, isLoading } = useAuth()
  const searchParams = useSearchParams()

  useEffect(() => {
    // Handle Google OAuth callback tokens from URL parameters
    const access_token = searchParams.get('access_token')
    const refresh_token = searchParams.get('refresh_token')
    const error_param = searchParams.get('error')
    const error_description = searchParams.get('error_description')
    
    console.log('Dashboard OAuth check:', { 
      access_token: access_token ? 'present' : 'missing',
      refresh_token: refresh_token ? 'present' : 'missing',
      error: error_param || 'none',
      error_description: error_description || 'none',
      currentUser: user?.name || 'none',
      userAgent: navigator.userAgent,
      isSafari: /^((?!chrome|android).)*safari/i.test(navigator.userAgent)
    })
    
    // Handle OAuth errors
    if (error_param) {
      console.error('OAuth error received:', error_param, error_description)
      // You might want to show a user-friendly error message here
      return
    }
    
    if (access_token && refresh_token) {
      console.log('Processing OAuth callback with tokens...')
      
      // Add a small delay for Safari to ensure everything is ready
      const processOAuth = async () => {
        try {
          console.log('Attempting login with access token...')
          await login(access_token)
          
          console.log('OAuth login successful, storing refresh token')
          // Store refresh token for later use
          try {
            if (typeof window !== 'undefined' && window.localStorage) {
              localStorage.setItem('refresh_token', refresh_token)
              console.log('Refresh token stored successfully')
            }
          } catch (storageError) {
            console.error('Failed to store refresh token:', storageError)
          }
          
          // Clean up URL parameters after a successful login
          setTimeout(() => {
            window.history.replaceState({}, document.title, '/dashboard')
            console.log('URL cleaned up')
          }, 1000)
          
        } catch (loginError) {
          console.error('Failed to process OAuth callback:', loginError)
          console.error('OAuth error details:', loginError instanceof Error ? loginError.message : loginError)
          
          // Try to redirect back to login on failure
          setTimeout(() => {
            window.location.href = '/login'
          }, 3000)
        }
      }
      
      // Small delay for Safari compatibility
      setTimeout(processOAuth, 100)
      
    } else if (!access_token && !refresh_token && !user && !isLoading) {
      console.log('No OAuth tokens and no user - checking for existing token in storage')
      try {
        if (typeof window !== 'undefined' && window.localStorage) {
          const existingToken = localStorage.getItem('token')
          console.log('Existing token in localStorage:', existingToken ? 'present' : 'missing')
          
          if (!existingToken) {
            console.log('No existing token found, user might need to login')
          }
        }
      } catch (error) {
        console.error('Failed to check localStorage for existing token:', error)
      }
    }
  }, [searchParams, login, user, isLoading])

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

      {/* Debug tools - only in development */}
      {process.env.NODE_ENV === 'development' && (
        <>
          <AuthDiagnostics />
          {!user && <AuthResetButton />}
        </>
      )}
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
