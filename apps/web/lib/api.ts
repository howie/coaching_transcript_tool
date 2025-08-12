import { debugLog, debugWarn } from '@/lib/debug'

interface TranscriptOptions {
  outputFormat: 'markdown' | 'excel'
  coachName: string
  clientName: string
  convertToTraditional: boolean
}

export class TranscriptNotAvailableError extends Error {
  constructor(message: string) {
    super(message)
    this.name = 'TranscriptNotAvailableError'
  }
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
      // IMPORTANT: We need to bind fetch to the correct context for Safari compatibility
      if (typeof window !== 'undefined' && window.fetch) {
        // In browser environment, bind fetch to window
        this.fetcher = window.fetch.bind(window)
      } else if (typeof globalThis !== 'undefined' && globalThis.fetch) {
        // In other environments, bind to globalThis
        this.fetcher = globalThis.fetch.bind(globalThis)
      } else {
        // Last resort fallback
        this.fetcher = fetch
      }
      this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    }
  }

  private async getHeaders() {
    let token: string | null = null
    
    // Safe localStorage access with error handling
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        token = localStorage.getItem('token')
      }
    } catch (error) {
      debugWarn('Failed to access localStorage:', error)
    }
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    }
    
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
      debugLog('API request with token present')
    } else {
      debugLog('API request without token')
    }
    
    return headers
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

  async signup(name: string, email: string, password: string, recaptchaToken?: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/auth/signup`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify({ name, email, password, recaptcha_token: recaptchaToken }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Signup failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Signup error:', error)
      throw error
    }
  }

  async login(email: string, password: string) {
    try {
      const formData = new URLSearchParams()
      formData.append('username', email)
      formData.append('password', password)

      const response = await this.fetcher(`${this.baseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: formData.toString(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Login failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  async updateProfile(data: { name?: string }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/user/profile`, {
        method: 'PUT',
        headers: await this.getHeaders(),
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update profile failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update profile error:', error)
      throw error
    }
  }

  async updateUserPreferences(preferences: { language?: 'zh' | 'en' | 'system' }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/user/preferences`, {
        method: 'PUT',
        headers: await this.getHeaders(),
        body: JSON.stringify(preferences),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update preferences failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update preferences error:', error)
      throw error
    }
  }
  

  async setPassword(newPassword: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/user/set-password`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify({ new_password: newPassword }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Set password failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Set password error:', error)
      throw error
    }
  }

  async changePassword(currentPassword: string, newPassword: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/user/change-password`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify({ 
          current_password: currentPassword,
          new_password: newPassword 
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Change password failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Change password error:', error)
      throw error
    }
  }

  async deleteAccount() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/user/account`, {
        method: 'DELETE',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Delete account failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Delete account error:', error)
      throw error
    }
  }

  // Client management methods
  async getClients(page = 1, pageSize = 20, query?: string) {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      
      if (query) {
        params.append('query', query)
      }

      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients?${params}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get clients failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get clients error:', error)
      throw error
    }
  }

  async getClient(clientId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/${clientId}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get client failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get client error:', error)
      throw error
    }
  }

  async createClient(clientData: {
    name: string
    email?: string
    phone?: string
    memo?: string
    source?: string
    client_type?: string
    issue_types?: string
    client_status?: string
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(clientData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Create client failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Create client error:', error)
      throw error
    }
  }

  async updateClient(clientId: string, clientData: {
    name?: string
    email?: string
    phone?: string
    memo?: string
    source?: string
    client_type?: string
    issue_types?: string
    client_status?: string
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/${clientId}`, {
        method: 'PATCH',
        headers: await this.getHeaders(),
        body: JSON.stringify(clientData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update client failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update client error:', error)
      throw error
    }
  }

  async deleteClient(clientId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/${clientId}`, {
        method: 'DELETE',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Delete client failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Delete client error:', error)
      throw error
    }
  }

  async anonymizeClient(clientId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/${clientId}/anonymize`, {
        method: 'POST',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Anonymize client failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Anonymize client error:', error)
      throw error
    }
  }

  async getClientSources() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/options/sources`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get client sources failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get client sources error:', error)
      throw error
    }
  }

  async getClientTypes() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/options/types`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get client types failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get client types error:', error)
      throw error
    }
  }

  async getClientStatuses() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/options/statuses`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get client statuses failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get client statuses error:', error)
      throw error
    }
  }

  async getClientStatistics() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/clients/statistics`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get client statistics failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get client statistics error:', error)
      throw error
    }
  }

  // Coaching Sessions methods
  async getSessions(page = 1, pageSize = 20, filters?: {
    from_date?: string
    to_date?: string
    client_id?: string
    currency?: string
    sort?: string
  }) {
    try {
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: pageSize.toString(),
      })
      
      if (filters) {
        Object.entries(filters).forEach(([key, value]) => {
          if (value) {
            // Map front-end parameter names to API parameter names
            const paramName = key === 'from_date' ? 'from' : key === 'to_date' ? 'to' : key
            params.append(paramName, value)
          }
        })
      }

      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions?${params}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const error = new Error(`Get sessions failed: ${response.statusText}`) as any;
        error.status = response.status;
        error.statusText = response.statusText;
        throw error;
      }

      return await response.json()
    } catch (error) {
      console.error('Get sessions error:', error)
      throw error
    }
  }

  async getSession(sessionId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions/${sessionId}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const error = new Error(`Get session failed: ${response.statusText}`) as any;
        error.status = response.status;
        error.statusText = response.statusText;
        throw error;
      }

      return await response.json()
    } catch (error) {
      console.error('Get session error:', error)
      throw error
    }
  }

  async createSession(sessionData: {
    session_date: string
    client_id: string
    duration_min: number
    fee_currency: string
    fee_amount: number
    notes?: string
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(sessionData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Create session failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Create session error:', error)
      throw error
    }
  }

  async updateSession(sessionId: string, sessionData: {
    session_date?: string
    client_id?: string
    duration_min?: number
    fee_currency?: string
    fee_amount?: number
    notes?: string
    audio_timeseq_id?: string  // TECHNICAL DEBT: Confusing name - actually stores session.id (transcription session ID)
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions/${sessionId}`, {
        method: 'PATCH',
        headers: await this.getHeaders(),
        body: JSON.stringify(sessionData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update session failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update session error:', error)
      throw error
    }
  }

  async deleteSession(sessionId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions/${sessionId}`, {
        method: 'DELETE',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Delete session failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Delete session error:', error)
      throw error
    }
  }

  async getCurrencies() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions/options/currencies`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get currencies failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get currencies error:', error)
      throw error
    }
  }

  // Coach profile methods
  async getCoachProfile() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/coach-profile/`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        if (response.status === 404) {
          return null // No profile exists yet
        }
        throw new Error(`Get coach profile failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get coach profile error:', error)
      throw error
    }
  }

  async createCoachProfile(profileData: {
    display_name: string
    profile_photo_url?: string
    public_email?: string
    phone_country_code?: string
    phone_number?: string
    country?: string
    city?: string
    timezone?: string
    coaching_languages?: string[]
    communication_tools?: any
    line_id?: string
    coach_experience?: string
    training_institution?: string
    certifications?: string[]
    linkedin_url?: string
    personal_website?: string
    bio?: string
    specialties?: string[]
    is_public?: boolean
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/coach-profile/`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(profileData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Create coach profile failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Create coach profile error:', error)
      throw error
    }
  }

  async updateCoachProfile(profileData: {
    display_name?: string
    profile_photo_url?: string
    public_email?: string
    phone_country_code?: string
    phone_number?: string
    country?: string
    city?: string
    timezone?: string
    coaching_languages?: string[]
    communication_tools?: any
    line_id?: string
    coach_experience?: string
    training_institution?: string
    certifications?: string[]
    linkedin_url?: string
    personal_website?: string
    bio?: string
    specialties?: string[]
    is_public?: boolean
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/coach-profile/`, {
        method: 'PUT',
        headers: await this.getHeaders(),
        body: JSON.stringify(profileData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update coach profile failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update coach profile error:', error)
      throw error
    }
  }

  async getCoachingPlans() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/coach-profile/plans`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        // Return empty array for 404 - endpoint not yet deployed
        if (response.status === 404) {
          console.log('Coaching plans endpoint not available, returning empty array')
          return []
        }
        throw new Error(`Get coaching plans failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get coaching plans error:', error)
      // Return empty array instead of throwing for network errors
      return []
    }
  }

  async createCoachingPlan(planData: {
    plan_type: string
    title: string
    description?: string
    duration_minutes?: number
    number_of_sessions: number
    price: number
    currency?: string
    is_active?: boolean
    max_participants?: number
    booking_notice_hours?: number
    cancellation_notice_hours?: number
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/coach-profile/plans`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(planData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Create coaching plan failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Create coaching plan error:', error)
      throw error
    }
  }

  async updateCoachingPlan(planId: string, planData: {
    plan_type?: string
    title?: string
    description?: string
    duration_minutes?: number
    number_of_sessions?: number
    price?: number
    currency?: string
    is_active?: boolean
    max_participants?: number
    booking_notice_hours?: number
    cancellation_notice_hours?: number
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/coach-profile/plans/${planId}`, {
        method: 'PUT',
        headers: await this.getHeaders(),
        body: JSON.stringify(planData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update coaching plan failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update coaching plan error:', error)
      throw error
    }
  }

  async deleteCoachingPlan(planId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/coach-profile/plans/${planId}`, {
        method: 'DELETE',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Delete coaching plan failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Delete coaching plan error:', error)
      throw error
    }
  }

  // Dashboard summary methods
  async getSummary(month?: string) {
    try {
      const params = new URLSearchParams()
      if (month) {
        params.append('month', month)
      }

      const url = `${this.baseUrl}/api/v1/dashboard/summary${params.toString() ? `?${params}` : ''}`
      const response = await this.fetcher(url, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get summary failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get summary error:', error)
      throw error
    }
  }

  // Audio transcription session methods
  async createTranscriptionSession(sessionData: {
    title: string
    language?: string
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(sessionData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Create transcription session failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Create transcription session error:', error)
      throw error
    }
  }

  async getUploadUrl(sessionId: string, filename: string) {
    try {
      const params = new URLSearchParams({ filename })
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/upload-url?${params}`, {
        method: 'POST',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        let errorMessage = 'Get upload URL failed'
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || errorMessage
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      return await response.json()
    } catch (error) {
      console.error('Get upload URL error:', error)
      throw error
    }
  }

  async uploadToGCS(uploadUrl: string, file: File, onProgress?: (progress: number) => void) {
    try {
      return new Promise<void>((resolve, reject) => {
        const xhr = new XMLHttpRequest()
        
        if (onProgress) {
          xhr.upload.addEventListener('progress', (event) => {
            if (event.lengthComputable) {
              const progress = (event.loaded / event.total) * 100
              onProgress(progress)
            }
          })
        }

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            resolve()
          } else {
            reject(new Error(`Upload failed: ${xhr.status} ${xhr.statusText}`))
          }
        })

        xhr.addEventListener('error', () => {
          reject(new Error('Upload failed: Network error'))
        })

        xhr.addEventListener('abort', () => {
          reject(new Error('Upload cancelled'))
        })

        // Map file extensions to proper MIME types (must match backend)
        const getContentType = (file: File): string => {
          const extension = file.name.split('.').pop()?.toLowerCase()
          const contentTypeMap: Record<string, string> = {
            'mp3': 'audio/mpeg',
            'wav': 'audio/wav',
            'flac': 'audio/flac',
            'ogg': 'audio/ogg',
            'mp4': 'audio/mp4'
          }
          return contentTypeMap[extension || ''] || file.type || 'audio/mpeg'
        }

        const contentType = getContentType(file)
        
        xhr.open('PUT', uploadUrl)
        xhr.setRequestHeader('Content-Type', contentType)
        xhr.send(file)
      })
    } catch (error) {
      console.error('GCS upload error:', error)
      throw error
    }
  }

  async confirmUpload(sessionId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/confirm-upload`, {
        method: 'POST',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Confirm upload failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Confirm upload error:', error)
      throw error
    }
  }

  async startTranscription(sessionId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/start-transcription`, {
        method: 'POST',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Start transcription failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Start transcription error:', error)
      throw error
    }
  }

  async getTranscriptionSession(sessionId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Get transcription session failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Get transcription session error:', error)
      throw error
    }
  }

  async listTranscriptionSessions(status?: string, limit = 50, offset = 0) {
    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      })
      
      if (status) {
        params.append('status', status)
      }

      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions?${params}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'List transcription sessions failed')
      }

      return await response.json()
    } catch (error) {
      console.error('List transcription sessions error:', error)
      throw error
    }
  }

  async exportTranscript(sessionId: string, format: 'json' | 'vtt' | 'srt' | 'txt' = 'json') {
    try {
      const params = new URLSearchParams({ format })
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/transcript?${params}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        
        // Handle specific error cases
        if (response.status === 404 && errorData.detail === 'No transcript segments found') {
          // This is a normal case when transcription hasn't completed or failed
          throw new TranscriptNotAvailableError(errorData.detail)
        }
        
        throw new Error(errorData.detail || 'Export transcript failed')
      }

      return response.blob()
    } catch (error) {
      // Only log as error if it's not the expected TranscriptNotAvailableError
      if (!(error instanceof TranscriptNotAvailableError)) {
        console.error('Export transcript error:', error)
      }
      throw error
    }
  }

  async getTranscriptionStatus(sessionId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/status`, {
        headers: await this.getHeaders(),
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Get transcription status failed')
      }
      return await response.json()
    } catch (error) {
      console.error('Get transcription status error:', error)
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
