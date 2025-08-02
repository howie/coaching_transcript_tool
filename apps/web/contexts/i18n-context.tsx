'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { translations, Language, TranslationKey } from '../lib/translations'

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
  const [language, setLanguageState] = useState<Language>('zh')
  const [mounted, setMounted] = useState(false)

  // 避免 hydration 錯誤
  useEffect(() => {
    setMounted(true)
    // 載入儲存的語言設定
    const savedLanguage = localStorage.getItem('language') as Language
    if (savedLanguage && (savedLanguage === 'zh' || savedLanguage === 'en')) {
      setLanguageState(savedLanguage)
    } else {
      // 預設使用繁體中文
      setLanguageState('zh')
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

  // 避免 hydration 不匹配
  if (!mounted) {
    return (
      <I18nContext.Provider value={{ 
        language: 'zh', 
        setLanguage: () => {}, 
        t: (key: TranslationKey) => translations['zh'][key] || key 
      }}>
        {children}
      </I18nContext.Provider>
    )
  }

  return (
    <I18nContext.Provider value={{ language, setLanguage, t }}>
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
