'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useI18n } from '@/contexts/i18n-context'
import { apiClient } from '@/lib/api'
import { useTranscriptionStatus, formatTimeRemaining, formatDuration, TranscriptionStatus, TranscriptionSession } from '@/hooks/useTranscriptionStatus'
import { TranscriptionProgress } from '@/components/ui/progress-bar'
import { Button } from '@/components/ui/button'
import { SpeakerWaveIcon, CloudArrowUpIcon, DocumentTextIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { usePlanLimits } from '@/hooks/usePlanLimits'
import planService, { PlanConfig } from '@/lib/services/plan.service'
import { cn } from '@/lib/theme-utils'

interface UploadState {
  status: 'idle' | 'uploading' | 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  estimatedTime?: string
  error?: string
  sessionId?: string
  fileName?: string
  taskId?: string
  currentPhase?: 'preparing' | 'creating_session' | 'uploading_file' | 'confirming' | 'starting_transcription'
  uploadSpeed?: string
}

interface AudioUploaderProps {
  sessionId: string
  onUploadComplete?: (audioSessionId: string) => void
  existingAudioSessionId?: string
  isSessionLoading?: boolean
  transcriptionStatus?: TranscriptionStatus | null
  transcriptionSession?: TranscriptionSession | null
}

export const AudioUploader: React.FC<AudioUploaderProps> = ({
  sessionId,
  onUploadComplete,
  existingAudioSessionId,
  isSessionLoading = false,
  transcriptionStatus: parentTranscriptionStatus,
  transcriptionSession: parentTranscriptionSession
}) => {
  const { t } = useI18n()
  const { checkBeforeAction, validateFile } = usePlanLimits()
  const [currentPlan, setCurrentPlan] = useState<PlanConfig | null>(null)
  
  // Set translation function for API client error messages
  useEffect(() => {
    apiClient.setTranslationFunction(t)
  }, [t])

  // Load current plan information
  useEffect(() => {
    const loadPlanInfo = async () => {
      try {
        const planStatus = await planService.getCurrentPlanStatus()
        setCurrentPlan(planStatus.currentPlan)
      } catch (error) {
        console.error('Failed to load plan info:', error)
        // Fallback to default limits if plan info fails
        setCurrentPlan(null)
      }
    }
    loadPlanInfo()
  }, [])
  const [uploadState, setUploadState] = useState<UploadState>(() => {
    // Initialize with proper status if we have an existing session
    return existingAudioSessionId 
      ? { status: 'pending', progress: 0 }
      : { status: 'idle', progress: 0 }
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [sessionTitle, setSessionTitle] = useState(`coaching-session-${sessionId}`)
  const [language, setLanguage] = useState('cmn-Hant-TW')
  const [dragActive, setDragActive] = useState(false)
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(existingAudioSessionId || null)
  const [forceUploadView, setForceUploadView] = useState<boolean>(false)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const completedCallbackRef = useRef<boolean>(false)

  // Use transcription status hook for progress tracking (fallback if parent doesn't provide)
  const {
    status: localTranscriptionStatus,
    session: localTranscriptionSession,
    loading: statusLoading,
    error: statusError,
    startPolling,
    stopPolling,
    isPolling
  } = useTranscriptionStatus(currentSessionId, {
    enablePolling: currentSessionId !== null && !parentTranscriptionStatus
  })

  // Use parent-provided status if available, otherwise use local
  const transcriptionStatus = parentTranscriptionStatus || localTranscriptionStatus
  const transcriptionSession = parentTranscriptionSession || localTranscriptionSession

  const supportedFormats = ['mp3', 'wav', 'flac', 'ogg', 'mp4', 'm4a']
  
  // Get file size limit from current plan
  const getFileSizeLimit = () => {
    const maxFileSizeMb = currentPlan?.limits?.maxFileSizeMb || 60 // Default to 60MB if plan not loaded
    return maxFileSizeMb
  }

  // Format file size for display
  const formatFileSize = (mb: number) => {
    if (mb >= 1024) {
      return `${(mb / 1024).toFixed(1)}GB`
    }
    return `${mb}MB`
  }

  // Update currentSessionId when existingAudioSessionId changes
  useEffect(() => {
    if (existingAudioSessionId && existingAudioSessionId !== currentSessionId) {
      setCurrentSessionId(existingAudioSessionId)
      // Also ensure upload state is not idle if we have an existing session
      if (uploadState.status === 'idle') {
        setUploadState(prev => ({
          ...prev,
          status: 'pending'
        }))
      }
    }
    // If existingAudioSessionId becomes null/undefined and we had one before,
    // reset currentSessionId only if upload is not in progress
    else if (!existingAudioSessionId && currentSessionId && uploadState.status === 'idle') {
      setCurrentSessionId(null)
    }
  }, [existingAudioSessionId, currentSessionId, uploadState.status])

  // Handle polling based on transcription session status
  useEffect(() => {
    if (currentSessionId && !isPolling) {
      // Start polling if session is processing or pending
      if (transcriptionSession?.status === 'processing' || transcriptionSession?.status === 'pending') {
        console.log('Starting polling for session:', currentSessionId, 'with status:', transcriptionSession?.status)
        startPolling()
      }
    }
    
    // Stop polling if session is completed or failed
    if (transcriptionSession?.status === 'completed' || transcriptionSession?.status === 'failed') {
      console.log('Stopping polling for session:', currentSessionId, 'with status:', transcriptionSession?.status)
      stopPolling()
    }
  }, [transcriptionSession?.status, currentSessionId, isPolling, startPolling, stopPolling])

  // Use useCallback to stabilize the onUploadComplete function
  const stableOnUploadComplete = useCallback(onUploadComplete || (() => {}), [onUploadComplete])

  useEffect(() => {
    // Sync upload state with transcription status
    if (transcriptionSession && transcriptionStatus) {
      if (transcriptionSession.status === 'completed') {
        setUploadState(prev => ({
          ...prev,
          status: 'completed',
          progress: 100
        }))
        
        // Only call onUploadComplete once when transcription is completed
        if (!completedCallbackRef.current && currentSessionId && onUploadComplete) {
          completedCallbackRef.current = true
          onUploadComplete(currentSessionId)
        }
      } else if (transcriptionSession.status === 'failed') {
        setUploadState(prev => ({
          ...prev,
          status: 'failed',
          progress: transcriptionStatus.progress,
          error: transcriptionSession.error_message || 'Transcription failed'
        }))
      } else if (transcriptionSession.status === 'processing') {
        setUploadState(prev => ({
          ...prev,
          status: 'processing',
          progress: transcriptionStatus.progress,
          estimatedTime: transcriptionStatus.estimated_completion ? 
            formatTimeRemaining(transcriptionStatus.estimated_completion) : undefined
        }))
      }
    }
  }, [transcriptionSession, transcriptionStatus, currentSessionId, onUploadComplete])
  
  // Reset callback ref when session changes
  useEffect(() => {
    if (currentSessionId) {
      completedCallbackRef.current = false
    }
  }, [currentSessionId])

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0])
    }
  }

  const handleFileSelect = async (file: File) => {
    // Validate file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    if (!fileExtension || !supportedFormats.includes(fileExtension)) {
      setUploadState({
        status: 'failed',
        progress: 0,
        error: t('audio.unsupportedFormat')
      })
      return
    }

    // Check plan limits including file size before accepting the file
    const fileValidationResult = await validateFile(file, { showError: false })
    if (!fileValidationResult) {
      const maxSize = formatFileSize(getFileSizeLimit())
      setUploadState({
        status: 'failed',
        progress: 0,
        error: t('audio.fileTooLarge').replace('1GB', maxSize)
      })
      return
    }

    await checkBeforeAction('create_session', async () => {
      await checkBeforeAction('transcribe', async () => {
        setSelectedFile(file)
        setUploadState({ status: 'idle', progress: 0 })
      })
    })
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    // Immediately show uploading state when user clicks upload
    setUploadState({ 
      status: 'uploading', 
      progress: 0,
      estimatedTime: t('audio.preparingUpload')
    })

    // Double-check limits before uploading
    await checkBeforeAction('create_session', async () => {
      await checkBeforeAction('transcribe', async () => {
        try {
      // Step 1: Create transcription session
      setUploadState(prev => ({ 
        ...prev, 
        currentPhase: 'creating_session',
        progress: 5,
        estimatedTime: t('audio.creatingSession')
      }))

      const session = await apiClient.createTranscriptionSession({
        title: sessionTitle.trim(),
        language: language
      })

      setUploadState(prev => ({ 
        ...prev, 
        sessionId: session.id,
        progress: 10,
        estimatedTime: t('audio.preparingUpload')
      }))
      setCurrentSessionId(session.id)

      // Step 2: Get signed upload URL
      const fileSizeMB = selectedFile.size / (1024 * 1024) // Convert bytes to MB
      const uploadData = await apiClient.getUploadUrl(session.id, selectedFile.name, fileSizeMB)
      
      setUploadState(prev => ({ 
        ...prev, 
        currentPhase: 'uploading_file',
        progress: 15,
        estimatedTime: t('audio.uploadingFile')
      }))

      // Step 3: Upload file to GCS with progress tracking
      const uploadStartTime = Date.now()
      let lastProgressUpdate = Date.now()
      
      await apiClient.uploadToGCS(uploadData.upload_url, selectedFile, (progress) => {
        const now = Date.now()
        const elapsed = (now - uploadStartTime) / 1000 // seconds
        const bytesUploaded = selectedFile.size * (progress / 100)
        
        // Calculate upload speed (only update every 500ms to avoid too frequent updates)
        if (now - lastProgressUpdate > 500 && elapsed > 1) {
          const uploadSpeed = (bytesUploaded / elapsed) / (1024 * 1024) // MB/s
          const remainingBytes = selectedFile.size - bytesUploaded
          const estimatedSeconds = remainingBytes / (bytesUploaded / elapsed)
          
          setUploadState(prev => ({ 
            ...prev, 
            currentPhase: 'uploading_file',
            progress: Math.round(15 + (progress * 0.7)), // 15% to 85% for upload progress
            uploadSpeed: uploadSpeed > 1 ? `${uploadSpeed.toFixed(1)} MB/s` : `${(uploadSpeed * 1024).toFixed(0)} KB/s`,
            estimatedTime: estimatedSeconds > 60 
              ? `${Math.ceil(estimatedSeconds / 60)} ${t('audio.minutesRemaining')}`
              : `${Math.ceil(estimatedSeconds)} ${t('audio.secondsRemaining')}`
          }))
          
          lastProgressUpdate = now
        }
      })

      setUploadState(prev => ({ 
        ...prev, 
        currentPhase: 'confirming',
        progress: 90,
        estimatedTime: t('audio.confirmingUpload')
      }))

      // Step 4: Confirm upload
      const confirmResult = await apiClient.confirmUpload(session.id)
      
      if (!confirmResult.file_exists || !confirmResult.ready_for_transcription) {
        throw new Error('File upload verification failed: ' + confirmResult.message)
      }

      setUploadState(prev => ({ 
        ...prev, 
        progress: 95,
        estimatedTime: t('audio.uploadComplete')
      }))

      // Step 5: Immediately update state to processing before API calls
      // This provides instant feedback to user
      setUploadState(prev => ({ 
        ...prev, 
        currentPhase: 'starting_transcription',
        progress: 98,
        estimatedTime: t('audio.startingTranscription')
      }))
      
      // Immediately switch to processing for better UX - no delay needed
      setUploadState(prev => ({ 
        ...prev, 
        status: 'processing',
        progress: 5, // Start with small progress for immediate visual feedback
        currentPhase: undefined,
        uploadSpeed: undefined,
        estimatedTime: t('audio.estimatedTime15to30')
      }))

      // Step 6: Update coaching session with the transcription session ID
      if (sessionId) {
        try {
          console.log('Updating coaching session:', sessionId, 'with transcription_session_id:', session.id)
          const updateResult = await apiClient.updateSession(sessionId, {
            transcription_session_id: session.id
          })
          console.log('Update coaching session result:', updateResult)
          
          // Reset force upload view after successful upload
          setForceUploadView(false)
          
          // Call onUploadComplete immediately after linking session
          if (onUploadComplete) {
            onUploadComplete(session.id)
          }
        } catch (error) {
          console.error('Failed to link transcription session to coaching session:', error)
          // Continue with transcription even if linking fails
        }
      }

      // Step 7: Start transcription processing
      const transcriptionResult = await apiClient.startTranscription(session.id)
      
      // Update with actual task ID and estimated time
      setUploadState(prev => ({ 
        ...prev, 
        estimatedTime: t('audio.estimatedTime15to30'),
        taskId: transcriptionResult.task_id,
        progress: 10 // Increase progress to show transcription started
      }))
      
      // Force immediate parent update for better UX
      console.log('✅ Transcription started, beginning polling immediately')
      if (onUploadComplete) {
        // Small delay to ensure backend state is updated
        setTimeout(() => onUploadComplete(session.id), 100)
      }
      
      // Immediately start polling after transcription starts
      console.log('Transcription started, beginning polling immediately')
      startPolling()

        } catch (error: any) {
          console.error('Upload error:', error)
          setUploadState(prev => ({
            ...prev,
            status: 'failed',
            progress: 0,
            error: error.message || t('audio.uploadFailed')
          }))
        }
      })
    })
  }

  const resetUpload = () => {
    setSelectedFile(null)
    setUploadState({ status: 'idle', progress: 0 })
    setForceUploadView(true) // Force showing upload interface
    // Only reset currentSessionId if there's no existing audio session
    if (!existingAudioSessionId) {
      setCurrentSessionId(null)
    }
    stopPolling()
  }

  // Show loading state while session is being fetched
  if (isSessionLoading) {
    return (
      <div className="space-y-4">
        <div className="flex items-center justify-center p-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          <span className="ml-3 text-content-secondary">{t('audio.loadingAudioStatus')}</span>
        </div>
      </div>
    )
  }

  // If we have an existing audio session ID and not forcing upload view, show status view instead of upload interface
  if ((currentSessionId || existingAudioSessionId) && !forceUploadView) {
    return (
      <div className="space-y-4">
        {/* Current Status */}
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-content-primary">{t('audio.processingStatus')}</h4>
          {statusLoading ? (
            <span className="text-sm text-gray-500 font-medium">{t('audio.checkingStatus')}</span>
          ) : transcriptionSession?.status === 'completed' ? (
            <span className="text-sm text-green-600 font-medium">{t('audio.processingComplete')}</span>
          ) : transcriptionSession?.status === 'processing' ? (
            <span className="text-sm text-yellow-600 font-medium">{t('audio.status_processing')}</span>
          ) : transcriptionSession?.status === 'failed' ? (
            <span className="text-sm text-red-600 font-medium">{t('audio.processingFailed')}</span>
          ) : transcriptionSession?.status === 'pending' ? (
            <span className="text-sm text-blue-600 font-medium">{t('audio.waitingToProcess')}</span>
          ) : (
            <span className="text-sm text-gray-500 font-medium">{t('audio.audioUploaded')}</span>
          )}
        </div>

        {/* Progress Display */}
        {(uploadState.status === 'processing' || 
          transcriptionSession?.status === 'processing' ||
          transcriptionSession?.status === 'pending' ||
          transcriptionSession?.status === 'completed') && (
          <div className={cn(
            "rounded-lg p-4 border",
            transcriptionSession?.status === 'completed' 
              ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
              : "bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800"
          )}>
            <TranscriptionProgress
              progress={(() => {
                // Always ensure we have a valid progress value
                let progressValue = 0;
                
                if (transcriptionSession?.status === 'completed') {
                  // Show 100% for completed status
                  progressValue = 100;
                } else if (transcriptionStatus?.progress != null) {
                  progressValue = Number(transcriptionStatus.progress);
                } else if (uploadState.progress != null) {
                  progressValue = Number(uploadState.progress);
                }
                
                // For pending status, show a small progress to indicate activity
                if (transcriptionSession?.status === 'pending' && progressValue === 0) {
                  progressValue = 5;
                }
                
                console.log('TranscriptionProgress debug:', {
                  transcriptionStatus: transcriptionStatus,
                  transcriptionSession: transcriptionSession,
                  uploadState: uploadState,
                  rawProgress: transcriptionStatus?.progress,
                  finalProgress: progressValue,
                  currentSessionId: currentSessionId,
                  sessionStatus: transcriptionSession?.status
                });
                
                return Math.max(0, Math.min(100, progressValue));
              })()}
              status={transcriptionSession?.status === 'pending' ? 'pending' : 
                      transcriptionSession?.status === 'failed' ? 'failed' :
                      transcriptionSession?.status === 'completed' ? 'completed' : 'processing'}
              message={transcriptionStatus?.message || 
                (transcriptionSession?.status === 'pending' ? t('audio.waitingToStart') : t('audio.processingAudio'))}
              estimatedTime={transcriptionStatus?.estimated_completion ? 
                formatTimeRemaining(transcriptionStatus.estimated_completion) : uploadState.estimatedTime}
            />
            {transcriptionStatus?.duration_processed != null && 
             transcriptionStatus?.duration_total != null && 
             transcriptionStatus.duration_total > 0 && (
              <div className="mt-2 text-sm text-yellow-800 dark:text-yellow-200">
                {t('audio.processed')}: {formatDuration(transcriptionStatus.duration_processed)} / {formatDuration(transcriptionStatus.duration_total)}
              </div>
            )}
          </div>
        )}

        {/* Error Display */}
        {uploadState.status === 'failed' && (
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center gap-2">
              <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
              <span className="text-sm text-red-800 dark:text-red-200">{uploadState.error}</span>
            </div>
          </div>
        )}

        {/* Upload New File Option */}
        <div className="pt-4 border-t border-border">
          <Button
            onClick={resetUpload}
            variant="outline"
            className="text-sm"
          >
            {t('audio.uploadNewAudio')}
          </Button>
        </div>
      </div>
    )
  }

  // Upload interface
  return (
    <div className="space-y-4">
      {/* Upload Area */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          dragActive 
            ? 'border-blue-400 bg-blue-50 dark:bg-blue-900/20' 
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".mp3,.wav,.flac,.ogg,.mp4,.m4a"
          onChange={handleFileInputChange}
          className="hidden"
        />

        {uploadState.status === 'uploading' ? (
          <div className="space-y-4">
            <SpeakerWaveIcon className="h-12 w-12 text-blue-500 mx-auto animate-pulse" />
            <div className="space-y-3">
              <div className="text-center">
                <p className="text-content-primary font-medium">{t('audio.uploading')}</p>
                {uploadState.currentPhase && (
                  <p className="text-sm text-content-secondary">
                    {uploadState.currentPhase === 'creating_session' && t('audio.creatingSession')}
                    {uploadState.currentPhase === 'uploading_file' && t('audio.uploadingFile')}
                    {uploadState.currentPhase === 'confirming' && t('audio.confirmingUpload')}
                    {uploadState.currentPhase === 'starting_transcription' && t('audio.startingTranscription')}
                  </p>
                )}
              </div>
              
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-3">
                <div 
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-300 flex items-center justify-end pr-2"
                  style={{ width: `${Math.max(uploadState.progress, 2)}%` }}
                >
                  <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                </div>
              </div>
              
              <div className="flex justify-between text-sm">
                <span className="text-content-secondary">{uploadState.progress}%</span>
                <div className="text-right text-content-secondary">
                  {uploadState.uploadSpeed && (
                    <div>{uploadState.uploadSpeed}</div>
                  )}
                  {uploadState.estimatedTime && (
                    <div>{uploadState.estimatedTime}</div>
                  )}
                </div>
              </div>
              
              {selectedFile && (
                <div className="text-center">
                  <p className="text-xs text-content-secondary">
                    {selectedFile.name} • {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              )}
            </div>
          </div>
        ) : selectedFile ? (
          <div className="space-y-4">
            <DocumentTextIcon className="h-12 w-12 text-green-500 mx-auto" />
            <div>
              <p className="text-content-primary font-medium">{t('audio.fileSelected')}</p>
              <p className="text-sm text-content-secondary">{selectedFile.name}</p>
              <p className="text-xs text-content-secondary">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
            <div className="space-y-2">
              <Button onClick={handleUpload} className="w-full">
                {t('audio.startProcessing')}
              </Button>
              <Button onClick={resetUpload} variant="outline" className="w-full">
                {t('audio.reselect')}
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <CloudArrowUpIcon className="h-12 w-12 text-content-secondary mx-auto" />
            <div>
              <p className="text-content-primary font-medium">{t('audio.uploadForTranscription')}</p>
              <p className="text-sm text-content-secondary">
                {t('audio.dragDropFiles')}
              </p>
              <p className="text-xs text-content-secondary">
                {t('audio.supportedFormats')} • {t('audio.maxFileSize').replace('1GB', formatFileSize(getFileSizeLimit()))}
              </p>
            </div>
            <Button onClick={() => fileInputRef.current?.click()} className="mx-auto">
              {t('audio.selectFiles')}
            </Button>
          </div>
        )}
      </div>

      {/* Settings */}
      {selectedFile && (
        <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-content-primary mb-2">
              {t('audio.languageSettings')}
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-surface text-content-primary"
            >
              <option value="cmn-Hant-TW">{t('audio.langTraditionalChinese')}</option>
              <option value="cmn-Hans-CN">{t('audio.langSimplifiedChinese')}</option>
              <option value="en-US">English (US)</option>
              <option value="ja-JP">{t('audio.langJapanese')}</option>
              <option value="ko-KR">한국어</option>
            </select>
          </div>
        </div>
      )}

      {/* Error Display */}
      {uploadState.status === 'failed' && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="h-5 w-5 text-red-600" />
            <span className="text-sm text-red-800 dark:text-red-200">{uploadState.error}</span>
          </div>
        </div>
      )}
    </div>
  )
}