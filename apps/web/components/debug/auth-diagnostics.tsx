'use client'

import { useAuth } from '@/contexts/auth-context'
import { useSearchParams } from 'next/navigation'
import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api'

interface DiagnosticInfo {
  userAgent: string
  isSafari: boolean
  localStorageAvailable: boolean
  cookiesEnabled: boolean
  currentURL: string
  searchParams: Record<string, string>
  localStorageContents: Record<string, string>
  authState: {
    user: any
    isLoading: boolean
    isAuthenticated: boolean
  }
  apiConnectivity: {
    healthCheck: 'pending' | 'success' | 'failed'
    healthCheckError?: string
    apiBaseUrl: string
  }
}

export function AuthDiagnostics() {
  const { user, isLoading, isAuthenticated } = useAuth()
  const searchParams = useSearchParams()
  const [diagnostics, setDiagnostics] = useState<DiagnosticInfo | null>(null)
  const [showDiagnostics, setShowDiagnostics] = useState(false)

  useEffect(() => {
    // Only run in development mode
    if (process.env.NODE_ENV !== 'development') {
      return
    }
    const runDiagnostics = () => {
      try {
        // Gather diagnostic information
        const userAgent = navigator.userAgent
        const isSafari = /^((?!chrome|android).)*safari/i.test(userAgent)
        
        // Test localStorage availability
        let localStorageAvailable = false
        let localStorageContents: Record<string, string> = {}
        try {
          localStorage.setItem('test', 'test')
          localStorage.removeItem('test')
          localStorageAvailable = true
          
          // Get all localStorage contents
          for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i)
            if (key) {
              localStorageContents[key] = localStorage.getItem(key) || ''
            }
          }
        } catch (e) {
          localStorageAvailable = false
        }

        // Test cookies
        const cookiesEnabled = navigator.cookieEnabled

        // Get URL and search params
        const currentURL = window.location.href
        const searchParamsObj: Record<string, string> = {}
        searchParams.forEach((value, key) => {
          searchParamsObj[key] = value
        })

        // Test API connectivity
        const testApiConnectivity = async () => {
          const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          try {
            await apiClient.healthCheck()
            return { healthCheck: 'success' as const, apiBaseUrl }
          } catch (error) {
            return { 
              healthCheck: 'failed' as const, 
              healthCheckError: error instanceof Error ? error.message : 'Unknown error',
              apiBaseUrl 
            }
          }
        }

        testApiConnectivity().then(apiConnectivity => {
          setDiagnostics({
            userAgent,
            isSafari,
            localStorageAvailable,
            cookiesEnabled,
            currentURL,
            searchParams: searchParamsObj,
            localStorageContents,
            authState: {
              user,
              isLoading,
              isAuthenticated
            },
            apiConnectivity
          })
        })
      } catch (error) {
        console.error('Failed to run diagnostics:', error)
      }
    }

    runDiagnostics()
    
    // Re-run diagnostics when auth state changes
    const interval = setInterval(runDiagnostics, 2000)
    return () => clearInterval(interval)
  }, [user, isLoading, isAuthenticated, searchParams])

  // Auto-show diagnostics if we're on Safari and not authenticated
  useEffect(() => {
    if (diagnostics?.isSafari && !isAuthenticated && !isLoading) {
      setShowDiagnostics(true)
    }
  }, [diagnostics, isAuthenticated, isLoading])

  // Only render in development mode
  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  if (!diagnostics) {
    return null
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setShowDiagnostics(!showDiagnostics)}
        className="bg-blue-500 text-white px-3 py-2 rounded-md text-sm hover:bg-blue-600 transition-colors"
      >
        🔍 診斷
      </button>

      {showDiagnostics && (
        <div className="absolute bottom-12 right-0 bg-white border border-gray-300 rounded-lg shadow-lg p-4 max-w-md max-h-96 overflow-auto">
          <div className="mb-3 flex justify-between items-center">
            <h3 className="font-bold text-foreground">認證診斷</h3>
            <button
              onClick={() => setShowDiagnostics(false)}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <div className="space-y-2 text-xs">
            {/* Browser Info */}
            <div className="border-b pb-2">
              <div className="font-semibold">瀏覽器資訊</div>
              <div>Safari: {diagnostics.isSafari ? '✅' : '❌'}</div>
              <div>localStorage: {diagnostics.localStorageAvailable ? '✅' : '❌'}</div>
              <div>Cookies: {diagnostics.cookiesEnabled ? '✅' : '❌'}</div>
            </div>

            {/* Auth State */}
            <div className="border-b pb-2">
              <div className="font-semibold">認證狀態</div>
              <div>已認證: {diagnostics.authState.isAuthenticated ? '✅' : '❌'}</div>
              <div>載入中: {diagnostics.authState.isLoading ? '⏳' : '✅'}</div>
              <div>用戶: {diagnostics.authState.user?.name || '無'}</div>
              <div>Email: {diagnostics.authState.user?.email || '無'}</div>
            </div>

            {/* URL and Params */}
            <div className="border-b pb-2">
              <div className="font-semibold">URL 參數</div>
              <div className="break-all">URL: {diagnostics.currentURL}</div>
              {Object.keys(diagnostics.searchParams).length > 0 ? (
                Object.entries(diagnostics.searchParams).map(([key, value]) => (
                  <div key={key}>{key}: {value}</div>
                ))
              ) : (
                <div>無 URL 參數</div>
              )}
            </div>

            {/* API Connectivity */}
            <div className="border-b pb-2">
              <div className="font-semibold">API 連通性</div>
              <div>API URL: {diagnostics.apiConnectivity.apiBaseUrl}</div>
              <div>健康檢查: {
                diagnostics.apiConnectivity.healthCheck === 'success' ? '✅' :
                diagnostics.apiConnectivity.healthCheck === 'failed' ? '❌' : '⏳'
              }</div>
              {diagnostics.apiConnectivity.healthCheckError && (
                <div className="text-red-600">錯誤: {diagnostics.apiConnectivity.healthCheckError}</div>
              )}
            </div>

            {/* localStorage Contents */}
            <div>
              <div className="font-semibold">localStorage 內容</div>
              {Object.keys(diagnostics.localStorageContents).length > 0 ? (
                Object.entries(diagnostics.localStorageContents).map(([key, value]) => (
                  <div key={key} className="break-all">
                    {key}: {value.length > 50 ? value.substring(0, 50) + '...' : value}
                  </div>
                ))
              ) : (
                <div>localStorage 為空</div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}