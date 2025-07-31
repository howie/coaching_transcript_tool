'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'

interface SidebarContextType {
  isOpen: boolean
  isCollapsed: boolean
  isMobile: boolean
  toggleSidebar: () => void
  closeSidebar: () => void
  toggleCollapse: () => void
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined)

interface SidebarProviderProps {
  children: ReactNode
}

export function SidebarProvider({ children }: SidebarProviderProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  const [mounted, setMounted] = useState(false)

  // 檢測螢幕尺寸變化
  useEffect(() => {
    setMounted(true)
    
    const checkScreenSize = () => {
      const mobile = window.innerWidth < 1024 // lg breakpoint
      setIsMobile(mobile)
      
      if (mobile) {
        // 移動端：清除 collapsed 狀態
        setIsCollapsed(false)
        // 不自動開啟 sidebar
      } else {
        // 桌面端：載入儲存的 collapsed 狀態
        const savedCollapsed = localStorage.getItem('sidebarCollapsed')
        setIsCollapsed(savedCollapsed === 'true')
        // 桌面端 sidebar 總是顯示，不需要 open 狀態
        setIsOpen(false)
      }
    }

    checkScreenSize()
    window.addEventListener('resize', checkScreenSize)
    
    return () => window.removeEventListener('resize', checkScreenSize)
  }, [])

  const toggleSidebar = () => {
    if (isMobile) {
      setIsOpen(!isOpen)
    } else {
      // 桌面端：切換 collapsed 狀態
      toggleCollapse()
    }
  }

  const closeSidebar = () => {
    setIsOpen(false)
  }

  const toggleCollapse = () => {
    if (!isMobile) {
      const newCollapsed = !isCollapsed
      setIsCollapsed(newCollapsed)
      localStorage.setItem('sidebarCollapsed', newCollapsed.toString())
      
      // 更新 body class 以便 CSS 可以相應調整
      if (newCollapsed) {
        document.body.classList.add('sidebar-collapsed')
      } else {
        document.body.classList.remove('sidebar-collapsed')
      }
    }
  }

  // 避免 hydration 不匹配
  if (!mounted) {
    return (
      <SidebarContext.Provider value={{
        isOpen: false,
        isCollapsed: false,
        isMobile: false,
        toggleSidebar: () => {},
        closeSidebar: () => {},
        toggleCollapse: () => {}
      }}>
        {children}
      </SidebarContext.Provider>
    )
  }

  return (
    <SidebarContext.Provider value={{
      isOpen,
      isCollapsed,
      isMobile,
      toggleSidebar,
      closeSidebar,
      toggleCollapse
    }}>
      {children}
    </SidebarContext.Provider>
  )
}

export function useSidebar() {
  const context = useContext(SidebarContext)
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider')
  }
  return context
}
