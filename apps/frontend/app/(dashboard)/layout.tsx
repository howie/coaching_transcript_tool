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
    <div className="min-h-screen bg-white">
      {/* Header */}
      <header className="bg-white shadow-custom border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-black">
                Coaching Transcript Tool
              </h1>
            </div>
            <div className="flex items-center space-x-6">
              {/* 這裡將來會放置用戶選單 */}
              <button className="text-gray-800 hover:text-gold font-medium transition-colors">
                設定
              </button>
              <button className="text-gray-800 hover:text-gold font-medium transition-colors">
                登出
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar and Content */}
      <div className="flex">
        {/* Sidebar */}
        <nav className="w-64 bg-white shadow-custom min-h-screen">
          <div className="p-6">
            <ul className="space-y-3">
              <li>
                <Link
                  href="/dashboard"
                  className="flex items-center px-6 py-3 text-black rounded-lg hover:bg-gray-100 font-medium transition-all duration-300"
                >
                  <span className="text-gold mr-3">📊</span>
                  <span>儀表板</span>
                </Link>
              </li>
              <li>
                <Link
                  href="/transcript-converter"
                  className="flex items-center px-6 py-3 text-black rounded-lg hover:bg-gray-100 font-medium transition-all duration-300"
                >
                  <span className="text-gold mr-3">📝</span>
                  <span>逐字稿轉換</span>
                </Link>
              </li>
            </ul>
          </div>
        </nav>

        {/* Main Content */}
        <main className="flex-1 p-8 bg-gray-100">
          {children}
        </main>
      </div>
    </div>
  )
}
