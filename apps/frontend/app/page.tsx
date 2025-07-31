import Link from 'next/link'

export default function HomePage() {
  return (
    <>
      {/* Navigation */}
      <nav className="fixed top-0 w-full z-50 bg-nav-dark shadow-lg">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-10">
              <h1 className="text-xl font-semibold text-white">
                Coachly
              </h1>
              <div className="hidden md:flex items-center gap-8">
                <a href="#features" className="text-white hover:text-primary-blue transition-colors">功能</a>
                <a href="#pricing" className="text-white hover:text-primary-blue transition-colors">價格</a>
                <a href="#about" className="text-white hover:text-primary-blue transition-colors">關於我們</a>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <Link
                href="/dashboard"
                className="px-4 py-2 bg-accent-orange text-white rounded-md hover:bg-accent-orange-hover transform hover:-translate-y-0.5 transition-all duration-300 font-medium"
              >
                開始使用
              </Link>
            </div>
          </div>
        </div>
      </nav>

      <main className="min-h-screen">
        {/* Hero Section */}
        <section className="bg-primary-blue text-white pt-24 pb-20 min-h-[500px] flex items-center">
          <div className="max-w-6xl mx-auto px-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-15 items-center">
              {/* Hero Content */}
              <div className="text-center lg:text-left">
                <h1 className="text-5xl lg:text-6xl font-bold mb-6 leading-tight">
                  AI-Powered Coaching
                </h1>
                <p className="text-xl mb-10 opacity-80 leading-relaxed">
                  從新手教練到執業認證，Coachly 幫你記錄、成長與實踐。
                </p>
                
                <div className="flex flex-col sm:flex-row gap-5 justify-center lg:justify-start">
                  <Link
                    href="/dashboard"
                    className="inline-flex items-center justify-center px-8 py-4 bg-white text-nav-dark rounded-lg font-semibold hover:bg-gray-100 transform hover:-translate-y-1 transition-all duration-300 shadow-lg"
                  >
                    Get Started for Free
                  </Link>
                  <a
                    href="mailto:service@doxa.com.tw"
                    className="inline-flex items-center justify-center px-8 py-4 border-2 border-white text-white rounded-lg font-semibold hover:bg-white hover:text-primary-blue transition-all duration-300"
                  >
                    contact sales
                  </a>
                </div>
              </div>

              {/* Hero Image */}
              <div className="flex justify-center">
                <div className="w-96 h-96 flex items-center justify-center">
                  <div className="text-9xl opacity-80">🤖</div>
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
              <div className="text-5xl text-primary-blue mb-6">🎯</div>
              <h3 className="text-2xl font-semibold text-black mb-4">
                智能處理
              </h3>
              <p className="text-gray-800">
                自動解析 VTT 逐字稿，智能識別說話者並進行內容整理
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-custom text-center hover:transform hover:-translate-y-2 transition-all duration-300">
              <div className="text-5xl text-primary-blue mb-6">📊</div>
              <h3 className="text-2xl font-semibold text-black mb-4">
                多格式輸出
              </h3>
              <p className="text-gray-800">
                支援 Markdown 和 Excel 格式輸出，滿足不同使用場景需求
              </p>
            </div>

            <div className="bg-white p-8 rounded-lg shadow-custom text-center hover:transform hover:-translate-y-2 transition-all duration-300">
              <div className="text-5xl text-primary-blue mb-6">🔒</div>
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
            className="inline-flex items-center justify-center px-12 py-4 bg-primary-blue text-white rounded-lg font-medium hover:bg-accent-orange transform hover:-translate-y-1 transition-all duration-300 text-lg"
          >
            立即開始
          </Link>
        </div>
      </section>
    </main>
    </>
  )
}
