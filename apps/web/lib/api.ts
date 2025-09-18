import { debugLog, debugWarn } from '@/lib/debug'

interface TranscriptOptions {
  outputFormat: 'markdown' | 'excel'
  coachName: string
  clientName: string
  convertToTraditional: boolean
}

// Transcript smoothing types
interface ProcessedSegment {
  speaker: string
  start_ms: number
  end_ms: number
  text: string
  source_utterance_indices: number[]
  note?: string
}

interface HeuristicStats {
  short_first_segment: number
  filler_words: number
  no_terminal_punct: number
  echo_backfill: number
}

interface ProcessingStats {
  moved_word_count: number
  merged_segments: number
  split_segments: number
  heuristic_hits: HeuristicStats
  language_detected: string
  processor_used: string
  processing_time_ms: number
}

interface SmoothingResponse {
  segments: ProcessedSegment[]
  stats: ProcessingStats
  success: boolean
}

// LeMUR-based smoothing types
interface LeMURSegment {
  speaker: string
  start_ms: number
  end_ms: number
  text: string
}

interface LeMURSmoothingResponse {
  segments: LeMURSegment[]
  speaker_mapping: { [key: string]: string }
  improvements_made: string[]
  processing_notes: string
  processing_time_ms: number
  success: boolean
}

export type { TranscriptOptions, ProcessedSegment, ProcessingStats, SmoothingResponse, LeMURSegment, LeMURSmoothingResponse }

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

/**
 * Parse error response and extract human-readable message with i18n support
 */
function parseErrorMessage(
  errorData: any, 
  defaultMessage: string, 
  t?: (key: string, params?: Record<string, any>) => string
): string {
  // Handle structured error responses from backend
  if (errorData.detail && typeof errorData.detail === 'object') {
    const baseMessage = errorData.detail.message || errorData.detail.error || defaultMessage
    
    // Add helpful context for plan limit errors with i18n
    if (t && (errorData.detail.error === 'session_limit_exceeded' || 
              errorData.detail.error === 'transcription_limit_exceeded' ||
              errorData.detail.error === 'file_size_exceeded')) {
      
      // Get localized plan name
      const planKey = errorData.detail.plan === 'free' ? 'errors.planFree' :
                     errorData.detail.plan === 'pro' ? 'errors.planPro' :
                     errorData.detail.plan === 'business' ? 'errors.planBusiness' :
                     errorData.detail.plan?.toUpperCase()
      
      const planName = planKey?.startsWith('errors.') ? t(planKey) : planKey
      
      // Use appropriate i18n message based on error type
      if (errorData.detail.error === 'session_limit_exceeded') {
        return t('errors.sessionLimitExceededWithPlan', {
          limit: errorData.detail.limit || errorData.detail.current_usage,
          plan: planName
        })
      } else if (errorData.detail.error === 'transcription_limit_exceeded') {
        return t('errors.transcriptionLimitExceededWithPlan', {
          limit: errorData.detail.limit || errorData.detail.current_usage,
          plan: planName
        })
      } else if (errorData.detail.error === 'file_size_exceeded') {
        return t('errors.fileSizeExceededWithPlan', {
          fileSize: errorData.detail.file_size_mb,
          limit: errorData.detail.limit_mb,
          plan: planName
        })
      }
    }
    
    // Fallback to original logic if no i18n function or unhandled error
    if (errorData.detail.error === 'session_limit_exceeded' || 
        errorData.detail.error === 'transcription_limit_exceeded' ||
        errorData.detail.error === 'file_size_exceeded') {
      const planType = errorData.detail.plan === 'free' ? 'FREE' : errorData.detail.plan?.toUpperCase()
      return `${baseMessage}${planType ? ` (${planType} plan)` : ''}. Consider upgrading your plan for higher limits.`
    }
    
    return baseMessage
  } else if (errorData.detail && typeof errorData.detail === 'string') {
    return errorData.detail
  } else if (errorData.message) {
    return errorData.message
  }
  return defaultMessage
}

class ApiClient {
  private _baseUrl: string | null = null
  private fetcher: typeof fetch
  private translateFn?: (key: string, params?: Record<string, any>) => string

  setTranslationFunction(t: (key: string, params?: Record<string, any>) => string) {
    this.translateFn = t
  }

  // Lazy initialization of baseUrl to ensure proper runtime context
  public getBaseUrl(): string {
    if (this._baseUrl === null) {
      // CRITICAL: Force HTTPS for production domains BEFORE checking env vars
      if (typeof window !== 'undefined') {
        const isSecureContext = window.location.protocol === 'https:'
        const isProductionDomain = window.location.hostname.includes('doxa.com.tw')
        
        if (isSecureContext || isProductionDomain) {
          this._baseUrl = 'https://api.doxa.com.tw'
          console.warn('🔒 FORCED HTTPS for production:', this._baseUrl)
          debugLog('Production domain detected - forcing HTTPS API URL')
          return this._baseUrl
        }
      }
      
      // Only use env var for non-production environments
      const envUrl = process.env.NEXT_PUBLIC_API_URL
      this._baseUrl = envUrl || 'http://localhost:8000'
      console.log('📡 Using environment API URL:', this._baseUrl)
    }
    
    // ADDITIONAL SAFETY: Always ensure HTTPS for doxa.com.tw domains
    if (typeof window !== 'undefined' && 
        window.location.protocol === 'https:' && 
        this._baseUrl && 
        this._baseUrl.includes('doxa.com.tw') && 
        !this._baseUrl.startsWith('https://')) {
      console.warn('🚨 SAFETY OVERRIDE: Clearing HTTP baseUrl cache and forcing HTTPS')
      // Clear bad cache and force HTTPS
      this._baseUrl = 'https://api.doxa.com.tw'
    }
    
    return this._baseUrl
  }

  // Legacy getter for backward compatibility
  get baseUrl(): string {
    return this.getBaseUrl()
  }

  private handleUnauthorized() {
    // Clear the stored token
    if (typeof window !== 'undefined') {
      localStorage.removeItem('token')
      // Redirect to login page
      window.location.href = '/login'
    }
  }

  private async handleResponse(response: Response) {
    if (response.status === 401) {
      this.handleUnauthorized()
      throw new Error('Unauthorized - please login again')
    }
    return response
  }

  constructor() {
    // Set up fetcher - simplified since baseUrl is now handled lazily
    if (typeof globalThis !== 'undefined' && 
        globalThis.API_SERVICE && 
        typeof globalThis.API_SERVICE.fetch === 'function') {
      this.fetcher = this.createSecureFetcher(globalThis.API_SERVICE.fetch.bind(globalThis.API_SERVICE))
    } else if (typeof window !== 'undefined' && window.fetch) {
      // In browser environment, bind fetch to window
      this.fetcher = this.createSecureFetcher(window.fetch.bind(window))
    } else if (typeof globalThis !== 'undefined' && globalThis.fetch) {
      // In other environments, bind to globalThis
      this.fetcher = this.createSecureFetcher(globalThis.fetch.bind(globalThis))
    } else {
      // Last resort fallback
      this.fetcher = this.createSecureFetcher(fetch)
    }
    // baseUrl is now initialized lazily via getBaseUrl()
  }


  // Create a secure fetch wrapper that enforces HTTPS for production
  private createSecureFetcher(originalFetch: typeof fetch): typeof fetch {
    return async (input: RequestInfo | URL, init?: RequestInit) => {
      // Helper to extract URL string from various input types
      const toUrlString = (x: RequestInfo | URL): string =>
        x instanceof Request ? x.url : x instanceof URL ? x.toString() : String(x)

      let url = toUrlString(input)
      const isInsecureApi = url.startsWith('http://') && /:\/\/api\.doxa\.com\.tw\b/.test(url)

      // In production: fail-fast to block insecure calls
      if (isInsecureApi && process.env.NODE_ENV === 'production') {
        console.error('🚨 BLOCKED: Insecure API call in production:', url)
        throw new Error(`Blocked insecure API call: ${url}. Use /api/proxy/* or https://`)
      }

      // In development: upgrade and warn
      if (isInsecureApi && process.env.NODE_ENV !== 'production') {
        const upgraded = url.replace(/^http:/, 'https:')
        console.warn('🛡️ SECURE FETCH (dev): upgraded to HTTPS', { original: url, upgraded })
        url = upgraded
      }

      // Additional check for SSR/Node environments
      if (typeof window === 'undefined' && url.includes('api.doxa.com.tw') && !url.startsWith('https://')) {
        // Force HTTPS in SSR/Node environments
        url = url.replace(/^https?:\/\//, 'https://')
        console.warn('🛡️ SSR/Node: Forced HTTPS for API call')
      }

      // Handle Request objects properly to preserve method/headers/body
      if (input instanceof Request) {
        // Create new Request with updated URL while preserving all properties
        const newRequest = new Request(url, input)
        return originalFetch(newRequest, init)
      }
      
      // Handle URL objects
      if (input instanceof URL) {
        return originalFetch(new URL(url), init)
      }
      
      // String URL
      return originalFetch(url, init)
    }
  }

  // Note: getBaseUrl() is now handled by the getter above

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

  // Generic HTTP methods for plan service and other uses
  async get(path: string) {
    try {
      const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`
      const response = await this.fetcher(url, {
        method: 'GET',
        headers: await this.getHeaders(),
      })

      await this.handleResponse(response)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `GET ${path} failed`)
      }

      return await response.json()
    } catch (error) {
      console.error(`GET ${path} error:`, error)
      throw error
    }
  }

  async post(path: string, data?: any) {
    try {
      const url = path.startsWith('http') ? path : `${this.baseUrl}${path}`
      const response = await this.fetcher(url, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: data ? JSON.stringify(data) : undefined,
      })

      await this.handleResponse(response)

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `POST ${path} failed`)
      }

      return await response.json()
    } catch (error) {
      console.error(`POST ${path} error:`, error)
      throw error
    }
  }

  async healthCheck() {
    try {
      const baseUrl = this.baseUrl
      // Add trailing slash to prevent backend redirect from HTTPS to HTTP
      const url = `${baseUrl}/api/health/`
      console.log('🔍 HEALTH CHECK DEBUG:', {
        baseUrl,
        constructedUrl: url,
        windowProtocol: typeof window !== 'undefined' ? window.location.protocol : 'N/A',
        windowHostname: typeof window !== 'undefined' ? window.location.hostname : 'N/A'
      })
      const response = await this.fetcher(url)
      
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
    const maxRetries = 2
    let lastError: Error | null = null
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await this.fetcher(`${this.baseUrl}/api/v1/user/profile`, {
          headers: await this.getHeaders(),
        })

        if (!response.ok) {
          // If this is a 401 and not the last attempt, wait and retry
          if (response.status === 401 && attempt < maxRetries) {
            debugLog(`getUserProfile: 401 error on attempt ${attempt + 1}, retrying...`)
            await new Promise(resolve => setTimeout(resolve, 500 * (attempt + 1)))
            continue
          }
          throw new Error(`Get profile failed: ${response.statusText}`)
        }

        return await response.json()
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error))
        if (attempt < maxRetries) {
          debugLog(`getUserProfile: Error on attempt ${attempt + 1}, retrying...`, error)
          await new Promise(resolve => setTimeout(resolve, 500 * (attempt + 1)))
          continue
        }
        break
      }
    }
    
    console.error('Get profile error after retries:', lastError)
    throw lastError || new Error('Unknown error occurred')
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

  async updateBillingPreferences(preferences: {
    billingCycle?: 'monthly' | 'yearly',
    autoRenew?: boolean,
    emailNotifications?: {
      paymentSuccess?: boolean,
      paymentFailed?: boolean,
      planChanges?: boolean,
      usageAlerts?: boolean,
      invoices?: boolean
    }
  }) {
    try {
      // For now, store billing preferences in user preferences as well
      const response = await this.fetcher(`${this.baseUrl}/api/v1/user/preferences`, {
        method: 'PUT',
        headers: await this.getHeaders(),
        body: JSON.stringify({
          billing: preferences
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update billing preferences failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update billing preferences error:', error)
      // For now, don't throw to avoid breaking the UI
      console.warn('Billing preferences update not fully implemented, changes saved locally only')
      return { success: false, message: 'Saved locally only' }
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
    status?: string
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
    status?: string
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
    transcription_session_id?: string
  }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions/${sessionId}`, {
        method: 'PATCH',
        headers: await this.getHeaders(),
        body: JSON.stringify(sessionData),
      })

      // Handle 401 errors
      await this.handleResponse(response)

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

  async getClientLastSession(clientId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions/clients/${clientId}/last-session`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        throw new Error(`Get client last session failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get client last session error:', error)
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
        let errorMessage = 'Create transcription session failed'
        try {
          const errorData = await response.json()
          console.error('Create session error details:', errorData)
          
          errorMessage = parseErrorMessage(errorData, errorMessage, this.translateFn)
        } catch (e) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`
        }
        throw new Error(errorMessage)
      }

      return await response.json()
    } catch (error) {
      console.error('Create transcription session error:', error)
      throw error
    }
  }

  async getUploadUrl(sessionId: string, filename: string, fileSizeMB: number) {
    try {
      const params = new URLSearchParams({ 
        filename,
        file_size_mb: fileSizeMB.toString()
      })
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/upload-url?${params}`, {
        method: 'POST',
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        let errorMessage = 'Get upload URL failed'
        try {
          const errorData = await response.json()
          console.error('Upload URL error details:', errorData)
          
          errorMessage = parseErrorMessage(errorData, errorMessage, this.translateFn)
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
            'mp4': 'audio/mp4',
            'm4a': 'audio/mp4'
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

  async exportTranscript(sessionId: string, format: 'json' | 'vtt' | 'srt' | 'txt' | 'xlsx' = 'json') {
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
        
        // Handle case when session is still processing (HTTP 400)
        if (response.status === 400 && errorData.detail?.includes('Transcript not available. Session status:')) {
          // This is normal when transcription is still in progress
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

  async updateSpeakerRoles(sessionId: string, roleAssignments: { [speakerId: number]: 'coach' | 'client' }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/speaker-roles`, {
        method: 'PATCH',
        headers: await this.getHeaders(),
        body: JSON.stringify({
          speaker_roles: roleAssignments
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update speaker roles failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Update speaker roles error:', error)
      throw error
    }
  }

  async updateSegmentRoles(sessionId: string, segmentRoles: { [segmentId: string]: 'coach' | 'client' }) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/sessions/${sessionId}/segment-roles`, {
        method: 'PATCH',
        headers: await this.getHeaders(),
        body: JSON.stringify({
          segment_roles: segmentRoles
        }),
      })
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Update segment roles failed')
      }
      return await response.json()
    } catch (error) {
      console.error('Update segment roles error:', error)
      throw error
    }
  }

  async updateSegmentContent(sessionId: string, segmentContent: { [segmentId: string]: string }) {
    try {
      // Note: This endpoint needs to be implemented in the backend
      // For now, we'll attempt to call it but catch errors gracefully
      const response = await this.fetcher(`${this.baseUrl}/sessions/${sessionId}/segment-content`, {
        method: 'PATCH',
        headers: await this.getHeaders(),
        body: JSON.stringify({
          segment_content: segmentContent
        }),
      })

      if (!response.ok) {
        if (response.status === 404) {
          console.warn('Segment content update endpoint not implemented yet')
          return { success: false, message: 'Endpoint not implemented' }
        }
        throw new Error(`Update segment content failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Update segment content error:', error)
      // For now, return success to not break the UI while backend is being implemented
      return { success: false, message: 'Endpoint not available' }
    }
  }

  async uploadSessionTranscript(sessionId: string, file: File, speakerRoleMapping?: {[speakerId: string]: 'coach' | 'client'}, convertToTraditional?: boolean) {
    try {
      console.log('[API] uploadSessionTranscript called with:', {
        sessionId,
        fileName: file.name,
        speakerRoleMapping,
        convertToTraditional
      });
      
      const formData = new FormData()
      formData.append('file', file)
      
      // Add speaker role mapping if provided
      if (speakerRoleMapping) {
        const rolesJson = JSON.stringify(speakerRoleMapping);
        console.log('[API] Sending speaker_roles:', rolesJson);
        formData.append('speaker_roles', rolesJson)
      }
      
      // Add convert to traditional Chinese option
      if (convertToTraditional) {
        formData.append('convert_to_traditional', 'true')
      }
      
      // Get base headers without Content-Type for FormData
      const headers = await this.getHeaders()
      delete headers['Content-Type'] // Remove Content-Type to let browser set it for FormData
      
      const response = await this.fetcher(`${this.baseUrl}/api/v1/coaching-sessions/${sessionId}/transcript`, {
        method: 'POST',
        headers: headers,
        body: formData,
      })
      
      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload transcript failed')
      }
      
      return await response.json()
    } catch (error) {
      console.error('Upload session transcript error:', error)
      throw error
    }
  }

  // Transcript smoothing methods
  async smoothTranscript(transcript: any, language: string = 'auto', config?: any) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/smooth-and-punctuate`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify({
          transcript,
          language,
          config
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        const errorMessage = parseErrorMessage(errorData, 'Transcript smoothing failed', this.translateFn)
        throw new Error(errorMessage)
      }

      return await response.json()
    } catch (error) {
      console.error('Smooth transcript error:', error)
      throw error
    }
  }

  // LeMUR-based transcript smoothing  
  async lemurSmoothTranscript(transcript: any, language: string = 'auto', customPrompts?: { speakerPrompt?: string, punctuationPrompt?: string }) {
    try {
      const requestBody: any = {
        transcript,
        language
      };
      
      if (customPrompts) {
        requestBody.custom_prompts = customPrompts;
      }
      
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/lemur-smooth`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json()
        const errorMessage = parseErrorMessage(errorData, 'LeMUR transcript optimization failed', this.translateFn)
        throw new Error(errorMessage)
      }

      return await response.json() as LeMURSmoothingResponse
    } catch (error) {
      console.error('LeMUR smooth transcript error:', error)
      throw error
    }
  }

  // LeMUR-based speaker identification only
  async lemurSpeakerIdentification(transcript: any, language: string = 'auto', customPrompts?: { speakerPrompt?: string }) {
    try {
      const requestBody: any = {
        transcript,
        language
      };
      
      if (customPrompts?.speakerPrompt) {
        requestBody.custom_prompts = { speakerPrompt: customPrompts.speakerPrompt };
      }
      
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/lemur-speaker-identification`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json()
        const errorMessage = parseErrorMessage(errorData, 'LeMUR speaker identification failed', this.translateFn)
        throw new Error(errorMessage)
      }

      return await response.json() as LeMURSmoothingResponse
    } catch (error) {
      console.error('LeMUR speaker identification error:', error)
      throw error
    }
  }

  // LeMUR-based punctuation optimization only  
  async lemurPunctuationOptimization(transcript: any, language: string = 'auto', customPrompts?: { punctuationPrompt?: string }) {
    try {
      const requestBody: any = {
        transcript,
        language
      };
      
      if (customPrompts?.punctuationPrompt) {
        requestBody.custom_prompts = { punctuationPrompt: customPrompts.punctuationPrompt };
      }
      
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/lemur-punctuation-optimization`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json()
        const errorMessage = parseErrorMessage(errorData, 'LeMUR punctuation optimization failed', this.translateFn)
        throw new Error(errorMessage)
      }

      return await response.json() as LeMURSmoothingResponse
    } catch (error) {
      console.error('LeMUR punctuation optimization error:', error)
      throw error
    }
  }

  // Database-based LeMUR speaker identification
  async lemurSpeakerIdentificationFromDB(sessionId: string, customPrompts?: { speakerPrompt?: string }) {
    try {
      const requestBody: any = {};
      
      if (customPrompts?.speakerPrompt) {
        requestBody.custom_prompts = { speakerPrompt: customPrompts.speakerPrompt };
      }
      
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/session/${sessionId}/lemur-speaker-identification`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json()
        const errorMessage = parseErrorMessage(errorData, 'DB-based speaker identification failed', this.translateFn)
        throw new Error(errorMessage)
      }

      return await response.json() as LeMURSmoothingResponse
    } catch (error) {
      console.error('DB-based speaker identification error:', error)
      throw error
    }
  }

  // Database-based LeMUR punctuation optimization
  async lemurPunctuationOptimizationFromDB(sessionId: string, customPrompts?: { punctuationPrompt?: string }) {
    try {
      const requestBody: any = {};
      
      if (customPrompts?.punctuationPrompt) {
        requestBody.custom_prompts = { punctuationPrompt: customPrompts.punctuationPrompt };
      }
      
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/session/${sessionId}/lemur-punctuation-optimization`, {
        method: 'POST',
        headers: await this.getHeaders(),
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json()
        const errorMessage = parseErrorMessage(errorData, 'DB-based punctuation optimization failed', this.translateFn)
        throw new Error(errorMessage)
      }

      return await response.json() as LeMURSmoothingResponse
    } catch (error) {
      console.error('DB-based punctuation optimization error:', error)
      throw error
    }
  }

  async getSmoothingDefaults(language: string = 'chinese') {
    try {
      const params = new URLSearchParams({ language })
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/smooth/config/defaults?${params}`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Get smoothing defaults failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Get smoothing defaults error:', error)
      throw error
    }
  }

  async getSupportedLanguages() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/smooth/languages`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Get supported languages failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Get supported languages error:', error)
      throw error
    }
  }

  async getRawAssemblyAiData(sessionId: string) {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/v1/transcript/session/${sessionId}/raw-data`, {
        headers: await this.getHeaders(),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail?.error || 'Get raw AssemblyAI data failed')
      }

      return await response.json()
    } catch (error) {
      console.error('Get raw AssemblyAI data error:', error)
      throw error
    }
  }

  // Usage History APIs
  async getUsageHistory(period: string = '30d', groupBy: string = 'day') {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/usage-history/trends?period=${period}&group_by=${groupBy}`)

      if (!response.ok) {
        throw new Error(`Get usage history failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get usage history error:', error)
      throw error
    }
  }

  async getUsageInsights() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/usage-history/insights`)

      if (!response.ok) {
        throw new Error(`Get usage insights failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get usage insights error:', error)
      throw error
    }
  }

  async getUsagePredictions() {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/usage-history/predictions`)

      if (!response.ok) {
        throw new Error(`Get usage predictions failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Get usage predictions error:', error)
      throw error
    }
  }

  async exportUsageData(format: string = 'json', period: string = '30d') {
    try {
      const response = await this.fetcher(`${this.baseUrl}/api/usage-history/export?format=${format}&period=${period}`)

      if (!response.ok) {
        throw new Error(`Export usage data failed: ${response.statusText}`)
      }

      if (format === 'json') {
        return await response.json()
      } else {
        // For file exports (xlsx, txt), return the blob
        return await response.blob()
      }
    } catch (error) {
      console.error('Export usage data error:', error)
      throw error
    }
  }

  // Refresh token functionality
  async refreshAccessToken(refreshToken: string) {
    try {
      const response = await fetch(`${this.baseUrl}/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshToken }),
      })

      if (!response.ok) {
        throw new Error(`Token refresh failed: ${response.statusText}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Token refresh error:', error)
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
