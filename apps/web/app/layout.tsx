import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { ThemeProvider } from '@/contexts/theme-context'
import { I18nProvider } from '@/contexts/i18n-context'
import { AuthProvider } from '@/contexts/auth-context'
import { ReCaptchaProvider } from '@/components/recaptcha-provider'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Coachly - 你的 AI 教練夥伴',
  description: '從新手教練到執業認證，Coachly 幫你記錄、成長與實踐。',
  icons: {
    icon: '/images/coachly-favicon.ico',
    shortcut: '/images/coachly-favicon.ico',
    apple: '/images/coachly-favicon.ico',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/images/coachly-favicon.ico" sizes="any" />
        <link 
          href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" 
          rel="stylesheet" 
        />
        <link 
          href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" 
          rel="stylesheet" 
        />
        <script
          dangerouslySetInnerHTML={{
            __html: `
              (function() {
                try {
                  // Theme initialization
                  const stored = localStorage.getItem("theme");
                  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
                  const isDark = stored ? stored === "dark" : prefersDark;
                  if (isDark) {
                    document.documentElement.classList.add("dark");
                    document.body.classList.add("dark-mode");
                  } else {
                    document.body.classList.add("light-mode");
                  }
                  document.documentElement.setAttribute("data-theme", isDark ? "dark" : "light");
                  
                  // Language initialization
                  const storedLang = localStorage.getItem("language");
                  const browserLang = navigator.language.toLowerCase();
                  const lang = storedLang || (browserLang.includes('en') ? 'en' : 'zh');
                  document.documentElement.setAttribute("data-lang", lang);
                  if (!storedLang) {
                    localStorage.setItem("language", lang);
                  }
                } catch (e) {}
              })();
              
              // Chunk loading error recovery
              window.addEventListener('error', function(e) {
                if (e.error && e.error.name === 'ChunkLoadError') {
                  console.warn('Chunk loading failed, reloading page...', e);
                  window.location.reload();
                }
              });
              
              // Unhandled promise rejection for chunk loading
              window.addEventListener('unhandledrejection', function(e) {
                if (e.reason && e.reason.name === 'ChunkLoadError') {
                  console.warn('Chunk loading promise rejected, reloading page...', e);
                  e.preventDefault();
                  window.location.reload();
                }
              });
            `,
          }}
        />
      </head>
      <body className={inter.className} suppressHydrationWarning>
        <AuthProvider>
          <ThemeProvider>
            <I18nProvider>
              <ReCaptchaProvider>
                {children}
              </ReCaptchaProvider>
            </I18nProvider>
          </ThemeProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
