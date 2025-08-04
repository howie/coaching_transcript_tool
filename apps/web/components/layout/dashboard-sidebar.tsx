'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  HomeIcon, 
  DocumentTextIcon, 
  ChartBarIcon, 
  LightBulbIcon, 
  UserIcon, 
  ChatBubbleBottomCenterTextIcon,
  ChevronLeftIcon,
  ChevronRightIcon
} from '@heroicons/react/24/outline'
import { useI18n } from '@/contexts/i18n-context'
import { useSidebar } from '@/contexts/sidebar-context'

export function DashboardSidebar() {
  const pathname = usePathname()
  const { t } = useI18n()
  const { isOpen, isCollapsed, isMobile, closeSidebar, toggleCollapse } = useSidebar()

  const navigation = [
    {
      name: t('menu.dashboard'),
      href: '/dashboard',
      icon: HomeIcon,
      current: pathname === '/dashboard'
    },
    {
      name: t('menu.profile'),
      href: '/dashboard/profile',
      icon: UserIcon,
      current: pathname === '/dashboard/profile'
    },
    {
      name: t('menu.converter'),
      href: '/dashboard/transcript-converter',
      icon: DocumentTextIcon,
      current: pathname === '/dashboard/transcript-converter'
    },
    {
      name: t('menu.analysis'),
      href: '/dashboard/analysis',
      icon: ChartBarIcon,
      current: pathname === '/dashboard/analysis',
      comingSoon: true
    },
    {
      name: t('menu.insights'),
      href: '/dashboard/insights',
      icon: LightBulbIcon,
      current: pathname === '/dashboard/insights',
      comingSoon: true
    },
    {
      name: t('menu.feedback'),
      href: '/dashboard/feedback',
      icon: ChatBubbleBottomCenterTextIcon,
      current: pathname === '/dashboard/feedback',
      comingSoon: true
    },
  ]

  return (
    <>
      {/* Mobile overlay */}
      {isMobile && isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50"
          onClick={closeSidebar}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        ${isMobile ? 'fixed' : 'static'} inset-y-0 left-0 z-50 
        ${isMobile ? (isOpen ? 'translate-x-0' : '-translate-x-full') : 'translate-x-0'}
        ${isCollapsed && !isMobile ? 'w-16' : 'w-64'}
        bg-dashboard-sidebar shadow-dark transform transition-all duration-300 ease-in-out
        flex flex-col border-r border-dashboard-accent border-opacity-20
      `}>
        {/* Sidebar header - 只在行動端顯示 */}
        {isMobile && (
          <div className="flex items-center justify-between p-4 border-b border-dashboard-accent border-opacity-20">
            <span className="text-lg font-semibold text-white">選單</span>
            <button
              onClick={closeSidebar}
              className="p-1 text-white hover:text-dashboard-accent"
            >
              ✕
            </button>
          </div>
        )}

        {/* Menu items */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon
            const isActive = item.current
            
            return (
              <div key={item.name}>
                {item.comingSoon ? (
                  <div 
                    className={`
                      flex items-center px-3 py-2 text-white rounded-lg opacity-60 cursor-not-allowed
                      ${isCollapsed && !isMobile ? 'justify-center' : ''}
                    `}
                    title={isCollapsed && !isMobile ? item.name : undefined}
                  >
                    <Icon className="h-5 w-5 text-dashboard-accent flex-shrink-0" />
                    {(!isCollapsed || isMobile) && (
                      <>
                        <span className="ml-3 font-medium flex-1">{item.name}</span>
                        <span className="text-xs bg-gray-500 text-white px-2 py-1 rounded-full ml-2">
                          {t('menu.coming_soon')}
                        </span>
                      </>
                    )}
                  </div>
                ) : (
                  <Link
                    href={item.href as any}
                    onClick={isMobile ? closeSidebar : undefined}
                    className={`
                      flex items-center px-3 py-2 rounded-lg font-medium transition-all duration-200
                      group relative
                      ${isCollapsed && !isMobile ? 'justify-center' : ''}
                      ${isActive 
                        ? 'bg-dashboard-accent bg-opacity-10 text-dashboard-accent' 
                        : 'text-white hover:bg-dashboard-accent hover:bg-opacity-10 hover:text-dashboard-accent'
                      }
                    `}
                    title={isCollapsed && !isMobile ? item.name : undefined}
                  >
                    <Icon className="h-5 w-5 flex-shrink-0" />
                    {(!isCollapsed || isMobile) && (
                      <span className="ml-3">{item.name}</span>
                    )}
                    
                    {/* Active indicator for collapsed state */}
                    {isActive && isCollapsed && !isMobile && (
                      <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-dashboard-accent rounded-r-full" />
                    )}
                    
                    {/* Tooltip for collapsed state */}
                    {isCollapsed && !isMobile && (
                      <div className="absolute left-full ml-2 px-2 py-1 bg-gray-900 text-white text-sm rounded opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none whitespace-nowrap z-50">
                        {item.name}
                        {item.comingSoon && (
                          <span className="ml-2 text-xs bg-gray-600 px-1 rounded">
                            {t('menu.coming_soon')}
                          </span>
                        )}
                      </div>
                    )}
                  </Link>
                )}
              </div>
            )
          })}
        </nav>

        {/* Sidebar footer */}
        {(!isCollapsed || isMobile) && (
          <div className="p-4 border-t border-dashboard-accent border-opacity-20">
            <div className="text-xs text-white text-center">
              <div>Coachly v2.0</div>
              <div className="mt-1">© 2025 Doxa Studio</div>
            </div>
          </div>
        )}
      </aside>
    </>
  )
}
