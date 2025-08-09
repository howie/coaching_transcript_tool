'use client'

import { useState, useRef } from 'react'
import { useI18n } from '@/contexts/i18n-context'
import { SpeakerWaveIcon, CloudArrowUpIcon, DocumentTextIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline'

interface UploadState {
  status: 'idle' | 'uploading' | 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  estimatedTime?: string
  error?: string
  sessionId?: string
  fileName?: string
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
      // This is a placeholder for the actual upload implementation
      // In the real implementation, you would:
      // 1. Get signed URL from API
      // 2. Upload file to GCS
      // 3. Trigger transcription processing
      // 4. Poll for status updates

      // Simulate upload progress
      for (let i = 0; i <= 100; i += 10) {
        setUploadState({ status: 'uploading', progress: i })
        await new Promise(resolve => setTimeout(resolve, 200))
      }

      // Simulate processing state
      setUploadState({ 
        status: 'processing', 
        progress: 0,
        estimatedTime: '約 15 分鐘',
        sessionId: 'session-123'
      })

      // Note: In real implementation, you would start polling for status here
      
    } catch (error) {
      setUploadState({
        status: 'failed',
        progress: 0,
        error: t('audio.upload_error')
      })
    }
  }

  const resetUpload = () => {
    setSelectedFile(null)
    setUploadState({ status: 'idle', progress: 0 })
    setSessionTitle('')
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
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
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon()}
                        <span className="text-sm font-medium text-green-800">{t('audio.status_completed')}</span>
                      </div>
                      <div className="space-x-2">
                        <button className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                          {t('audio.download_transcript')}
                        </button>
                        <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md text-sm font-medium">
                          {t('audio.view_analysis')}
                        </button>
                      </div>
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