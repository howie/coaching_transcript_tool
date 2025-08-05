'use client'

import { useState, useEffect } from 'react'
import { 
  UserCircleIcon, 
  KeyIcon,
  TrashIcon,
  GlobeAltIcon,
  PaintBrushIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  LinkIcon
} from '@heroicons/react/24/outline'
import { useI18n } from '@/contexts/i18n-context'
import { useTheme } from '@/contexts/theme-context'
import { useAuth } from '@/contexts/auth-context'
import { useThemeClasses } from '@/lib/theme-utils'
import { apiClient } from '@/lib/api'

interface UserProfile {
  id: string
  email: string
  name: string
  plan: string
  auth_provider?: 'email' | 'google'
  google_connected?: boolean
}

export default function AccountSettingsPage() {
  const { t, language, setLanguage } = useI18n()
  const { theme, setTheme } = useTheme()
  const { user, loadUser, updateUserPreferences, updateProfile } = useAuth()
  const themeClasses = useThemeClasses()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [updateSuccess, setUpdateSuccess] = useState('')
  const [updateError, setUpdateError] = useState('')
  
  // Personal information
  const [profile, setProfile] = useState<UserProfile | null>(null)
  const [personalInfo, setPersonalInfo] = useState({
    name: '',
    email: ''
  })
  
  // Password change
  const [passwordData, setPasswordData] = useState({
    currentPassword: '',
    newPassword: '',
    confirmPassword: ''
  })
  const [passwordError, setPasswordError] = useState('')
  const [passwordSuccess, setPasswordSuccess] = useState(false)

  // Load user profile on mount
  useEffect(() => {
    loadUserProfile()
  }, [user])

  const loadUserProfile = async () => {
    try {
      if (user) {
        // Use user from auth context first
        setProfile(user)
        setPersonalInfo({
          name: user.name || '',
          email: user.email || ''
        })
      } else {
        // Fallback to API call if user not loaded in context
        await loadUser()
      }
    } catch (error) {
      console.error('Failed to load profile:', error)
    }
  }

  const handlePersonalInfoSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setUpdateError('')
    setUpdateSuccess('')
    
    try {
      await updateProfile({ name: personalInfo.name })
      setUpdateSuccess(t('account.updateSuccess'))
      setTimeout(() => setUpdateSuccess(''), 3000)
    } catch (error) {
      setUpdateError(t('account.updateError'))
    } finally {
      setIsLoading(false)
    }
  }

  const handlePasswordChange = (field: string, value: string) => {
    setPasswordData(prev => ({
      ...prev,
      [field]: value
    }))
    setPasswordError('')
  }

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      setPasswordError(t('account.passwordMismatch'))
      return
    }
    
    if (passwordData.newPassword.length < 8) {
      setPasswordError(t('account.passwordTooShort'))
      return
    }
    
    setIsLoading(true)
    setPasswordError('')
    setPasswordSuccess(false)
    
    try {
      await apiClient.changePassword(passwordData.currentPassword, passwordData.newPassword)
      setPasswordSuccess(true)
      setPasswordData({
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      })
      setTimeout(() => setPasswordSuccess(false), 5000)
    } catch (error) {
      setPasswordError(t('account.passwordChangeFailed'))
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteAccount = async () => {
    try {
      await apiClient.deleteAccount()
      // Logout and redirect
      window.location.href = '/'
    } catch (error) {
      console.error('Failed to delete account:', error)
    }
    setShowDeleteConfirm(false)
  }

  const canChangePassword = profile?.auth_provider === 'email'

  return (
    <div className="min-h-screen" style={{backgroundColor: 'var(--bg-primary)', color: 'var(--text-primary)'}}>
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* Page Title */}
        <div className="flex items-center space-x-3 mb-8">
          <UserCircleIcon className="h-8 w-8 text-dashboard-accent" />
          <h1 className="text-3xl font-bold" style={{color: 'var(--text-primary)'}}>{t('account.title')}</h1>
        </div>

        {/* Success/Error Messages */}
        {updateSuccess && (
          <div className="mb-6 p-4 bg-green-600 bg-opacity-20 border border-green-600 rounded-lg">
            <p className="text-green-400">{updateSuccess}</p>
          </div>
        )}
        
        {updateError && (
          <div className="mb-6 p-4 bg-red-600 bg-opacity-20 border border-red-600 rounded-lg">
            <p className="text-red-400">{updateError}</p>
          </div>
        )}

        <div className="space-y-8">
          {/* Personal Information */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <UserCircleIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('account.personalInfo')}</h2>
            </div>
            
            <form onSubmit={handlePersonalInfoSubmit} className="space-y-4">
              <div>
                <label className="label">
                  {t('account.fullName')}
                </label>
                <input
                  type="text"
                  value={personalInfo.name}
                  onChange={(e) => setPersonalInfo(prev => ({ ...prev, name: e.target.value }))}
                  className="input-base"
                  placeholder={t('account.fullNamePlaceholder')}
                />
              </div>

              <div>
                <label className="label">
                  {t('account.email')}
                </label>
                <input
                  type="email"
                  value={personalInfo.email}
                  disabled
                  className="input-base"
                />
                <p className="helper mt-1">{t('account.emailHint')}</p>
              </div>

              <div className="pt-4">
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-6 py-2 bg-dashboard-accent text-dashboard-bg rounded-lg hover:bg-dashboard-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                >
                  {isLoading ? t('common.saving') : t('common.save')}
                </button>
              </div>
            </form>
          </div>

          {/* Connected Accounts */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <LinkIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('account.connectedAccounts')}</h2>
            </div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                <div className="flex items-center space-x-4">
                  <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center">
                    <svg className="w-6 h-6" viewBox="0 0 48 48">
                      <path fill="#4285F4" d="M24 9.5c3.9 0 6.9 1.6 9.1 3.7l6.9-6.9C35.2 2.5 30.1 0 24 0 14.8 0 7.1 5.3 3 12.9l8.4 6.5C13.1 13.3 18.1 9.5 24 9.5z"></path>
                      <path fill="#34A853" d="M46.2 25.4c0-1.7-.2-3.4-.5-5H24v9.5h12.5c-.5 3.1-2.1 5.7-4.6 7.5l7.3 5.7c4.3-4 6.9-10 6.9-17.7z"></path>
                      <path fill="#FBBC05" d="M11.4 28.5c-.4-1.2-.6-2.5-.6-3.9s.2-2.7.6-3.9l-8.4-6.5C1.1 18.1 0 21.9 0 26.1s1.1 8 3 11.4l8.4-6.5z"></path>
                      <path fill="#EA4335" d="M24 48c5.9 0 11-2 14.7-5.4l-7.3-5.7c-2 1.3-4.5 2.1-7.4 2.1-5.9 0-11-3.8-12.9-9.1L3 37.5C7.1 44.7 14.8 48 24 48z"></path>
                    </svg>
                  </div>
                  <div>
                    <p className="font-medium" style={{color: 'var(--text-primary)'}}>Google</p>
                    <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>
                      {profile?.auth_provider === 'google' 
                        ? t('account.primaryLogin')
                        : profile?.google_connected 
                          ? t('account.connected')
                          : t('account.notConnected')}
                    </p>
                  </div>
                </div>
                {profile?.auth_provider !== 'google' && (
                  <button
                    className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                      profile?.google_connected
                        ? 'border border-gray-600 text-gray-300 hover:bg-gray-700'
                        : 'bg-dashboard-accent text-dashboard-bg hover:bg-dashboard-accent-hover'
                    }`}
                  >
                    {profile?.google_connected ? t('account.disconnect') : t('account.connect')}
                  </button>
                )}
              </div>
            </div>
          </div>

          {/* Password Change - Only show for email auth */}
          {canChangePassword && (
            <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
              <div className="flex items-center space-x-3 mb-6">
                <KeyIcon className="h-6 w-6 text-dashboard-accent" />
                <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('account.passwordManagement')}</h2>
              </div>
              
              {passwordSuccess && (
                <div className="mb-4 p-3 bg-green-600 bg-opacity-20 border border-green-600 rounded-lg">
                  <p className="text-green-400 text-sm">{t('account.passwordChangeSuccess')}</p>
                </div>
              )}
              
              {passwordError && (
                <div className="mb-4 p-3 bg-red-600 bg-opacity-20 border border-red-600 rounded-lg">
                  <p className="text-red-400 text-sm">{passwordError}</p>
                </div>
              )}
              
              <form onSubmit={handlePasswordSubmit} className="space-y-4">
                <div>
                  <label className="label">
                    {t('account.currentPassword')}
                  </label>
                  <input
                    type="password"
                    value={passwordData.currentPassword}
                    onChange={(e) => handlePasswordChange('currentPassword', e.target.value)}
                    className="input-base"
                    placeholder="••••••••"
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="label">
                      {t('account.newPassword')}
                    </label>
                    <input
                      type="password"
                      value={passwordData.newPassword}
                      onChange={(e) => handlePasswordChange('newPassword', e.target.value)}
                      className="input-base"
                      placeholder="••••••••"
                      required
                    />
                  </div>

                  <div>
                    <label className="label">
                      {t('account.confirmPassword')}
                    </label>
                    <input
                      type="password"
                      value={passwordData.confirmPassword}
                      onChange={(e) => handlePasswordChange('confirmPassword', e.target.value)}
                      className="input-base"
                      placeholder="••••••••"
                      required
                    />
                  </div>
                </div>

                <div className="flex items-center justify-between pt-4">
                  <a
                    href="/forgot-password"
                    className="text-dashboard-accent hover:text-dashboard-accent-hover text-sm font-medium"
                  >
                    {t('account.forgotPassword')}
                  </a>
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="px-6 py-2 bg-dashboard-accent text-dashboard-bg rounded-lg hover:bg-dashboard-accent-hover transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-medium"
                  >
                    {isLoading ? t('common.updating') : t('account.updatePassword')}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Preferences */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <PaintBrushIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('account.preferences')}</h2>
            </div>
            
            <div className="space-y-6">
              {/* Language Setting */}
              <div>
                <label className="label">
                  {t('account.preferredLanguage')}
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={async () => {
                      setLanguage('zh')
                      try {
                        await updateUserPreferences({ language: 'zh' })
                      } catch (error) {
                        console.error('Failed to save language preference:', error)
                      }
                    }}
                    className={`p-4 rounded-lg border ${
                      language === 'zh' 
                        ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10' 
                        : 'border-gray-600 hover:border-gray-500'
                    } transition-colors`}
                  >
                    <div className="text-2xl mb-2">🇹🇼</div>
                    <div className="font-medium">繁體中文</div>
                  </button>
                  <button
                    onClick={async () => {
                      setLanguage('en')
                      try {
                        await updateUserPreferences({ language: 'en' })
                      } catch (error) {
                        console.error('Failed to save language preference:', error)
                      }
                    }}
                    className={`p-4 rounded-lg border ${
                      language === 'en' 
                        ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10' 
                        : 'border-gray-600 hover:border-gray-500'
                    } transition-colors`}
                  >
                    <div className="text-2xl mb-2">🇺🇸</div>
                    <div className="font-medium">English</div>
                  </button>
                </div>
              </div>

              {/* Theme Setting */}
              <div>
                <label className="label">
                  {t('account.preferredTheme')}
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <button
                    onClick={() => setTheme('dark')}
                    className={`p-4 rounded-lg border ${
                      theme === 'dark' 
                        ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10' 
                        : 'border-gray-600 hover:border-gray-500'
                    } transition-colors`}
                  >
                    <div className="text-2xl mb-2">🌙</div>
                    <div className="font-medium">{t('account.darkTheme')}</div>
                  </button>
                  <button
                    onClick={() => setTheme('light')}
                    className={`p-4 rounded-lg border ${
                      theme === 'light' 
                        ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10' 
                        : 'border-gray-600 hover:border-gray-500'
                    } transition-colors`}
                  >
                    <div className="text-2xl mb-2">☀️</div>
                    <div className="font-medium">{t('account.lightTheme')}</div>
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="bg-red-900 bg-opacity-20 rounded-lg p-6 border border-red-600 border-opacity-50">
            <div className="flex items-center space-x-3 mb-6">
              <ExclamationTriangleIcon className="h-6 w-6 text-red-500" />
              <h2 className="text-xl font-semibold text-red-500">{t('account.dangerZone')}</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <h3 className="font-medium mb-2">{t('account.deleteAccount')}</h3>
                <p className="text-sm text-gray-300 mb-4">
                  {t('account.deleteAccountWarning')}
                </p>
                <button
                  onClick={() => setShowDeleteConfirm(true)}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  {t('account.deleteMyAccount')}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Delete Confirmation Dialog */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4">
              <div className="flex items-center space-x-3 mb-4">
                <ExclamationTriangleIcon className="h-8 w-8 text-red-500" />
                <h3 className="text-xl font-semibold">{t('account.confirmDelete')}</h3>
              </div>
              <p className="text-gray-300 mb-6">
                {t('account.confirmDeleteMessage')}
              </p>
              <div className="flex space-x-4">
                <button
                  onClick={() => setShowDeleteConfirm(false)}
                  className="flex-1 px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
                >
                  {t('common.cancel')}
                </button>
                <button
                  onClick={handleDeleteAccount}
                  className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  {t('common.confirmDelete')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}