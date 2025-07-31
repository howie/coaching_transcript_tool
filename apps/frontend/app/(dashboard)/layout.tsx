import { Metadata } from 'next'
import Link from 'next/link'

export const metadata: Metadata = {
  title: 'Dashboard - Coaching Transcript Tool',
  description: '管理您的逐字稿處理任務',
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-dashboard-bg">
      {/* Header */}
      <header className="bg-dashboard-bg shadow-dark border-b border-dashboard-accent border-opacity-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-dashboard-text">
                Coachly
              </h1>
            </div>
            <div className="flex items-center space-x-6">
              {/* 這裡將來會放置用戶選單 */}
              <button className="text-dashboard-text-secondary hover:text-dashboard-accent font-medium transition-colors">
                設定
              </button>
              <button className="px-4 py-2 border border-dashboard-accent text-dashboard-accent hover:bg-dashboard-accent hover:text-dashboard-bg font-medium transition-colors rounded-md">
                登出
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar and Content */}
      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-dashboard-bg shadow-dark min-h-screen">
          <div className="p-6">
            <ul className="space-y-3">
              <li>
                <Link
                  href="/dashboard"
                  className="flex items-center px-6 py-3 text-dashboard-text-secondary rounded-lg hover:bg-dashboard-accent hover:bg-opacity-10 hover:text-dashboard-accent font-medium transition-all duration-300 border-l-4 border-transparent hover:border-dashboard-accent"
                >
                  <span className="text-dashboard-accent mr-3">📊</span>
                  <span>儀表板</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/transcript-converter"
                  className="flex items-center px-6 py-3 text-dashboard-text-secondary rounded-lg hover:bg-dashboard-accent hover:bg-opacity-10 hover:text-dashboard-accent font-medium transition-all duration-300 border-l-4 border-transparent hover:border-dashboard-accent"
                >
                  <span className="text-dashboard-accent mr-3">📝</span>
                  <span>逐字稿轉換</span>
                </Link>
              </li>
            </ul>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-8 bg-dashboard-bg">
          {children}
        </main>
      </div>
    </div>
  )
}
