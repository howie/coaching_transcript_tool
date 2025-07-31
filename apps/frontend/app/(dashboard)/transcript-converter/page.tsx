'use client'

import { useState } from 'react'
import { apiClient, downloadBlob } from '@/lib/api'

interface ConversionOptions {
  outputFormat: 'markdown' | 'excel'
  coachName: string
  clientName: string
  convertToTraditional: boolean
}

export default function TranscriptConverterPage() {
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
      alert('請選擇 VTT 格式的檔案')
    }
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    
    if (!file) {
      alert('請先選擇檔案')
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
      alert('檔案處理完成並已下載！')
      setFile(null)
      
    } catch (error) {
      console.error('Processing error:', error)
      alert(`處理過程中發生錯誤：${error instanceof Error ? error.message : '未知錯誤'}`)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-black">逐字稿轉換器</h1>
        <p className="text-xl text-gray-800 mt-3">將 VTT 格式的逐字稿轉換為 Markdown 或 Excel 文件</p>
      </div>

      <div className="bg-white rounded-lg shadow-custom p-8">
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* 檔案上傳區域 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              選擇 VTT 檔案
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-gray-400 transition-colors">
              {file ? (
                <div className="flex items-center justify-center">
                  <svg className="w-8 h-8 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-gray-700">{file.name}</span>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    className="ml-2 text-red-600 hover:text-red-800"
                  >
                    移除
                  </button>
                </div>
              ) : (
                <div>
                  <svg className="w-12 h-12 text-gray-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
                    <span className="text-blue-600 hover:text-blue-700 font-medium">點擊選擇檔案</span>
                    <span className="text-gray-600"> 或拖放檔案到此處</span>
                  </label>
                  <p className="text-sm text-gray-500 mt-2">支援 VTT 格式，最大 10MB</p>
                </div>
              )}
            </div>
          </div>

          {/* 輸出格式選擇 */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              輸出格式
            </label>
            <div className="grid grid-cols-2 gap-4">
              <label className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="outputFormat"
                  value="markdown"
                  checked={options.outputFormat === 'markdown'}
                  onChange={(e) => setOptions({...options, outputFormat: e.target.value as 'markdown' | 'excel'})}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">Markdown (.md)</div>
                  <div className="text-sm text-gray-600">適合閱讀和版本控制</div>
                </div>
              </label>
              
              <label className="flex items-center p-4 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="radio"
                  name="outputFormat"
                  value="excel"
                  checked={options.outputFormat === 'excel'}
                  onChange={(e) => setOptions({...options, outputFormat: e.target.value as 'markdown' | 'excel'})}
                  className="mr-3"
                />
                <div>
                  <div className="font-medium">Excel (.xlsx)</div>
                  <div className="text-sm text-gray-600">適合數據分析和處理</div>
                </div>
              </label>
            </div>
          </div>

          {/* 說話者設定 */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="coachName" className="block text-sm font-medium text-gray-700 mb-2">
                教練名稱
              </label>
              <input
                type="text"
                id="coachName"
                value={options.coachName}
                onChange={(e) => setOptions({...options, coachName: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Coach"
              />
            </div>
            
            <div>
              <label htmlFor="clientName" className="block text-sm font-medium text-gray-700 mb-2">
                客戶名稱
              </label>
              <input
                type="text"
                id="clientName"
                value={options.clientName}
                onChange={(e) => setOptions({...options, clientName: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="Client"
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
                className="mr-2"
              />
              <span className="text-gray-700">轉換為繁體中文</span>
            </label>
          </div>

          {/* 提交按鈕 */}
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={!file || isProcessing}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {isProcessing ? (
                <div className="flex items-center">
                  <svg className="w-4 h-4 mr-2 animate-spin" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  處理中...
                </div>
              ) : (
                '開始轉換'
              )}
            </button>
          </div>
        </form>
      </div>

      {/* 使用說明 */}
      <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">使用說明</h3>
        <ul className="text-blue-800 space-y-2">
          <li>• 支援標準 WebVTT (.vtt) 格式檔案</li>
          <li>• 系統會自動識別說話者並進行內容整理</li>
          <li>• 可設定教練和客戶的顯示名稱以保護隱私</li>
          <li>• 支援簡體轉繁體中文功能</li>
          <li>• 處理完成後會自動下載結果檔案</li>
        </ul>
      </div>
    </div>
  )
}
