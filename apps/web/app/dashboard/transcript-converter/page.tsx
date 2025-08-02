'use client'

import { useState } from 'react'
import { apiClient, downloadBlob } from '../../../lib/api'
import { useI18n } from '../../../contexts/i18n-context'

interface ConversionOptions {
  outputFormat: 'markdown' | 'excel'
  coachName: string
  clientName: string
  convertToTraditional: boolean
}

export default function TranscriptConverterPage() {
  const { t } = useI18n()
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [options, setOptions] = useState<ConversionOptions>({
    outputFormat: 'markdown',
    coachName: 'Coach',
    clientName: 'Client',
    convertToTraditional: false
  })

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0]
    if (selectedFile && selectedFile.name.endsWith('.vtt')) {
      setFile(selectedFile)
    } else {
      alert(t('converter.alert_select_file'))
    }
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    
    if (!file) {
      alert(t('converter.alert_no_file'))
      return
    }

    setIsProcessing(true)
    
    try {
      console.log('Processing file:', file.name, 'with options:', options)
      
      // 調用真實的 API
      const result = await apiClient.uploadTranscript(file, options)
      
      // 自動下載處理結果
      downloadBlob(result.blob, result.filename)
      
      // 處理成功後的邏輯
      alert(t('converter.alert_success'))
      setFile(null)
      
    } catch (error) {
      console.error('Processing error:', error)
      alert(`${t('converter.alert_error')}${error instanceof Error ? error.message : t('converter.alert_unknown_error')}`)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-dashboard-accent">{t('converter.title')}</h1>
        <p className="text-xl text-dashboard-text-secondary mt-3">{t('converter.subtitle')}</p>
      </div>

      <div className="bg-dashboard-card-bg rounded-lg shadow-dark p-8 border border-dashboard-accent border-opacity-10">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 檔案上傳區域 */}
          <div>
            <label className="block text-sm font-medium text-dashboard-text mb-2">
              {t('converter.upload_text')}
            </label>
            <div className="border-2 border-dashed border-dashboard-accent border-opacity-30 rounded-lg p-6 text-center hover:border-dashboard-accent hover:border-opacity-50 transition-colors">
              {file ? (
                <div className="flex items-center justify-center">
                  <svg className="w-8 h-8 text-dashboard-accent mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-dashboard-text">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="ml-2 text-red-400 hover:text-red-300"
                  >
                    {t('converter.remove_file')}
                  </button>
                </div>
              ) : (
                <div>
                  <svg className="w-12 h-12 text-dashboard-text-secondary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
                  </svg>
                  <input
                    type="file"
                    accept=".vtt"
                    onChange={handleFileChange}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <span className="text-dashboard-accent hover:text-dashboard-accent font-medium">{t('converter.upload_subtext')}</span>
                  </label>
                  <p className="text-sm text-dashboard-text-tertiary mt-2">{t('converter.file_info')}</p>
                </div>
              )}
            </div>
          </div>

          {/* 輸出格式選擇 */}
          <div>
            <label className="block text-sm font-medium text-dashboard-text mb-2">
              {t('converter.output_format')}
            </label>
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center p-4 border border-dashboard-accent border-opacity-30 rounded-lg cursor-pointer hover:bg-dashboard-accent hover:bg-opacity-10 transition-colors">
                <input
                  type="radio"
                  name="outputFormat"
                  value="markdown"
                  checked={options.outputFormat === 'markdown'}
                  onChange={(e) => setOptions({...options, outputFormat: e.target.value as 'markdown' | 'excel'})}
                  className="mr-3 text-dashboard-accent"
                />
                <div>
                  <div className="font-medium text-dashboard-text">{t('converter.markdown_title')}</div>
                  <div className="text-sm text-dashboard-text-secondary">{t('converter.markdown_desc')}</div>
                </div>
              </label>
              
              <label className="flex items-center p-4 border border-dashboard-accent border-opacity-30 rounded-lg cursor-pointer hover:bg-dashboard-accent hover:bg-opacity-10 transition-colors">
                <input
                  type="radio"
                  name="outputFormat"
                  value="excel"
                  checked={options.outputFormat === 'excel'}
                  onChange={(e) => setOptions({...options, outputFormat: e.target.value as 'markdown' | 'excel'})}
                  className="mr-3 text-dashboard-accent"
                />
                <div>
                  <div className="font-medium text-dashboard-text">{t('converter.excel_title')}</div>
                  <div className="text-sm text-dashboard-text-secondary">{t('converter.excel_desc')}</div>
                </div>
              </label>
            </div>
          </div>

          {/* 說話者設定 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="coachName" className="block text-sm font-medium text-dashboard-text mb-2">
                {t('converter.coach_name')}
              </label>
              <input
                type="text"
                id="coachName"
                value={options.coachName}
                onChange={(e) => setOptions({...options, coachName: e.target.value})}
                className="w-full px-3 py-2 bg-dashboard-bg border border-dashboard-accent border-opacity-30 rounded-lg focus:ring-2 focus:ring-dashboard-accent focus:border-dashboard-accent text-dashboard-text placeholder-dashboard-text-tertiary"
                placeholder={t('converter.coach_placeholder')}
              />
            </div>
            
            <div>
              <label htmlFor="clientName" className="block text-sm font-medium text-dashboard-text mb-2">
                {t('converter.client_name')}
              </label>
              <input
                type="text"
                id="clientName"
                value={options.clientName}
                onChange={(e) => setOptions({...options, clientName: e.target.value})}
                className="w-full px-3 py-2 bg-dashboard-bg border border-dashboard-accent border-opacity-30 rounded-lg focus:ring-2 focus:ring-dashboard-accent focus:border-dashboard-accent text-dashboard-text placeholder-dashboard-text-tertiary"
                placeholder={t('converter.client_placeholder')}
              />
            </div>
          </div>

          {/* 中文轉換選項 */}
          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={options.convertToTraditional}
                onChange={(e) => setOptions({...options, convertToTraditional: e.target.checked})}
                className="mr-2 text-dashboard-accent focus:ring-dashboard-accent"
              />
              <span className="text-dashboard-text">{t('converter.convert_chinese')}</span>
            </label>
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!file || isProcessing}
              className="px-8 py-3 bg-dashboard-accent text-dashboard-bg rounded-lg hover:bg-dashboard-accent hover:bg-opacity-90 disabled:bg-dashboard-text-secondary disabled:cursor-not-allowed transition-all duration-300 font-medium"
            >
              {isProcessing ? (
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {t('converter.processing')}
                </div>
              ) : (
                t('converter.start_btn')
              )}
            </button>
          </div>
        </form>
      </div>

      {/* 使用說明 */}
      <div className="mt-8 bg-dashboard-card-bg border border-dashboard-accent border-opacity-20 rounded-lg p-6 shadow-dark">
        <h3 className="text-xl font-semibold text-dashboard-accent mb-4">{t('converter.instructions')}</h3>
        <ul className="text-dashboard-text-secondary space-y-3">
          <li className="flex items-start">
            <span className="text-dashboard-accent mr-2">•</span>
            <span>{t('converter.instruction1')}</span>
          </li>
          <li className="flex items-start">
            <span className="text-dashboard-accent mr-2">•</span>
            <span>{t('converter.instruction2')}</span>
          </li>
          <li className="flex items-start">
            <span className="text-dashboard-accent mr-2">•</span>
            <span>{t('converter.instruction3')}</span>
          </li>
          <li className="flex items-start">
            <span className="text-dashboard-accent mr-2">•</span>
            <span>{t('converter.instruction4')}</span>
          </li>
          <li className="flex items-start">
            <span className="text-dashboard-accent mr-2">•</span>
            <span>{t('converter.instruction5')}</span>
          </li>
        </ul>
      </div>
    </div>
  )
}
