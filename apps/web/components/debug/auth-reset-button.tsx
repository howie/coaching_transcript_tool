'use client'

import { useAuth } from '@/contexts/auth-context'

export function AuthResetButton() {
  const { logout } = useAuth()

  const handleReset = () => {
    try {
      // Clear all auth-related localStorage items
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('userPreferences')
      localStorage.removeItem('language')
      
      console.log('Cleared all auth tokens from localStorage')
      
      // Call logout to reset auth state
      logout()
      
      // Redirect to login page
      setTimeout(() => {
        window.location.href = '/login'
      }, 500)
    } catch (error) {
      console.error('Failed to reset auth:', error)
    }
  }

  return (
    <button
      onClick={handleReset}
      className="fixed bottom-4 left-4 z-50 bg-red-500 text-white px-3 py-2 rounded-md text-sm hover:bg-red-600 transition-colors"
    >
      🔄 重置認證
    </button>
  )
}