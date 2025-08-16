'use client'

import { useState, useRef, useEffect, useCallback } from 'react'
import { useI18n } from '@/contexts/i18n-context'
import { apiClient } from '@/lib/api'
import { useTranscriptionStatus, formatTimeRemaining, formatDuration, TranscriptionStatus, TranscriptionSession } from '@/hooks/useTranscriptionStatus'
import { TranscriptionProgress } from '@/components/ui/progress-bar'
import { Button } from '@/components/ui/button'
import { SpeakerWaveIcon, CloudArrowUpIcon, DocumentTextIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'
import { usePlanLimits } from '@/hooks/usePlanLimits'

interface UploadState {
  status: 'idle' | 'uploading' | 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  estimatedTime?: string
  error?: string
  sessionId?: string
  fileName?: string
  taskId?: string
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
  const { checkBeforeAction } = usePlanLimits()
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
    enablePolling: currentSessionId !== null && uploadState.status === 'processing' && !parentTranscriptionStatus
  })

  // Use parent-provided status if available, otherwise use local
  const transcriptionStatus = parentTranscriptionStatus || localTranscriptionStatus
  const transcriptionSession = parentTranscriptionSession || localTranscriptionSession

  const supportedFormats = ['mp3', 'wav', 'flac', 'ogg', 'mp4', 'm4a']
  const maxFileSize = 1 * 1024 * 1024 * 1024 // 1GB

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
  }, [existingAudioSessionId])

  // Handle polling based on transcription session status
  useEffect(() => {
    if (currentSessionId && transcriptionSession?.status === 'processing' && !isPolling) {
      startPolling()
    } else if (transcriptionSession?.status === 'completed' || transcriptionSession?.status === 'failed') {
      stopPolling()
    }
  }, [transcriptionSession?.status, currentSessionId, isPolling])

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
  }, [transcriptionSession?.status, transcriptionStatus?.progress, currentSessionId])
  
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
        error: '不支援的檔案格式。請上傳 MP3、WAV、FLAC、OGG、MP4 或 M4A 檔案。'
      })
      return
    }

    // Validate file size
    if (file.size > maxFileSize) {
      setUploadState({
        status: 'failed',
        progress: 0,
        error: '檔案太大。最大支援 1GB。'
      })
      return
    }

    // Check plan limits before accepting the file
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

    // Double-check limits before uploading
    await checkBeforeAction('create_session', async () => {
      await checkBeforeAction('transcribe', async () => {
        setUploadState({ status: 'uploading', progress: 0 })

        try {
      // Step 1: Create transcription session
      const session = await apiClient.createTranscriptionSession({
        title: sessionTitle.trim(),
        language: language
      })

      setUploadState(prev => ({ 
        ...prev, 
        sessionId: session.id,
        progress: 10
      }))
      setCurrentSessionId(session.id)

      // Step 2: Get signed upload URL
      const uploadData = await apiClient.getUploadUrl(session.id, selectedFile.name)
      
      setUploadState(prev => ({ 
        ...prev, 
        progress: 20
      }))

      // Step 3: Upload file to GCS with progress tracking
      await apiClient.uploadToGCS(uploadData.upload_url, selectedFile, (progress) => {
        setUploadState(prev => ({ 
          ...prev, 
          progress: Math.round(20 + (progress * 0.6)) // 20% to 80% for upload progress
        }))
      })

      setUploadState(prev => ({ 
        ...prev, 
        progress: 90
      }))

      // Step 4: Confirm upload
      const confirmResult = await apiClient.confirmUpload(session.id)
      
      if (!confirmResult.file_exists || !confirmResult.ready_for_transcription) {
        throw new Error('File upload verification failed: ' + confirmResult.message)
      }

      setUploadState(prev => ({ 
        ...prev, 
        progress: 100
      }))

      // Step 5: Immediately update state to processing before API calls
      // This provides instant feedback to user
      setUploadState(prev => ({ 
        ...prev, 
        status: 'processing',
        progress: 0,
        estimatedTime: '準備開始轉檔...'
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
        estimatedTime: '約 15-30 分鐘',
        taskId: transcriptionResult.task_id
      }))

        } catch (error: any) {
          console.error('Upload error:', error)
          setUploadState(prev => ({
            ...prev,
            status: 'failed',
            progress: 0,
            error: error.message || '上傳失敗'
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
          <span className="ml-3 text-content-secondary">載入音檔狀態中...</span>
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
          <h4 className="font-medium text-content-primary">音檔處理狀態</h4>
          {statusLoading ? (
            <span className="text-sm text-gray-500 font-medium">🔍 檢查狀態中...</span>
          ) : transcriptionSession?.status === 'completed' ? (
            <span className="text-sm text-green-600 font-medium">✅ 處理完成</span>
          ) : transcriptionSession?.status === 'processing' ? (
            <span className="text-sm text-yellow-600 font-medium">⏳ 處理中</span>
          ) : transcriptionSession?.status === 'failed' ? (
            <span className="text-sm text-red-600 font-medium">❌ 處理失敗</span>
          ) : transcriptionSession?.status === 'pending' ? (
            <span className="text-sm text-blue-600 font-medium">⏱️ 等待處理</span>
          ) : (
            <span className="text-sm text-gray-500 font-medium">📁 音檔已上傳</span>
          )}
        </div>

        {/* Progress Display */}
        {(uploadState.status === 'processing' || 
          transcriptionSession?.status === 'processing' ||
          transcriptionSession?.status === 'pending') ? (
          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <TranscriptionProgress
              progress={(() => {
                const progressValue = Number(transcriptionStatus?.progress) || Number(uploadState.progress) || 0;
                console.log('TranscriptionProgress debug:', {
                  transcriptionStatus: transcriptionStatus,
                  transcriptionSession: transcriptionSession,
                  uploadState: uploadState,
                  rawProgress: transcriptionStatus?.progress,
                  finalProgress: progressValue,
                  currentSessionId: currentSessionId
                });
                return progressValue;
              })()}
              status={transcriptionSession?.status === 'pending' ? 'pending' : 'processing'}
              message={transcriptionStatus?.message || 
                (transcriptionSession?.status === 'pending' ? '等待開始處理...' : '處理音檔中...')}
              estimatedTime={transcriptionStatus?.estimated_completion ? 
                formatTimeRemaining(transcriptionStatus.estimated_completion) : uploadState.estimatedTime}
            />
            {transcriptionStatus?.duration_processed != null && 
             transcriptionStatus?.duration_total != null && 
             transcriptionStatus.duration_total > 0 && (
              <div className="mt-2 text-sm text-yellow-800 dark:text-yellow-200">
                已處理: {formatDuration(transcriptionStatus.duration_processed)} / {formatDuration(transcriptionStatus.duration_total)}
              </div>
            )}
          </div>
        ) : null}

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
            上傳新的音檔
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
            <div>
              <p className="text-content-primary font-medium">上傳中...</p>
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 mt-2">
                <div 
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadState.progress}%` }}
                />
              </div>
              <p className="text-sm text-content-secondary mt-1">{uploadState.progress}%</p>
            </div>
          </div>
        ) : selectedFile ? (
          <div className="space-y-4">
            <DocumentTextIcon className="h-12 w-12 text-green-500 mx-auto" />
            <div>
              <p className="text-content-primary font-medium">已選擇檔案</p>
              <p className="text-sm text-content-secondary">{selectedFile.name}</p>
              <p className="text-xs text-content-secondary">
                {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB
              </p>
            </div>
            <div className="space-y-2">
              <Button onClick={handleUpload} className="w-full">
                開始處理音檔
              </Button>
              <Button onClick={resetUpload} variant="outline" className="w-full">
                重新選擇
              </Button>
            </div>
          </div>
        ) : (
          <div className="space-y-4">
            <CloudArrowUpIcon className="h-12 w-12 text-content-secondary mx-auto" />
            <div>
              <p className="text-content-primary font-medium">上傳音檔進行轉錄</p>
              <p className="text-sm text-content-secondary">
                拖拽檔案到這裡或點擊選擇檔案
              </p>
              <p className="text-xs text-content-secondary">
                支援 MP3、WAV、FLAC、OGG、MP4、M4A 格式，最大 1GB
              </p>
            </div>
            <Button onClick={() => fileInputRef.current?.click()} className="mx-auto">
              選擇檔案
            </Button>
          </div>
        )}
      </div>

      {/* Settings */}
      {selectedFile && (
        <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
          <div>
            <label className="block text-sm font-medium text-content-primary mb-2">
              語言設定
            </label>
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="w-full px-3 py-2 border border-border rounded-md bg-surface text-content-primary"
            >
              <option value="cmn-Hant-TW">繁體中文 (台灣)</option>
              <option value="cmn-Hans-CN">簡體中文</option>
              <option value="en-US">English (US)</option>
              <option value="ja-JP">日本語</option>
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