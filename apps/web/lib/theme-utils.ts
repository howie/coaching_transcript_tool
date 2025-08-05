import { useTheme } from '@/contexts/theme-context'

export function useThemeClasses() {
  const { theme } = useTheme()
  
  return {
    // Background colors - 按照 design-system.md
    dashboardBg: theme === 'dark' ? 'bg-dashboard-bg' : 'bg-dashboard-bg-light',
    headerBg: theme === 'dark' ? 'bg-dashboard-header' : 'bg-dashboard-header-light',
    sidebarBg: theme === 'dark' ? 'bg-dashboard-sidebar' : 'bg-dashboard-sidebar-light',
    cardBg: theme === 'dark' ? 'bg-dashboard-card' : 'bg-dashboard-card-light',
    
    // Text colors - 按照設計文件
    textPrimary: theme === 'dark' ? 'text-dashboard-text' : 'text-dashboard-text-light',
    textSecondary: theme === 'dark' ? 'text-dashboard-text-secondary' : 'text-dashboard-text-secondary-light',
    textTertiary: theme === 'dark' ? 'text-dashboard-text-tertiary' : 'text-gray-600',
    textOnBlue: 'text-white', // 在藍色背景上的文字都是白色
    
    // Accent colors - 黃色強調色在兩個主題都一樣
    accent: 'text-dashboard-accent',
    accentBg: 'bg-dashboard-accent',
    accentHover: 'hover:bg-dashboard-accent-hover',
    
    // Stats colors - 統計數字用淺藍色
    stats: theme === 'dark' ? 'text-dashboard-stats' : 'text-dashboard-stats-light',
    
    // Border colors
    border: theme === 'dark' ? 'border-dashboard-accent-border' : 'border-gray-200',
    cardBorder: theme === 'dark' ? 'border-dashboard-accent border-opacity-20' : 'border-gray-200',
    
    // Input colors
    input: theme === 'dark' 
      ? 'bg-dashboard-input border-dashboard-accent-border text-dashboard-text' 
      : 'bg-white border-gray-300 text-dashboard-text-light',
    inputFocus: 'focus:ring-2 focus:ring-dashboard-accent focus:border-transparent',
    
    // Button colors - 黃色按鈕，深藍色文字
    buttonPrimary: 'bg-dashboard-accent text-dashboard-bg hover:bg-dashboard-accent-hover font-medium',
    buttonSecondary: theme === 'dark'
      ? 'border border-dashboard-accent-border text-dashboard-text-secondary hover:bg-dashboard-accent-bg'
      : 'border border-gray-300 text-dashboard-text-secondary-light hover:bg-gray-50',
    
    // Card styling
    card: theme === 'dark' 
      ? 'bg-dashboard-card border border-dashboard-accent border-opacity-20 rounded-lg'
      : 'bg-dashboard-card-light border border-gray-200 rounded-lg shadow-sm',
  }
}

// Static theme classes for components that don't use hooks
export const themeClasses = {
  dark: {
    dashboardBg: 'dark:bg-dashboard-bg',
    cardBg: 'dark:bg-dashboard-card',
    textPrimary: 'dark:text-white',
    textSecondary: 'dark:text-gray-300',
    border: 'dark:border-dashboard-accent dark:border-opacity-20',
    input: 'dark:bg-gray-700 dark:border-gray-600 dark:text-white',
  },
  light: {
    dashboardBg: 'bg-dashboard-bg-light',
    cardBg: 'bg-dashboard-card-light',
    textPrimary: 'text-dashboard-text-light',
    textSecondary: 'text-dashboard-text-secondary-light',
    border: 'border-gray-200',
    input: 'bg-white border-gray-300 text-dashboard-text-light',
  }
}