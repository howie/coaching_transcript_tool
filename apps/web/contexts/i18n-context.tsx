'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { translations, Language, TranslationKey } from '@/lib/translations'

interface I18nContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: TranslationKey) => string
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

  const t = (key: TranslationKey): string => {
    // 直接從翻譯物件中獲取對應的值
    const value = translations[language]?.[key]
    
    // 如果當前語言沒有找到，回退到中文
    if (value) {
      return value
    }
    
    const fallbackValue = translations['zh']?.[key]
    if (fallbackValue) {
      return fallbackValue
    }
    
    // 最後回退到原始 key
    return key
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
