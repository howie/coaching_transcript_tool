interface TranscriptOptions {
  outputFormat: 'markdown' | 'excel'
  coachName: string
  clientName: string
  convertToTraditional: boolean
}

// Augment the global scope to include the Cloudflare service binding
declare global {
  var API_SERVICE: { fetch: typeof fetch } | undefined;
}

class ApiClient {
  private baseUrl: string
  private fetcher: typeof fetch

  constructor() {
    // In a Cloudflare Worker environment, a service binding `API_SERVICE` will be available.
    // We use a robust check to see if it's a valid binding with a fetch method.
    if (typeof globalThis !== 'undefined' && 
        globalThis.API_SERVICE && 
        typeof globalThis.API_SERVICE.fetch === 'function') {
      this.fetcher = globalThis.API_SERVICE.fetch.bind(globalThis.API_SERVICE)
      this.baseUrl = '' // Base URL is handled by the binding
    } else {
      // Fallback for local development or other environments
      this.fetcher = globalThis.fetch || fetch
      this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    }
  }

  private async getHeaders() {
    return {
      'Content-Type': 'application/json',
    }
  }

  async healthCheck() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/health`)
      
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Health check error:', error)
      throw error
    }
  }

  async uploadTranscript(file: File, options: TranscriptOptions) {
    try {
      const formData = new FormData()
      formData.append('file', file)
      
      // 將選項作為 FormData 參數傳遞（與 curl 測試一致）
      formData.append('output_format', options.outputFormat)
      formData.append('coach_name', options.coachName)
      formData.append('client_name', options.clientName)
      formData.append('convert_to_traditional_chinese', options.convertToTraditional.toString())

      const response = await this.fetcher(`${this.baseUrl}/api/v1/format`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`API Error: ${response.status} ${response.statusText} - ${errorText}`)
      }

      // 檢查回應類型
      const contentType = response.headers.get('content-type')
      
      if (contentType?.includes('application/json')) {
        // 如果是 JSON 回應，可能是錯誤訊息
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Unknown error')
      }

      // 回傳檔案 blob
      return {
        blob: await response.blob(),
        filename: this.getFilenameFromResponse(response, file.name, options.outputFormat)
      }
    } catch (error) {
      console.error('Upload error:', error)
      throw error
    }
  }

  private getFilenameFromResponse(response: Response, originalName: string, format: string): string {
    // 嘗試從 Content-Disposition header 取得檔名
    const contentDisposition = response.headers.get('content-disposition')
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
      if (filenameMatch) {
        return filenameMatch[1].replace(/['"]/g, '')
      }
    }

    // 如果沒有，則生成檔名
    const baseName = originalName.replace(/\.[^/.]+$/, '')
    const extension = format === 'excel' ? 'xlsx' : 'md'
    return `${baseName}.${extension}`
  }

  async getUserProfile() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/user/profile`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get profile failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get profile error:', error)
      throw error
    }
  }
}

export const apiClient = new ApiClient()

// 下載辅助函式
export function downloadBlob(blob: Blob, filename: string) {
  // Check if we're in a browser environment
  if (typeof window !== 'undefined' && typeof document !== 'undefined') {
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } else {
    // In Worker environment, this function shouldn't be called
    // but we provide a fallback to avoid errors
    console.warn('downloadBlob called in non-browser environment')
  }
}
