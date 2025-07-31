export default function DashboardPage() {
  return (
    <div className="space-y-6">
      {/* 頁面標題 */}
      <div>
        <h1 className="text-3xl font-bold text-dashboard-accent mb-2">儀表板</h1>
        <p className="text-dashboard-text-tertiary">管理您的逐字稿處理任務</p>
      </div>

      {/* 統計卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-dashboard-card-bg p-6 rounded-lg shadow-dark border border-dashboard-accent border-opacity-10">
          <div className="flex items-center">
            <div className="p-2 bg-dashboard-accent bg-opacity-20 rounded-lg">
              <svg className="w-6 h-6 text-dashboard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dashboard-text-tertiary uppercase">已處理檔案</p>
              <p className="text-3xl font-bold text-dashboard-accent">0</p>
            </div>
          </div>
        </div>

        <div className="bg-dashboard-card-bg p-6 rounded-lg shadow-dark border border-dashboard-accent border-opacity-10">
          <div className="flex items-center">
            <div className="p-2 bg-dashboard-accent bg-opacity-20 rounded-lg">
              <svg className="w-6 h-6 text-dashboard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dashboard-text-tertiary uppercase">成功轉換</p>
              <p className="text-3xl font-bold text-dashboard-accent">0</p>
            </div>
          </div>
        </div>

        <div className="bg-dashboard-card-bg p-6 rounded-lg shadow-dark border border-dashboard-accent border-opacity-10">
          <div className="flex items-center">
            <div className="p-2 bg-dashboard-accent bg-opacity-20 rounded-lg">
              <svg className="w-6 h-6 text-dashboard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dashboard-text-tertiary uppercase">處理中</p>
              <p className="text-3xl font-bold text-dashboard-accent">0</p>
            </div>
          </div>
        </div>

        <div className="bg-dashboard-card-bg p-6 rounded-lg shadow-dark border border-dashboard-accent border-opacity-10">
          <div className="flex items-center">
            <div className="p-2 bg-dashboard-accent bg-opacity-20 rounded-lg">
              <svg className="w-6 h-6 text-dashboard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-dashboard-text-tertiary uppercase">處理失敗</p>
              <p className="text-3xl font-bold text-dashboard-accent">0</p>
            </div>
          </div>
        </div>
      </div>

      {/* 快速操作 */}
      <div className="bg-dashboard-card-bg p-6 rounded-lg shadow-dark border border-dashboard-accent border-opacity-10">
        <h2 className="text-xl font-semibold text-dashboard-accent mb-6">快速操作</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <a
            href="/transcript-converter"
            className="flex items-center p-6 border border-dashboard-accent border-opacity-30 rounded-lg hover:bg-dashboard-accent hover:bg-opacity-10 hover:border-dashboard-accent transition-all duration-300"
          >
            <div className="p-3 bg-dashboard-accent bg-opacity-20 rounded-lg mr-4">
              <svg className="w-6 h-6 text-dashboard-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-dashboard-text">上傳新檔案</h3>
              <p className="text-sm text-dashboard-text-secondary">將 VTT 檔案轉換為 Markdown 或 Excel</p>
            </div>
          </a>

          <div className="flex items-center p-6 border border-dashboard-accent border-opacity-10 rounded-lg opacity-50">
            <div className="p-3 bg-dashboard-text-secondary bg-opacity-20 rounded-lg mr-4">
              <svg className="w-6 h-6 text-dashboard-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <div>
              <h3 className="font-medium text-dashboard-text-secondary">查看統計報告</h3>
              <p className="text-sm text-dashboard-text-tertiary">即將推出</p>
            </div>
          </div>
        </div>
      </div>

      {/* 最近活動 */}
      <div className="bg-dashboard-card-bg p-6 rounded-lg shadow-dark border border-dashboard-accent border-opacity-10">
        <h2 className="text-xl font-semibold text-dashboard-accent mb-6">最近活動</h2>
        <div className="text-center py-8">
          <svg className="w-12 h-12 text-dashboard-text-secondary mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <p className="text-dashboard-text-secondary">尚無處理記錄</p>
          <p className="text-sm text-dashboard-text-tertiary mt-1">上傳您的第一個 VTT 檔案開始使用</p>
        </div>
      </div>
    </div>
  )
}
