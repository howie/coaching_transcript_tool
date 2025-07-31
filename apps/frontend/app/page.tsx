import Link from 'next/link'

export default function HomePage() {
  return (
    <main className="min-h-screen bg-white">
      {/* Hero Section */}
      <section className="pt-24 pb-16">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col lg:flex-row items-center gap-12">
            {/* Hero Content */}
            <div className="flex-1 text-center lg:text-left">
              <h1 className="text-5xl lg:text-6xl font-bold text-black mb-6 leading-tight">
                Coaching Transcript Tool
              </h1>
              <p className="text-xl text-gray-800 mb-8 max-w-2xl">
                專業的教練對話逐字稿處理工具，將 VTT 格式檔案轉換為結構化的 Markdown 或 Excel 文件
              </p>
              
              <div className="flex flex-col sm:flex-row gap-4 justify-center lg:justify-start">
                <Link
                  href="/dashboard"
                  className="inline-flex items-center justify-center px-8 py-4 bg-gold text-white rounded-lg font-medium hover:bg-gold-dark transform hover:-translate-y-1 transition-all duration-300 shadow-custom"
                >
                  開始使用
                </Link>
                <button className="px-8 py-4 border-2 border-black text-black rounded-lg font-medium hover:bg-black hover:text-white transition-all duration-300">
                  了解更多
                </button>
              </div>
            </div>

            {/* Hero Image */}
            <div className="flex-1 flex justify-center">
              <div className="w-80 h-80 bg-gray-100 rounded-full flex items-center justify-center">
                <div className="text-8xl text-gold">📝</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 bg-gray-100">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-black mb-16">
            專業功能特色
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="bg-white p-8 rounded-lg shadow-custom text-center hover:transform hover:-translate-y-2 transition-all duration-300">
              <div className="text-5xl text-gold mb-6">🎯</div>
              <h3 className="text-2xl font-semibold text-black mb-4">
                智能處理
              </h3>
              <p className="text-gray-800">
                自動解析 VTT 逐字稿，智能識別說話者並進行內容整理
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-custom text-center hover:transform hover:-translate-y-2 transition-all duration-300">
              <div className="text-5xl text-gold mb-6">📊</div>
              <h3 className="text-2xl font-semibold text-black mb-4">
                多格式輸出
              </h3>
              <p className="text-gray-800">
                支援 Markdown 和 Excel 格式輸出，滿足不同使用場景需求
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-custom text-center hover:transform hover:-translate-y-2 transition-all duration-300">
              <div className="text-5xl text-gold mb-6">🔒</div>
              <h3 className="text-2xl font-semibold text-black mb-4">
                隱私保護
              </h3>
              <p className="text-gray-800">
                提供說話者匿名化功能，保護對話參與者的隱私安全
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 bg-black text-white">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold mb-6">
            準備開始使用了嗎？
          </h2>
          <p className="text-xl mb-8 text-gray-300">
            立即體驗專業的逐字稿處理服務，提升您的工作效率
          </p>
          <Link
            href="/dashboard"
            className="inline-flex items-center justify-center px-12 py-4 bg-gold text-white rounded-lg font-medium hover:bg-gold-dark transform hover:-translate-y-1 transition-all duration-300 text-lg"
          >
            立即開始
          </Link>
        </div>
      </section>
    </main>
  )
}
