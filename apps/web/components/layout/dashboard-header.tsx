'use client'

import { useState } from 'react'
import Image from 'next/image'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ChevronDownIcon, BellIcon, QuestionMarkCircleIcon } from '@heroicons/react/24/outline'
import { Bars3Icon } from '@heroicons/react/24/solid'
import { useTheme } from '@/contexts/theme-context'
import { useI18n } from '@/contexts/i18n-context'
import { useSidebar } from '@/contexts/sidebar-context'
import { useAuth } from '@/contexts/auth-context'

export function DashboardHeader() {
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [showHelpMenu, setShowHelpMenu] = useState(false)
  const [showLanguageMenu, setShowLanguageMenu] = useState(false)
  
  const { theme, setTheme } = useTheme()
  const { language, setLanguage, t } = useI18n()
  const { toggleSidebar, toggleCollapse } = useSidebar()
  const { user, logout } = useAuth()
  const router = useRouter()

  const handleLogout = async () => {
    try {
      // Clear local storage
      localStorage.removeItem('theme')
      localStorage.removeItem('language')
      localStorage.removeItem('sidebarCollapsed')
      
      // Call auth context logout
      logout()
      
      // Redirect to home page
      router.push('/')
    } catch (error) {
      console.error(t('dashboard.logoutFailed'), error)
    }
  }

  const switchLanguage = (lang: 'zh' | 'en') => {
    setLanguage(lang)
    setShowLanguageMenu(false)
  }

  return (
    <header className="bg-dashboard-header shadow-dark border-b border-dashboard-accent border-opacity-20 sticky top-0 z-50">
      <div className="flex justify-between items-center h-16 px-4">
        {/* Left side */}
        <div className="flex items-center space-x-4">
          {/* Mobile hamburger button */}
          <button
            onClick={toggleSidebar}
            className="lg:hidden text-white hover:text-dashboard-accent transition-colors p-1"
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          
          {/* Desktop collapse button */}
          <button
            onClick={toggleCollapse}
            className="hidden lg:block text-white hover:text-dashboard-accent transition-colors p-1"
            title={t('dashboard.toggleSidebar')}
          >
            <Bars3Icon className="h-6 w-6" />
          </button>
          
          <Link href="/dashboard" className="flex items-center space-x-2">
            <Image 
              src="/images/Coachly-logo-transparent-300px.png" 
              alt="Coachly Logo" 
              width={24} 
              height={24}
              className="w-6 h-6"
            />
            <span className="text-xl font-bold text-white">Coachly</span>
          </Link>
        </div>

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Notifications */}
          <button 
            className="p-2 text-white hover:text-dashboard-accent transition-colors rounded-md hover:bg-dashboard-accent hover:bg-opacity-10"
            title={t('dashboard.notifications')}
          >
            <BellIcon className="h-5 w-5" />
          </button>

          {/* Help dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowHelpMenu(!showHelpMenu)}
              className="p-2 text-white hover:text-dashboard-accent transition-colors rounded-md hover:bg-dashboard-accent hover:bg-opacity-10"
              title={t('dashboard.help')}
            >
              <QuestionMarkCircleIcon className="h-5 w-5" />
            </button>

            {showHelpMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                <div className="px-4 py-2 flex items-center space-x-3 text-sm text-gray-700 dark:text-gray-300">
                  <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                  <span>{t('dashboard.systemStatusOk')}</span>
                </div>
                <div className="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                <a href="#" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3">
                  <QuestionMarkCircleIcon className="h-4 w-4" />
                  <span>{t('help.get_help')}</span>
                </a>
                <a href="#" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3">
                  <span className="text-dashboard-accent">🌐</span>
                  <span>{t('help.community_hub')}</span>
                </a>
                <a href="#" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3">
                  <span className="text-dashboard-accent">⭐</span>
                  <span>{t('help.view_updates')}</span>
                </a>
                <a href="#" className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3">
                  <span className="text-dashboard-accent">📚</span>
                  <span>{t('help.read_docs')}</span>
                </a>
              </div>
            )}
          </div>

          {/* User dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex items-center space-x-2 p-2 text-white hover:text-dashboard-accent transition-colors rounded-md hover:bg-dashboard-accent hover:bg-opacity-10"
            >
              <div className="w-6 h-6 bg-dashboard-accent rounded-full flex items-center justify-center text-white text-sm font-medium">
                {user?.name?.charAt(0).toUpperCase() || 'U'}
              </div>
              <span className="text-sm font-medium">{user?.name || 'User'}</span>
              <ChevronDownIcon className="h-4 w-4" />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 py-2 z-50">
                <Link href={'/dashboard/account-settings' as any} className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 flex items-center space-x-3">
                  <span className="text-dashboard-accent">⚙️</span>
                  <span>{t('menu.account')}</span>
                </Link>
                
                <div className="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                
                {/* Theme toggle */}
                <div className="px-4 py-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-dashboard-accent">🎨</span>
                      <span className="text-sm text-gray-700 dark:text-gray-300">{t('menu.theme')}</span>
                    </div>
                    <div className="flex space-x-1">
                      <button
                        onClick={() => setTheme('dark')}
                        className={`p-1 rounded ${theme === 'dark' ? 'bg-dashboard-accent text-white' : 'text-gray-400 hover:text-gray-600'}`}
                        title={t('account.darkTheme')}
                      >
                        🌙
                      </button>
                      <button
                        onClick={() => setTheme('light')}
                        className={`p-1 rounded ${theme === 'light' ? 'bg-dashboard-accent text-white' : 'text-gray-400 hover:text-gray-600'}`}
                        title={t('account.lightTheme')}
                      >
                        ☀️
                      </button>
                    </div>
                  </div>
                </div>

                {/* Language selector */}
                <div className="px-4 py-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <span className="text-dashboard-accent">🌐</span>
                      <span className="text-sm text-gray-700 dark:text-gray-300">{t('menu.language')}</span>
                    </div>
                    <div className="relative">
                      <button
                        onClick={() => setShowLanguageMenu(!showLanguageMenu)}
                        className="flex items-center space-x-1 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-800 dark:hover:text-gray-200"
                      >
                        <span>{language === 'zh' ? '🇹🇼 ZH' : '🇺🇸 EN'}</span>
                        <ChevronDownIcon className="h-3 w-3" />
                      </button>

                      {showLanguageMenu && (
                        <div className="absolute right-0 mt-1 w-32 bg-white dark:bg-gray-700 rounded-md shadow-lg border border-gray-200 dark:border-gray-600 py-1">
                          <button
                            onClick={() => switchLanguage('zh')}
                            className="block w-full text-left px-3 py-1 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
                          >
                            🇹🇼 {t('layout.traditionalChinese')}
                          </button>
                          <button
                            onClick={() => switchLanguage('en')}
                            className="block w-full text-left px-3 py-1 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600"
                          >
                            🇺🇸 English
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                <div className="border-t border-gray-100 dark:border-gray-700 my-1"></div>
                
                <button 
                  onClick={handleLogout}
                  className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center space-x-3"
                >
                  <span>🚪</span>
                  <span>{t('nav.logout')}</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Click outside to close dropdowns */}
      {(showUserMenu || showHelpMenu || showLanguageMenu) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setShowUserMenu(false)
            setShowHelpMenu(false)
            setShowLanguageMenu(false)
          }}
        />
      )}
    </header>
  )
}
