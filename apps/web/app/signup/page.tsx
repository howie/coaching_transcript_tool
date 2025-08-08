'use client'

import Link from 'next/link'
import { useState, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { useI18n } from '@/contexts/i18n-context'
import { apiClient } from '@/lib/api'
import { useAuth } from '@/contexts/auth-context'
import { useReCaptcha } from '@/components/recaptcha-provider'

export default function SignupPage() {
  const { t } = useI18n()
  const router = useRouter()
  const { login } = useAuth()
  const { getReCaptchaToken } = useReCaptcha()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showSuccess, setShowSuccess] = useState(false)
  const [recaptchaError, setRecaptchaError] = useState(false)

  const handleGoogleSignup = () => {
    // Redirect to backend Google login endpoint
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/google/login`
  }

  const handleSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError('密碼不符')
      return
    }
    
    setIsLoading(true)
    setError('')
    setRecaptchaError(false)
    
    try {
      // Get reCAPTCHA token
      const recaptchaToken = await getReCaptchaToken('signup');
      if (!recaptchaToken) {
        console.warn('Could not get reCAPTCHA token.');
        setRecaptchaError(true);
        // Depending on strictness, you might want to stop here
        // For now, we'll proceed as per the spec's fallback suggestion
      }
      
      const response = await apiClient.signup(name, email, password, recaptchaToken)
      
      // Show success message
      setShowSuccess(true)
      
      // Auto-login after successful registration
      if (response.access_token) {
        login(response.access_token)
        
        // Redirect to profile page after 2 seconds
        setTimeout(() => {
          router.push('/dashboard/profile')
        }, 2000)
      } else {
        // If no token returned, redirect to login
        setTimeout(() => {
          router.push('/login')
        }, 2000)
      }
    } catch (err) {
      if (err instanceof Error && err.message.includes('Human Verification')) {
        setError('人機驗證失敗，請稍後再試')
      } else {
        setError(err instanceof Error ? err.message : '發生未知錯誤')
      }
      setIsLoading(false)
    }
  }, [name, email, password, confirmPassword, getReCaptchaToken, login, router])

  return (
    <div className="flex items-center justify-center min-h-screen" style={{backgroundColor: 'var(--section-light)'}}>
      <div className="w-full max-w-md p-8 space-y-6 rounded-lg shadow-md" style={{backgroundColor: 'var(--white)', boxShadow: 'var(--shadow)'}}>
        {showSuccess ? (
          // Success message
          <div className="text-center space-y-4">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold" style={{color: 'var(--text-primary)'}}>
              註冊成功！
            </h2>
            <p style={{color: 'var(--text-secondary)'}}>
              歡迎加入 Coachly！正在為您跳轉到個人資料頁面...
            </p>
            <div className="flex justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          </div>
        ) : (
          <>
            <h1 className="text-2xl font-bold text-center" style={{color: 'var(--text-primary)'}}>
              建立您的帳號
            </h1>
        
        <button
          onClick={handleGoogleSignup}
          className="w-full flex items-center justify-center px-4 py-2 border rounded-md shadow-sm text-sm font-medium transition-colors" style={{borderColor: 'var(--input-border)', backgroundColor: 'var(--input-bg)', color: 'var(--input-text)'}}
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 48 48">
            <path fill="#4285F4" d="M24 9.5c3.9 0 6.9 1.6 9.1 3.7l6.9-6.9C35.2 2.5 30.1 0 24 0 14.8 0 7.1 5.3 3 12.9l8.4 6.5C13.1 13.3 18.1 9.5 24 9.5z"></path>
            <path fill="#34A853" d="M46.2 25.4c0-1.7-.2-3.4-.5-5H24v9.5h12.5c-.5 3.1-2.1 5.7-4.6 7.5l7.3 5.7c4.3-4 6.9-10 6.9-17.7z"></path>
            <path fill="#FBBC05" d="M11.4 28.5c-.4-1.2-.6-2.5-.6-3.9s.2-2.7.6-3.9l-8.4-6.5C1.1 18.1 0 21.9 0 26.1s1.1 8 3 11.4l8.4-6.5z"></path>
            <path fill="#EA4335" d="M24 48c5.9 0 11-2 14.7-5.4l-7.3-5.7c-2 1.3-4.5 2.1-7.4 2.1-5.9 0-11-3.8-12.9-9.1L3 37.5C7.1 44.7 14.8 48 24 48z"></path>
            <path fill="none" d="M0 0h48v48H0z"></path>
          </svg>
          使用 Google 註冊
        </button>

        <div className="flex items-center justify-center space-x-2">
          <span className="h-px bg-gray-300 w-full"></span>
          <span className="text-gray-500 font-normal">或</span>
          <span className="h-px bg-gray-300 w-full"></span>
        </div>

        <form className="space-y-4" onSubmit={handleSubmit}>
          <div>
            <label className="label">
              Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="input-base"
              placeholder="Your Name"
              required
            />
          </div>
          <div>
            <label className="label">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="input-base"
              placeholder="you@example.com"
              required
            />
          </div>
          <div>
            <label className="label">
              密碼
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="input-base"
              placeholder="••••••••"
              required
            />
          </div>
          <div>
            <label className="label">
              確認密碼
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="input-base"
              placeholder="••••••••"
              required
            />
          </div>
          {error && <p className="error-text">{error}</p>}
          {recaptchaError && (
            <div className="p-3 rounded-md bg-yellow-50 border border-yellow-200">
              <p className="text-sm text-yellow-800">
                ⚠️ 無法載入人機驗證服務，但您仍可以繼續註冊。如果遇到問題，請稍後再試。
              </p>
            </div>
          )}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full px-4 py-2 rounded-md transition-colors focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed" style={{backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)'}}
          >
            {isLoading ? '註冊中...' : '註冊'}
          </button>
        </form>
        <p className="text-sm text-center" style={{color: 'var(--text-secondary)'}}>
          已經有帳號了嗎？{' '}
          <Link href={'/login' as any} className="font-medium hover:opacity-80" style={{color: 'var(--accent-color)'}}>
            登入
          </Link>
        </p>
          </>
        )}
      </div>
    </div>
  )
}
