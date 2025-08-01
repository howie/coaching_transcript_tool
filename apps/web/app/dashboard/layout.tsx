'use client'

import { SidebarProvider } from '@/contexts/sidebar-context'
import { DashboardHeader } from '@/components/layout/dashboard-header'
import { DashboardSidebar } from '@/components/layout/dashboard-sidebar'

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <SidebarProvider>
      <div className="min-h-screen bg-dashboard-bg">
        {/* Dashboard Header */}
        <DashboardHeader />

        {/* Layout with Sidebar and Content */}
        <div className="flex h-[calc(100vh-64px)]">
          {/* Dashboard Sidebar */}
          <DashboardSidebar />

          {/* Main Content */}
          <main className="flex-1 overflow-auto">
            <div className="p-6 lg:p-8">
              {children}
            </div>
          </main>
        </div>
      </div>
    </SidebarProvider>
  )
}
