import React from 'react'
import { cn } from '@/lib/theme-utils'

interface ProgressBarProps {
  progress: number // 0-100
  status?: 'pending' | 'processing' | 'completed' | 'failed'
  showPercentage?: boolean
  size?: 'sm' | 'md' | 'lg'
  animated?: boolean
  className?: string
  children?: React.ReactNode
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  status = 'processing',
  showPercentage = true,
  size = 'md',
  animated = false,
  className,
  children
}) => {
  const clampedProgress = Math.round(Math.max(0, Math.min(100, progress)))
  
  const getBarColor = () => {
    switch (status) {
      case 'completed':
        return 'bg-green-500'
      case 'failed':
        return 'bg-red-500'
      case 'pending':
        return 'bg-gray-400'
      default:
        if (clampedProgress >= 90) return 'bg-blue-500'
        return 'bg-blue-400'
    }
  }

  const getBarHeight = () => {
    switch (size) {
      case 'sm':
        return 'h-1.5'
      case 'lg':
        return 'h-3'
      default:
        return 'h-2'
    }
  }

  const getTextSize = () => {
    switch (size) {
      case 'sm':
        return 'text-xs'
      case 'lg':
        return 'text-base'
      default:
        return 'text-sm'
    }
  }

  return (
    <div className={cn('w-full', className)}>
      {(showPercentage || children) && (
        <div className={cn('flex items-center justify-between mb-2', getTextSize())}>
          {children && (
            <div className="flex items-center space-x-2">
              {children}
            </div>
          )}
          {showPercentage && (
            <span className="font-medium text-gray-700 dark:text-gray-300">
              {Math.round(clampedProgress)}%
            </span>
          )}
        </div>
      )}
      
      <div className={cn(
        'w-full bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden',
        getBarHeight()
      )}>
        <div
          className={cn(
            'transition-all duration-500 ease-out rounded-full',
            getBarColor(),
            {
              'animate-pulse': animated && status === 'processing'
            }
          )}
          style={{ 
            width: `${clampedProgress}%`,
            transition: 'width 0.5s ease-out'
          }}
        />
      </div>
    </div>
  )
}

// Specialized progress bar for transcription status
interface TranscriptionProgressProps {
  progress: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  message?: string
  estimatedTime?: string
  showDetails?: boolean
  className?: string
}

export const TranscriptionProgress: React.FC<TranscriptionProgressProps> = ({
  progress,
  status,
  message,
  estimatedTime,
  showDetails = true,
  className
}) => {
  const getStatusIcon = () => {
    switch (status) {
      case 'processing':
        return (
          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
        )
      case 'completed':
        return (
          <div className="w-4 h-4 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )
      case 'failed':
        return (
          <div className="w-4 h-4 bg-red-100 rounded-full flex items-center justify-center">
            <svg className="w-3 h-3 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </div>
        )
      default:
        return (
          <div className="w-4 h-4 bg-gray-100 rounded-full flex items-center justify-center">
            <div className="w-2 h-2 bg-gray-400 rounded-full"></div>
          </div>
        )
    }
  }

  const getStatusText = () => {
    switch (status) {
      case 'pending':
        return 'Pending'
      case 'processing':
        return 'Processing'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
      default:
        return 'Unknown'
    }
  }

  return (
    <div className={cn('space-y-3', className)}>
      <ProgressBar
        progress={progress}
        status={status}
        showPercentage={true}
        animated={status === 'processing'}
      >
        <div className="flex items-center space-x-2">
          {getStatusIcon()}
          <span className="font-medium text-gray-900 dark:text-gray-100">
            {getStatusText()}
          </span>
        </div>
      </ProgressBar>
      
      {showDetails && (message || estimatedTime) && (
        <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
          {message && (
            <div className="flex items-center">
              <span>{message}</span>
            </div>
          )}
          {estimatedTime && status === 'processing' && (
            <div className="flex items-center justify-between">
              <span>Estimated time remaining:</span>
              <span className="font-medium">{estimatedTime}</span>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// Compact progress indicator for small spaces
interface ProgressIndicatorProps {
  progress: number
  status: 'pending' | 'processing' | 'completed' | 'failed'
  size?: 'sm' | 'md'
  className?: string
}

export const ProgressIndicator: React.FC<ProgressIndicatorProps> = ({
  progress,
  status,
  size = 'sm',
  className
}) => {
  const getSize = () => {
    return size === 'sm' ? 'w-16 h-16' : 'w-20 h-20'
  }

  const getStrokeWidth = () => {
    return size === 'sm' ? '2' : '3'
  }

  const getColor = () => {
    switch (status) {
      case 'completed':
        return 'text-green-500'
      case 'failed':
        return 'text-red-500'
      case 'pending':
        return 'text-gray-400'
      default:
        return 'text-blue-500'
    }
  }

  const radius = size === 'sm' ? 28 : 34
  const circumference = 2 * Math.PI * radius
  const strokeDasharray = circumference
  const strokeDashoffset = circumference - (progress / 100) * circumference

  return (
    <div className={cn('relative', getSize(), className)}>
      <svg className="transform -rotate-90 w-full h-full" viewBox="0 0 64 64">
        {/* Background circle */}
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={getStrokeWidth()}
          className="text-gray-200 dark:text-gray-700"
        />
        {/* Progress circle */}
        <circle
          cx="32"
          cy="32"
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth={getStrokeWidth()}
          strokeLinecap="round"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          className={cn(
            'transition-all duration-300 ease-out',
            getColor(),
            {
              'animate-pulse': status === 'processing'
            }
          )}
        />
      </svg>
      {/* Center content */}
      <div className="absolute inset-0 flex items-center justify-center">
        <span className={cn(
          'font-bold',
          size === 'sm' ? 'text-xs' : 'text-sm',
          getColor()
        )}>
          {Math.round(progress)}%
        </span>
      </div>
    </div>
  )
}