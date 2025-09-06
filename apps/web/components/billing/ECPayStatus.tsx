'use client'

import { useState, useEffect } from 'react'
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ExclamationTriangleIcon,
  InformationCircleIcon,
  CreditCardIcon 
} from '@heroicons/react/24/outline'
import { apiClient } from '@/lib/api'

export function ECPayStatus() {
  const [apiStatus, setApiStatus] = useState<'checking' | 'available' | 'unavailable'>('checking')
  const [backendHealth, setBackendHealth] = useState<boolean | null>(null)

  useEffect(() => {
    checkECPayStatus()
  }, [])

  const checkECPayStatus = async () => {
    try {
      // Check if backend API is running through Next.js proxy
      const healthResponse = await fetch('/api/proxy/health', {
        method: 'GET',
        cache: 'no-store', // Health check needs to be real-time
      })
      
      if (healthResponse.ok) {
        setBackendHealth(true)
        
        // Check if subscription endpoints are available through proxy
        const subResponse = await fetch('/api/proxy/webhooks/health', {
          method: 'GET',
          cache: 'no-store', // Don't cache health checks
        })
        
        if (subResponse.ok) {
          setApiStatus('available')
        } else {
          setApiStatus('unavailable')
        }
      } else {
        setBackendHealth(false)
        setApiStatus('unavailable')
      }
    } catch (error) {
      console.error('ECPay status check failed:', error)
      setBackendHealth(false)
      setApiStatus('unavailable')
    }
  }

  const getStatusIcon = () => {
    if (apiStatus === 'checking') {
      return <div className="animate-spin rounded-full h-5 w-5 border-t-2 border-b-2 border-blue-500"></div>
    }
    
    if (backendHealth === false) {
      return <XCircleIcon className="h-5 w-5 text-red-500" />
    }
    
    if (apiStatus === 'available') {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />
    }
    
    return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />
  }

  const getStatusText = () => {
    if (apiStatus === 'checking') return '檢查中...'
    if (backendHealth === false) return 'Backend API 離線'
    if (apiStatus === 'available') return 'ECPay 整合運行中'
    return 'ECPay API 不可用'
  }

  const getStatusColor = () => {
    if (apiStatus === 'checking') return 'text-blue-600 bg-blue-50 border-blue-200'
    if (backendHealth === false) return 'text-red-600 bg-red-50 border-red-200'
    if (apiStatus === 'available') return 'text-green-600 bg-green-50 border-green-200'
    return 'text-yellow-600 bg-yellow-50 border-yellow-200'
  }

  return (
    <div className={`inline-flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-sm font-medium ${getStatusColor()}`}>
      <CreditCardIcon className="h-4 w-4" />
      {getStatusIcon()}
      <span>{getStatusText()}</span>
      {apiStatus === 'available' && (
        <span className="text-xs opacity-75">(測試模式)</span>
      )}
    </div>
  )
}