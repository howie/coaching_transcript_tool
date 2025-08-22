import { useState, useEffect, useRef, useCallback } from 'react'
import { apiClient } from '@/lib/api'

export interface TranscriptionStatus {
  session_id: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  message?: string
  duration_processed?: number
  duration_total?: number
  started_at?: string
  estimated_completion?: string
  processing_speed?: number
  created_at: string
  updated_at: string
}

export interface TranscriptionSession {
  id: string
  title: string
  status: 'uploading' | 'pending' | 'processing' | 'completed' | 'failed'
  language: string
  audio_filename?: string
  duration_sec?: number
  duration_minutes?: number
  segments_count: number
  error_message?: string
  stt_cost_usd?: string
  created_at: string
  updated_at: string
}

interface UseTranscriptionStatusOptions {
  pollInterval?: number // milliseconds, default 3000 (3 seconds for faster updates)
  maxPollingTime?: number // milliseconds, default 2 hours
  enablePolling?: boolean // default true
}

interface UseTranscriptionStatusReturn {
  status: TranscriptionStatus | null
  session: TranscriptionSession | null
  loading: boolean
  error: string | null
  startPolling: () => void
  stopPolling: () => void
  isPolling: boolean
  refetch: () => Promise<void>
}

export const useTranscriptionStatus = (
  sessionId: string | null,
  options: UseTranscriptionStatusOptions = {}
): UseTranscriptionStatusReturn => {
  const {
    pollInterval = 3000, // Reduced from 5s to 3s for faster UI updates
    maxPollingTime = 2 * 60 * 60 * 1000, // 2 hours
    enablePolling = true
  } = options

  const [status, setStatus] = useState<TranscriptionStatus | null>(null)
  const [session, setSession] = useState<TranscriptionSession | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [isPolling, setIsPolling] = useState(false)

  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null)
  const startTimeRef = useRef<number | null>(null)

  const fetchStatus = useCallback(async (): Promise<{ session: any; status: any } | null> => {
    if (!sessionId) return null

    try {
      setLoading(true)
      setError(null)

      // Fetch both session data and status
      const [sessionData, statusData] = await Promise.all([
        apiClient.getTranscriptionSession(sessionId),
        apiClient.getTranscriptionStatus(sessionId)
      ])

      setSession(sessionData)
      setStatus(statusData)

      return { session: sessionData, status: statusData }
    } catch (err: any) {
      console.error('Error fetching transcription status:', err)
      setError(err.message || 'Failed to fetch status')
      return null
    } finally {
      setLoading(false)
    }
  }, [sessionId])
  
  const refetch = useCallback(async (): Promise<void> => {
    await fetchStatus()
  }, [fetchStatus])

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    setIsPolling(false)
    startTimeRef.current = null
  }, [])

  const startPolling = useCallback(() => {
    if (!sessionId || !enablePolling) return

    // Clear any existing polling first
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current)
      pollingIntervalRef.current = null
    }
    
    startTimeRef.current = Date.now()
    setIsPolling(true)

    const poll = async () => {
      // Check for timeout
      if (startTimeRef.current && Date.now() - startTimeRef.current > maxPollingTime) {
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }
        setIsPolling(false)
        startTimeRef.current = null
        setError('Polling timed out. The transcription may still be processing.')
        return
      }

      const result = await fetchStatus()
      if (!result) {
        // Error occurred, continue polling but with exponential backoff
        pollingIntervalRef.current = setTimeout(poll, pollInterval * 2)
        return
      }

      const { session: sessionData, status: statusData } = result

      // Check if we should stop polling
      const shouldStopPolling = 
        sessionData.status === 'completed' || 
        sessionData.status === 'failed' ||
        statusData.status === 'completed' ||
        statusData.status === 'failed'

      console.log('Initial polling check:', {
        sessionId,
        sessionStatus: sessionData.status,
        statusDataStatus: statusData.status,
        shouldStopPolling,
        isPolling
      })

      if (shouldStopPolling) {
        console.log('Stopping initial polling for sessionId:', sessionId)
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current)
          pollingIntervalRef.current = null
        }
        setIsPolling(false)
        startTimeRef.current = null
      } else {
        console.log('Continuing initial polling for sessionId:', sessionId)
        // Use faster polling for initial state transitions (first 30 seconds)
        const elapsedTime = Date.now() - (startTimeRef.current || Date.now())
        const interval = elapsedTime < 30000 ? 1500 : pollInterval // 1.5s for first 30s, then normal
        pollingIntervalRef.current = setTimeout(poll, interval)
      }
    }

    // Start initial poll
    poll()
  }, [sessionId, enablePolling, maxPollingTime, pollInterval])

  // Auto-start polling when session changes and is processing
  useEffect(() => {
    if (!sessionId) {
      // Clear any existing polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
      setIsPolling(false)
      startTimeRef.current = null
      return
    }

    // Fetch initial status
    const initializeStatus = async () => {
      try {
        setLoading(true)
        setError(null)

        const [sessionData, statusData] = await Promise.all([
          apiClient.getTranscriptionSession(sessionId),
          apiClient.getTranscriptionStatus(sessionId)
        ])

        setSession(sessionData)
        setStatus(statusData)

        if ((sessionData.status === 'processing' || statusData.status === 'processing') && enablePolling) {
          // Start polling inline to avoid callback dependencies
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current)
            pollingIntervalRef.current = null
          }
          
          startTimeRef.current = Date.now()
          setIsPolling(true)

          const poll = async () => {
            if (startTimeRef.current && Date.now() - startTimeRef.current > maxPollingTime) {
              if (pollingIntervalRef.current) {
                clearInterval(pollingIntervalRef.current)
                pollingIntervalRef.current = null
              }
              setIsPolling(false)
              startTimeRef.current = null
              setError('Polling timed out. The transcription may still be processing.')
              return
            }

            try {
              const [sessionData, statusData] = await Promise.all([
                apiClient.getTranscriptionSession(sessionId),
                apiClient.getTranscriptionStatus(sessionId)
              ])

              setSession(sessionData)
              setStatus(statusData)

              const shouldStopPolling = 
                sessionData.status === 'completed' || 
                sessionData.status === 'failed' ||
                statusData.status === 'completed' ||
                statusData.status === 'failed'

              console.log('Polling check:', {
                sessionId,
                sessionStatus: sessionData.status,
                statusDataStatus: statusData.status,
                shouldStopPolling,
                isPolling
              })

              if (shouldStopPolling) {
                console.log('Stopping polling for sessionId:', sessionId)
                if (pollingIntervalRef.current) {
                  clearInterval(pollingIntervalRef.current)
                  pollingIntervalRef.current = null
                }
                setIsPolling(false)
                startTimeRef.current = null
              } else {
                console.log('Continuing polling for sessionId:', sessionId)
                // Use faster polling for initial state transitions (first 30 seconds)
                const elapsedTime = Date.now() - (startTimeRef.current || Date.now())
                const interval = elapsedTime < 30000 ? 1500 : pollInterval // 1.5s for first 30s
                pollingIntervalRef.current = setTimeout(poll, interval)
              }
            } catch (err: any) {
              console.error('Error fetching transcription status:', err)
              pollingIntervalRef.current = setTimeout(poll, pollInterval * 2)
            }
          }

          poll()
        }
      } catch (err: any) {
        console.error('Error fetching transcription status:', err)
        setError(err.message || 'Failed to fetch status')
      } finally {
        setLoading(false)
      }
    }

    initializeStatus()

    // Cleanup on unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current)
        pollingIntervalRef.current = null
      }
      setIsPolling(false)
      startTimeRef.current = null
    }
  }, [sessionId, enablePolling, maxPollingTime, pollInterval])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling()
    }
  }, [stopPolling])

  return {
    status,
    session,
    loading,
    error,
    startPolling,
    stopPolling,
    isPolling,
    refetch
  }
}

// Helper functions for formatting
export const formatTimeRemaining = (estimatedCompletion?: string): string => {
  if (!estimatedCompletion) return ''
  
  const now = new Date()
  const completion = new Date(estimatedCompletion)
  const diffMs = completion.getTime() - now.getTime()
  
  if (diffMs <= 0) return 'Almost done'
  
  const minutes = Math.ceil(diffMs / (1000 * 60))
  if (minutes <= 1) return 'Less than 1 minute'
  if (minutes < 60) return `~${minutes} minutes`
  
  const hours = Math.floor(minutes / 60)
  const remainingMinutes = minutes % 60
  
  if (hours === 1) {
    return remainingMinutes > 0 ? `~1 hour ${remainingMinutes} minutes` : '~1 hour'
  }
  
  return remainingMinutes > 0 ? `~${hours} hours ${remainingMinutes} minutes` : `~${hours} hours`
}

export const formatDuration = (seconds?: number): string => {
  if (!seconds) return '0:00'
  
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = Math.floor(seconds % 60)
  
  if (hours > 0) {
    return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
  }
  
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

export const getProgressColor = (progress: number, status: string): string => {
  if (status === 'failed') return 'bg-red-500'
  if (status === 'completed') return 'bg-green-500'
  if (progress >= 90) return 'bg-blue-500'
  if (progress >= 50) return 'bg-blue-500'
  return 'bg-blue-400'
}

export const getStatusMessage = (
  status: string, 
  progress: number, 
  message?: string
): string => {
  if (message) return message
  
  switch (status) {
    case 'pending':
      return 'Waiting to start processing...'
    case 'processing':
      if (progress >= 90) return 'Almost done!'
      if (progress >= 75) return 'Finalizing transcription...'
      if (progress >= 50) return 'Processing audio segments...'
      if (progress >= 25) return 'Analyzing speech patterns...'
      return 'Starting audio processing...'
    case 'completed':
      return 'Transcription completed successfully!'
    case 'failed':
      return 'Transcription failed. Please try again.'
    default:
      return 'Processing...'
  }
}