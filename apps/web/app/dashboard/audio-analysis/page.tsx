'use client'

import { useState, useRef, useEffect } from 'react'
import { useI18n } from '@/contexts/i18n-context'
import { apiClient, downloadBlob } from '@/lib/api'
import { SpeakerWaveIcon, CloudArrowUpIcon, DocumentTextIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface UploadState {
  status: 'idle' | 'uploading' | 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  estimatedTime?: string
  error?: string
  sessionId?: string
  fileName?: string
  taskId?: string
  transcriptData?: any
}

export default function AudioAnalysisPage() {
  const { t } = useI18n()
  const [uploadState, setUploadState] = useState<UploadState>({ status: 'idle', progress: 0 })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [sessionTitle, setSessionTitle] = useState('')
  const [language, setLanguage] = useState('auto')
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const supportedFormats = ['mp3', 'wav', 'm4a', 'ogg', 'mp4']
  const maxFileSize = 1 * 1024 * 1024 * 1024 // 1GB
  const maxDuration = 120 // 120 minutes

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

  const handleFileSelect = (file: File) => {
    // Validate file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase()
    if (!fileExtension || !supportedFormats.includes(fileExtension)) {
      setUploadState({
        status: 'failed',
        progress: 0,
        error: t('audio.invalid_format')
      })
      return
    }

    // Validate file size
    if (file.size > maxFileSize) {
      setUploadState({
        status: 'failed',
        progress: 0,
        error: t('audio.file_too_large')
      })
      return
    }

    setSelectedFile(file)
    setUploadState({ status: 'idle', progress: 0 })
  }

  const handleFileInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0])
    }
  }

  const handleUpload = async () => {
    if (!selectedFile) return

    setUploadState({ status: 'uploading', progress: 0 })

    try {
      // Step 1: Create transcription session
      const session = await apiClient.createTranscriptionSession({
        title: sessionTitle.trim(),
        language: language === 'auto' ? 'zh-TW' : language
      })

      setUploadState(prev => ({ 
        ...prev, 
        sessionId: session.id,
        progress: 10
      }))

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
          progress: 20 + (progress * 0.6) // 20% to 80% for upload progress
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

      // Step 5: Start transcription processing
      const transcriptionResult = await apiClient.startTranscription(session.id)
      
      setUploadState(prev => ({ 
        ...prev, 
        status: 'processing',
        progress: 0,
        estimatedTime: '約 15-30 分鐘',
        taskId: transcriptionResult.task_id
      }))

      // Step 6: Start polling for transcription status
      startPollingTranscriptionStatus(session.id)
      
    } catch (error: any) {
      console.error('Upload error:', error)
      setUploadState(prev => ({
        ...prev,
        status: 'failed',
        progress: 0,
        error: error.message || t('audio.upload_error')
      }))
    }
  }

  // Polling for transcription status
  const startPollingTranscriptionStatus = async (sessionId: string) => {
    const pollInterval = 5000 // Poll every 5 seconds
    const maxPollingTime = 2 * 60 * 60 * 1000 // 2 hours maximum
    const startTime = Date.now()

    const poll = async () => {
      try {
        if (Date.now() - startTime > maxPollingTime) {
          setUploadState(prev => ({
            ...prev,
            status: 'failed',
            error: 'Transcription timed out. Please try again.'
          }))
          return
        }

        const session = await apiClient.getTranscriptionSession(sessionId)
        
        if (session.status === 'completed') {
          setUploadState(prev => ({
            ...prev,
            status: 'completed',
            progress: 100,
            transcriptData: session
          }))
        } else if (session.status === 'failed') {
          setUploadState(prev => ({
            ...prev,
            status: 'failed',
            error: session.error_message || 'Transcription failed'
          }))
        } else if (session.status === 'processing') {
          // Continue polling
          setTimeout(poll, pollInterval)
          
          // Update estimated time based on duration if available
          if (session.duration_minutes) {
            const estimatedMinutes = Math.ceil(session.duration_minutes * 2) // Estimate 2x duration
            setUploadState(prev => ({
              ...prev,
              estimatedTime: `約 ${estimatedMinutes} 分鐘`
            }))
          }
        } else {
          // Still processing, continue polling
          setTimeout(poll, pollInterval)
        }
      } catch (error: any) {
        console.error('Polling error:', error)
        // Continue polling unless it's a serious error
        if (error.message?.includes('404') || error.message?.includes('unauthorized')) {
          setUploadState(prev => ({
            ...prev,
            status: 'failed',
            error: 'Session not found or access denied'
          }))
        } else {
          setTimeout(poll, pollInterval * 2) // Retry with longer interval
        }
      }
    }

    // Start polling
    poll()
  }

  const resetUpload = () => {
    setSelectedFile(null)
    setUploadState({ status: 'idle', progress: 0 })
    setSessionTitle('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  // Handle transcript download
  const handleDownloadTranscript = async (format: 'json' | 'vtt' | 'srt' | 'txt' = 'json') => {
    if (!uploadState.sessionId) return

    try {
      const blob = await apiClient.exportTranscript(uploadState.sessionId, format)
      const filename = `${sessionTitle.trim() || 'transcript'}.${format}`
      downloadBlob(blob, filename)
    } catch (error: any) {
      console.error('Download error:', error)
      setUploadState(prev => ({
        ...prev,
        error: `Download failed: ${error.message}`
      }))
    }
  }

  const getStatusIcon = () => {
    switch (uploadState.status) {
      case 'uploading':
      case 'processing':
        return (
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        )
      case 'completed':
        return (
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
        )
      case 'failed':
        return (
          <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center">
            <ExclamationTriangleIcon className="w-5 h-5 text-red-600" />
          </div>
        )
      default:
        return null
    }
  }

  const getStatusText = () => {
    switch (uploadState.status) {
      case 'uploading':
        return t('audio.status_uploading')
      case 'pending':
        return t('audio.status_pending')
      case 'processing':
        return t('audio.status_processing')
      case 'completed':
        return t('audio.status_completed')
      case 'failed':
        return t('audio.status_failed')
      default:
        return ''
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-3">
        <SpeakerWaveIcon className="h-8 w-8 text-blue-600" />
        <div className="flex-1">
          <div className="flex items-center space-x-3">
            <h1 className="text-2xl font-bold text-gray-900">{t('audio.title')}</h1>
            <span className="bg-orange-100 text-orange-800 text-xs font-medium px-2.5 py-0.5 rounded-full">
              {t('menu.experimental')}
            </span>
          </div>
          <p className="text-gray-600 mt-1">{t('audio.subtitle')}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Upload Area */}
        <div className="lg:col-span-2 space-y-6">
          {/* File Upload Section */}
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('audio.upload_text')}</h2>
            
            {/* Auto-delete Warning */}
            <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
              <div className="flex">
                <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />
                <div className="ml-3">
                  <p className="text-sm text-yellow-700">{t('audio.auto_delete_warning')}</p>
                </div>
              </div>
            </div>

            {!selectedFile ? (
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  dragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <CloudArrowUpIcon className="mx-auto h-12 w-12 text-gray-400" />
                <p className="mt-2 text-lg font-medium text-gray-900">{t('audio.upload_subtext')}</p>
                <p className="mt-1 text-sm text-gray-500">{t('audio.file_info')}</p>
                
                <input
                  ref={fileInputRef}
                  type="file"
                  className="hidden"
                  accept=".mp3,.wav,.m4a,.ogg,.mp4"
                  onChange={handleFileInputChange}
                />
              </div>
            ) : (
              <div className="space-y-4">
                {/* Selected File Info */}
                <div className="bg-gray-50 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <SpeakerWaveIcon className="h-8 w-8 text-blue-600" />
                      <div>
                        <p className="font-medium text-gray-900">{selectedFile.name}</p>
                        <p className="text-sm text-gray-500">
                          {(selectedFile.size / (1024 * 1024)).toFixed(1)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={resetUpload}
                      className="text-red-600 hover:text-red-800 text-sm font-medium"
                      disabled={uploadState.status === 'uploading' || uploadState.status === 'processing'}
                    >
                      移除
                    </button>
                  </div>
                </div>

                {/* Session Information */}
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('audio.session_title')}
                    </label>
                    <input
                      type="text"
                      value={sessionTitle}
                      onChange={(e) => setSessionTitle(e.target.value)}
                      placeholder={t('audio.session_title_placeholder')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={uploadState.status === 'uploading' || uploadState.status === 'processing'}
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      {t('audio.language_selection')}
                    </label>
                    <select
                      value={language}
                      onChange={(e) => setLanguage(e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                      disabled={uploadState.status === 'uploading' || uploadState.status === 'processing'}
                    >
                      <option value="auto">{t('audio.language_auto')}</option>
                      <option value="zh-TW">{t('audio.language_zh_tw')}</option>
                      <option value="zh-CN">{t('audio.language_zh_cn')}</option>
                      <option value="en-US">{t('audio.language_en')}</option>
                    </select>
                  </div>
                </div>

                {/* Upload Progress */}
                {(uploadState.status === 'uploading' || uploadState.status === 'processing') && (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon()}
                        <span className="text-sm font-medium text-gray-900">{getStatusText()}</span>
                      </div>
                      {uploadState.estimatedTime && (
                        <span className="text-sm text-gray-500">
                          {t('audio.estimated_time')}: {uploadState.estimatedTime}
                        </span>
                      )}
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                        style={{ width: `${uploadState.progress}%` }}
                      ></div>
                    </div>
                  </div>
                )}

                {/* Status Messages */}
                {uploadState.status === 'failed' && uploadState.error && (
                  <div className="bg-red-50 border border-red-200 rounded-md p-3">
                    <div className="flex">
                      <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                      <div className="ml-3">
                        <p className="text-sm text-red-800">{uploadState.error}</p>
                      </div>
                    </div>
                  </div>
                )}

                {uploadState.status === 'completed' && (
                  <div className="bg-green-50 border border-green-200 rounded-md p-4">
                    <div className="flex flex-col space-y-3">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon()}
                        <span className="text-sm font-medium text-green-800">{t('audio.status_completed')}</span>
                        {uploadState.transcriptData?.segments_count && (
                          <span className="text-sm text-green-700">
                            ({uploadState.transcriptData.segments_count} 段對話)
                          </span>
                        )}
                      </div>
                      <div className="flex flex-wrap gap-2">
                        <button 
                          onClick={() => handleDownloadTranscript('json')}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-md text-sm font-medium"
                        >
                          下載 JSON
                        </button>
                        <button 
                          onClick={() => handleDownloadTranscript('txt')}
                          className="bg-green-600 hover:bg-green-700 text-white px-3 py-1.5 rounded-md text-sm font-medium"
                        >
                          下載文本
                        </button>
                        <button 
                          onClick={() => handleDownloadTranscript('vtt')}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md text-sm font-medium"
                        >
                          下載 VTT
                        </button>
                        <button 
                          onClick={() => handleDownloadTranscript('srt')}
                          className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1.5 rounded-md text-sm font-medium"
                        >
                          下載 SRT
                        </button>
                      </div>
                      {uploadState.transcriptData?.stt_cost_usd && (
                        <div className="text-sm text-gray-600">
                          轉錄費用: ${uploadState.transcriptData.stt_cost_usd} USD
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Action Buttons */}
                {uploadState.status === 'idle' && (
                  <button
                    onClick={handleUpload}
                    disabled={!sessionTitle.trim()}
                    className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white font-medium py-3 px-4 rounded-md transition-colors"
                  >
                    {t('audio.upload_btn')}
                  </button>
                )}

                {uploadState.status === 'failed' && (
                  <div className="flex space-x-3">
                    <button
                      onClick={handleUpload}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md"
                    >
                      {t('audio.retry')}
                    </button>
                    <button
                      onClick={resetUpload}
                      className="flex-1 bg-gray-600 hover:bg-gray-700 text-white font-medium py-2 px-4 rounded-md"
                    >
                      {t('audio.new_upload')}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Instructions Sidebar */}
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('audio.instructions')}</h3>
            <ul className="space-y-3 text-sm text-gray-600">
              <li className="flex items-start space-x-2">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2"></span>
                <span>{t('audio.instruction1')}</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2"></span>
                <span>{t('audio.instruction2')}</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2"></span>
                <span>{t('audio.instruction3')}</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2"></span>
                <span>{t('audio.instruction4')}</span>
              </li>
              <li className="flex items-start space-x-2">
                <span className="flex-shrink-0 w-1.5 h-1.5 bg-blue-600 rounded-full mt-2"></span>
                <span>{t('audio.instruction5')}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}