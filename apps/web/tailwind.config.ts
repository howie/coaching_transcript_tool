import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Landing Page 主題 - 天藍色系
        'primary-blue': '#71c9f1',
        'nav-dark': '#2c3e50',
        'accent-orange': '#ff6b35',
        'accent-orange-hover': '#e55a2b',
        'section-light': '#f8f9fa',
        'hero-bg': '#71c9f1',
        
        // Dashboard 主題 - 深藍色+黃色系
        'dashboard-bg': '#1C2E4A',
        'dashboard-header': '#71c9f1', // Header 使用淺藍色
        'dashboard-sidebar': '#71c9f1', // Sidebar 使用淺藍色
        'dashboard-card-bg': 'rgba(255, 255, 255, 0.05)',
        'dashboard-accent': '#F5C451', // 黃色強調色（按鈕等）
        'dashboard-accent-hover': '#f3c043',
        'dashboard-stats-blue': '#71c9f1', // 統計數字使用淺藍色
        'dashboard-text': '#ffffff',
        'dashboard-text-secondary': '#b0bdc8',
        'dashboard-text-tertiary': '#94a3b8',
        'dashboard-input-bg': 'rgba(255, 255, 255, 0.05)',
        
        // 通用色彩
        black: '#000000',
        white: '#ffffff',
        gray: {
          100: '#f8f9fa',
          200: '#e9ecef',
          300: '#dee2e6',
          600: '#6c757d',
          800: '#343a40',
        },
        // 保持原有的 shadcn/ui 色彩系統
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "#71c9f1", // Landing 使用天藍色
          foreground: "#ffffff",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "8px", // 統一使用 8px 圓角
        md: "6px",
        sm: "4px",
      },
      boxShadow: {
        'custom': '0 4px 20px rgba(0, 0, 0, 0.1)', // Landing Page 陰影
        'dark': '0 4px 20px rgba(0, 0, 0, 0.3)', // Dashboard 陰影
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}
export default config
