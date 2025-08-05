'use client'

import Image from 'next/image'
import Link from 'next/link'
import { useState } from 'react'
import { I18nProvider, useI18n } from '@/contexts/i18n-context'

function HomePageContent() {
  const { language, setLanguage, t } = useI18n()
  const [showLanguageMenu, setShowLanguageMenu] = useState(false)

  const handleLanguageChange = (newLanguage: 'zh' | 'en') => {
    setLanguage(newLanguage)
    setShowLanguageMenu(false)
  }
  return (
    <>
      {/* Navigation Header */}
      <nav className="fixed top-0 w-full z-50 bg-nav-dark shadow-lg">
        <div className="max-w-6xl mx-auto px-5">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-10">
              <Link href="/" className="flex items-center gap-2 text-white text-xl font-semibold hover:text-primary-blue transition-colors">
                <Image 
                  src="/images/Coachly-logo-transparent-300px.png" 
                  alt="Coachly Logo" 
                  width={32} 
                  height={32}
                  className="w-8 h-auto"
                />
                Coachly
              </Link>
              <div className="hidden md:flex items-center gap-8">
                <a href="#who-its-for" className="text-white hover:text-primary-blue transition-colors text-sm">{t('nav.who_its_for')}</a>
                <a href="#features" className="text-white hover:text-primary-blue transition-colors text-sm">{t('nav.features')}</a>
                <a href="#pricing" className="text-white hover:text-primary-blue transition-colors text-sm">{t('nav.pricing')}</a>
                <a href="#" className="text-white hover:text-primary-blue transition-colors text-sm">{t('nav.blog')}</a>
                <a href="#" className="text-white hover:text-primary-blue transition-colors text-sm">{t('nav.contact')}</a>
              </div>
            </div>
            <div className="flex items-center gap-5">
              <Link href={'/login' as any} className="bg-accent-orange hover:bg-accent-orange-hover text-white px-4 py-2 rounded-md text-sm font-medium transition-all hover:-translate-y-0.5">
                {t('nav.login')}
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Language Switcher */}
      <div className="fixed top-20 right-5 z-40">
        <div className="relative">
          <button
            onClick={() => setShowLanguageMenu(!showLanguageMenu)}
            className="bg-nav-dark/90 backdrop-blur-sm text-white border-none rounded-md px-3 py-2 text-sm cursor-pointer hover:bg-primary-blue hover:text-nav-dark transition-colors min-w-[140px] flex items-center justify-between"
          >
            <span>{language === 'zh' ? '🇹🇼 繁體中文' : '🇺🇸 English'}</span>
            <svg className="w-4 h-4 ml-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </button>
          
          {showLanguageMenu && (
            <div className="absolute top-full mt-1 w-full bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 py-1">
              <button
                onClick={() => handleLanguageChange('zh')}
                className="block w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                🇹🇼 繁體中文
              </button>
              <button
                onClick={() => handleLanguageChange('en')}
                className="block w-full text-left px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
              >
                🇺🇸 English
              </button>
            </div>
          )}
        </div>
      </div>
      
      {/* Click outside to close language menu */}
      {showLanguageMenu && (
        <div
          className="fixed inset-0 z-30"
          onClick={() => setShowLanguageMenu(false)}
        />
      )}

      <main>
        {/* Hero Section */}
        <section className="bg-primary-blue text-white pt-20 pb-20 mt-16 min-h-[500px] flex items-center">
          <div className="max-w-6xl mx-auto px-5">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
              <div className="text-left">
                <h1 className="text-5xl font-bold mb-6 leading-tight">{t('landing.slogan')}</h1>
                <p className="text-xl mb-10 text-white/80 leading-relaxed">{t('landing.subtitle')}</p>
                <div className="flex gap-5 flex-wrap">
                  <Link 
                    href="/dashboard" 
                    className="bg-white text-nav-dark border-2 border-white px-8 py-4 text-base font-semibold rounded-lg hover:-translate-y-1 transition-all inline-block"
                  >
                    {t('landing.get_started')}
                  </Link>
                  <a 
                    href="mailto:service@doxa.com.tw" 
                    className="bg-transparent text-white border-2 border-white px-8 py-4 text-base font-semibold rounded-lg hover:-translate-y-1 transition-all inline-block"
                  >
                    {t('landing.contact_sales')}
                  </a>
                </div>
              </div>
              <div className="flex justify-center items-center">
                <div className="hero-logo">
                  <Image 
                    src="/images/Coachly-logo-transparent-600px.png" 
                    alt="Coachly Logo" 
                    width={400} 
                    height={400}
                    className="w-full max-w-[400px] h-auto"
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Who it's for Section */}
        <section id="who-its-for" className="py-20 bg-section-light text-center">
          <h2 className="text-4xl font-bold mb-12">{t('landing.who_its_for')}</h2>
          <div className="max-w-6xl mx-auto px-5">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
              <div className="bg-white p-8 rounded-lg shadow-custom text-left">
                <div className="text-4xl text-primary-blue mb-5">
                  <i className="fas fa-user-graduate"></i>
                </div>
                <h3 className="text-xl font-semibold mb-4">{t('landing.learner.title')}</h3>
                <p className="text-gray-600">{t('landing.learner.desc')}</p>
              </div>
              <div className="bg-white p-8 rounded-lg shadow-custom text-left">
                <div className="text-4xl text-primary-blue mb-5">
                  <i className="fas fa-user-tie"></i>
                </div>
                <h3 className="text-xl font-semibold mb-4">{t('landing.professional.title')}</h3>
                <p className="text-gray-600">{t('landing.professional.desc')}</p>
              </div>
              <div className="bg-white p-8 rounded-lg shadow-custom text-left">
                <div className="text-4xl text-primary-blue mb-5">
                  <i className="fas fa-chalkboard-teacher"></i>
                </div>
                <h3 className="text-xl font-semibold mb-4">{t('landing.supervisor.title')}</h3>
                <p className="text-gray-600">{t('landing.supervisor.desc')}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Features Section */}
        <section id="features" className="py-20 bg-primary-blue text-white text-center">
          <h2 className="text-4xl font-bold mb-12">{t('landing.features')}</h2>
          <div className="max-w-6xl mx-auto px-5">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
              <div className="bg-nav-dark p-8 rounded-lg text-left">
                <div className="text-4xl text-primary-blue mb-5">
                  <i className="fas fa-file-excel"></i>
                </div>
                <h3 className="text-xl font-semibold mb-4">{t('landing.transcript.title')}</h3>
                <p className="text-white/80">{t('landing.transcript.desc')}</p>
              </div>
              <div className="bg-nav-dark p-8 rounded-lg text-left">
                <div className="text-4xl text-primary-blue mb-5">
                  <i className="fas fa-compass"></i>
                </div>
                <h3 className="text-xl font-semibold mb-4">{t('landing.analysis.title')}</h3>
                <p className="text-white/80">{t('landing.analysis.desc')}</p>
              </div>
              <div className="bg-nav-dark p-8 rounded-lg text-left">
                <div className="text-4xl text-primary-blue mb-5">
                  <i className="fas fa-lightbulb"></i>
                </div>
                <h3 className="text-xl font-semibold mb-4">{t('landing.insights.title')}</h3>
                <p className="text-white/80">{t('landing.insights.desc')}</p>
              </div>
            </div>
          </div>
        </section>

        {/* Pricing Section */}
        <section id="pricing" className="py-20 bg-section-light text-center">
          <h2 className="text-4xl font-bold mb-12">{t('landing.pricing')}</h2>
          <div className="max-w-4xl mx-auto px-5">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div className="bg-white p-8 rounded-lg shadow-custom border-2 border-nav-dark flex flex-col">
                <h3 className="text-2xl font-semibold mb-5">{t('landing.pricing.free')}</h3>
                <p className="text-5xl font-bold mb-5">$0</p>
                
                <Link 
                  href="/dashboard" 
                  className="bg-nav-dark text-white border-2 border-nav-dark px-8 py-4 rounded-lg text-center font-semibold hover:-translate-y-1 transition-all mb-5 inline-block"
                >
                  {t('landing.get_started')}
                </Link>
                
                <div className="border-t pt-5 mt-2">
                  <ul className="text-left space-y-2">
                    <li>• {t('landing.pricing.free.feature1')}</li>
                    <li>• {t('landing.pricing.free.feature2')}</li>
                  </ul>
                </div>
              </div>
              
              <div className="bg-white p-8 rounded-lg shadow-custom border-2 border-primary-blue flex flex-col">
                <h3 className="text-2xl font-semibold mb-5">{t('landing.pricing.pro')}</h3>
                <p className="text-3xl font-bold mb-5">Custom Pricing</p>
                
                <a 
                  href="mailto:service@doxa.com.tw" 
                  className="bg-primary-blue text-white border-2 border-primary-blue px-8 py-4 rounded-lg text-center font-semibold hover:-translate-y-1 hover:shadow-lg hover:shadow-primary-blue/50 transition-all mb-5 inline-block"
                >
                  {t('landing.pro.contact_sales')}
                </a>
                
                <div className="border-t pt-5 mt-2">
                  <ul className="text-left space-y-2">
                    <li>• {t('landing.pricing.pro.feature1')}</li>
                    <li>• {t('landing.pricing.pro.feature2')}</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Coming Soon Section */}
        <section id="coming-soon" className="py-20 bg-primary-blue text-white text-center">
          <h2 className="text-4xl font-bold mb-8">{t('landing.coming_soon')}</h2>
          <p className="max-w-2xl mx-auto text-lg leading-relaxed">{t('landing.coming_soon.desc')}</p>
        </section>
      </main>

      {/* Footer */}
      <footer className="bg-nav-dark text-white py-16">
        <div className="max-w-6xl mx-auto px-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-10 mb-10">
            <div>
              <h3 className="text-primary-blue mb-4">build by Doxa Studio</h3>
            </div>
            <div>
              <h4 className="text-primary-blue mb-4">Contact</h4>
              <p className="text-gray-300">Email: service@doxa.com.tw</p>
            </div>
            <div>
              <h4 className="text-primary-blue mb-4">Follow Us</h4>
              <div className="flex gap-4">
                <a href="#" className="text-gray-300 hover:text-primary-blue transition-colors text-xl">
                  <i className="fab fa-linkedin"></i>
                </a>
                <a href="#" className="text-gray-300 hover:text-primary-blue transition-colors text-xl">
                  <i className="fab fa-twitter"></i>
                </a>
                <a href="#" className="text-gray-300 hover:text-primary-blue transition-colors text-xl">
                  <i className="fab fa-instagram"></i>
                </a>
              </div>
            </div>
          </div>
          <div className="text-center pt-5 border-t border-gray-600">
            <p className="text-gray-300">&copy; 2025 Doxa Studio. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </>
  )
}

export default function HomePage() {
  return (
    <I18nProvider>
      <HomePageContent />
    </I18nProvider>
  )
}
