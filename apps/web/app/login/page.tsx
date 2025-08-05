'use client'

import Link from 'next/link'
import { useState } from 'react'
import { useI18n } from '@/contexts/i18n-context'

export default function LoginPage() {
  const { t } = useI18n()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleGoogleLogin = () => {
    // Redirect to backend Google login endpoint
    window.location.href = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/v1/auth/google/login`
  }

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <div className="w-full max-w-md p-8 space-y-6 bg-white rounded-lg shadow-md dark:bg-gray-800">
        <h1 className="text-2xl font-bold text-center text-gray-900 dark:text-white">
          {t('nav.login')}
        </h1>
        
        <button
          onClick={handleGoogleLogin}
          className="w-full flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600"
        >
          <svg className="w-5 h-5 mr-2" viewBox="0 0 48 48">
            <path fill="#4285F4" d="M24 9.5c3.9 0 6.9 1.6 9.1 3.7l6.9-6.9C35.2 2.5 30.1 0 24 0 14.8 0 7.1 5.3 3 12.9l8.4 6.5C13.1 13.3 18.1 9.5 24 9.5z"></path>
            <path fill="#34A853" d="M46.2 25.4c0-1.7-.2-3.4-.5-5H24v9.5h12.5c-.5 3.1-2.1 5.7-4.6 7.5l7.3 5.7c4.3-4 6.9-10 6.9-17.7z"></path>
            <path fill="#FBBC05" d="M11.4 28.5c-.4-1.2-.6-2.5-.6-3.9s.2-2.7.6-3.9l-8.4-6.5C1.1 18.1 0 21.9 0 26.1s1.1 8 3 11.4l8.4-6.5z"></path>
            <path fill="#EA4335" d="M24 48c5.9 0 11-2 14.7-5.4l-7.3-5.7c-2 1.3-4.5 2.1-7.4 2.1-5.9 0-11-3.8-12.9-9.1L3 37.5C7.1 44.7 14.8 48 24 48z"></path>
            <path fill="none" d="M0 0h48v48H0z"></path>
          </svg>
          使用 Google 登入
        </button>

        <div className="flex items-center justify-center space-x-2">
          <span className="h-px bg-gray-300 w-full"></span>
          <span className="text-gray-500 font-normal">或</span>
          <span className="h-px bg-gray-300 w-full"></span>
        </div>

        <form className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="you@example.com"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              密碼
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 mt-1 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
              placeholder="••••••••"
            />
          </div>
          <button
            type="submit"
            className="w-full px-4 py-2 text-white bg-indigo-600 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
          >
            登入
          </button>
        </form>
        <p className="text-sm text-center text-gray-600 dark:text-gray-400">
          還沒有帳號嗎？{' '}
          <Link href={'/signup' as any} className="font-medium text-indigo-600 hover:text-indigo-500">
            建立帳號
          </Link>
        </p>
      </div>
    </div>
  )
}
