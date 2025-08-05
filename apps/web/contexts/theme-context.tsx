'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

type Theme = 'light' | 'dark'

interface ThemeContextType {
  theme: Theme
  setTheme: (theme: Theme) => void
  toggleTheme: () => void
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined)

interface ThemeProviderProps {
  children: ReactNode
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setThemeState] = useState<Theme>('light')
  const [mounted, setMounted] = useState(false)

  // 避免 hydration 錯誤
  useEffect(() => {
    setMounted(true)
    // 載入儲存的主題設定
    const savedTheme = localStorage.getItem('theme') as Theme
    if (savedTheme && (savedTheme === 'light' || savedTheme === 'dark')) {
      setThemeState(savedTheme)
      applyTheme(savedTheme)
    } else {
      // 預設使用淺色模式
      setThemeState('light')
      applyTheme('light')
    }
  }, [])

  const applyTheme = (newTheme: Theme) => {
    // 使用 data-theme 屬性統一主題選擇器
    document.documentElement.setAttribute('data-theme', newTheme)
    
    // 保持向後相容性的類別（可以考慮在後續版本移除）
    if (newTheme === 'dark') {
      document.body.classList.add('dark-mode')
      document.documentElement.classList.add('dark')
      document.body.classList.remove('light-mode')
    } else {
      document.body.classList.remove('dark-mode')
      document.documentElement.classList.remove('dark')
      document.body.classList.add('light-mode')
    }
  }

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme)
    localStorage.setItem('theme', newTheme)
    applyTheme(newTheme)
  }

  const toggleTheme = () => {
    const newTheme = theme === 'light' ? 'dark' : 'light'
    setTheme(newTheme)
  }

  // 避免 hydration 不匹配
  if (!mounted) {
    return (
      <ThemeContext.Provider value={{ theme: 'light', setTheme: () => {}, toggleTheme: () => {} }}>
        {children}
      </ThemeContext.Provider>
    )
  }

  return (
    <ThemeContext.Provider value={{ theme, setTheme, toggleTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider')
  }
  return context
}
