'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { translations, Language, TranslationKey } from '@/lib/i18n'

interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: TranslationKey | string, params?: Record<string, any>) => string
}

const I18nContext = createContext<I18nContextType | undefined>(undefined)

interface I18nProviderProps {
  children: ReactNode
}

export function I18nProvider({ children }: I18nProviderProps) {
  // Get initial language from data attribute if available (set by script in layout)
  const getInitialLanguage = (): Language => {
    if (typeof window !== 'undefined') {
      const dataLang = document.documentElement.getAttribute('data-lang') as Language
      if (dataLang === 'zh' || dataLang === 'en') {
        return dataLang
      }
    }
    return 'zh'
  }

  const [language, setLanguageState] = useState<Language>(getInitialLanguage)
  const [isLoading, setIsLoading] = useState(false)

  // Ensure language is synced with localStorage on mount
  useEffect(() => {
    const savedLanguage = localStorage.getItem('language') as Language
    if (savedLanguage && (savedLanguage === 'zh' || savedLanguage === 'en')) {
      if (savedLanguage !== language) {
        setLanguageState(savedLanguage)
      }
    }
  }, [])

  const setLanguage = (lang: Language) => {
    setLanguageState(lang)
    localStorage.setItem('language', lang)
  }

  const t = (key: TranslationKey | string, params?: Record<string, any>): string => {
    // 直接從翻譯物件中獲取對應的值
    let value = translations[language]?.[key as TranslationKey]
    
    // 如果當前語言沒有找到，回退到中文
    if (!value) {
      value = translations['zh']?.[key as TranslationKey]
    }
    
    // 如果還是沒找到，回退到原始 key
    if (!value) {
      value = key
    }
    
    // 如果有參數，進行字串插值
    if (params && typeof value === 'string') {
      Object.entries(params).forEach(([paramKey, paramValue]) => {
        const placeholder = `{${paramKey}}`
        value = value.replace(new RegExp(placeholder.replace(/[{}]/g, '\\$&'), 'g'), String(paramValue))
      })
    }
    
    return value
  }

  // During loading, provide a consistent state
  // This prevents hydration mismatches while still showing content
  const value = {
    language,
    setLanguage: isLoading ? () => {} : setLanguage,
    t
  }

  return (
    <I18nContext.Provider value={value}>
      {children}
    </I18nContext.Provider>
  )
}

export function useI18n() {
  const context = useContext(I18nContext)
  if (context === undefined) {
    throw new Error('useI18n must be used within a I18nProvider')
  }
  return context
}
