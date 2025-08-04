'use client'

import { useState } from 'react'
import { 
  UserCircleIcon, 
  LockClosedIcon, 
  StarIcon,
  CameraIcon,
  GlobeAltIcon,
  ChatBubbleLeftRightIcon,
  CreditCardIcon,
  AcademicCapIcon,
  BriefcaseIcon,
  KeyIcon
} from '@heroicons/react/24/outline'
import { useI18n } from '@/contexts/i18n-context'

export default function ProfilePage() {
  const { t } = useI18n()
  const [formData, setFormData] = useState({
    // 基本資料
    name: '',
    email: '',
    phone: '',
    countryCode: '+886',
    country: '',
    city: '',
    timezone: '',
    
    // 語言設定
    coachingLanguage: 'zh',
    notificationLanguage: 'zh',
    
    // 溝通工具
    lineId: '',
    hasZoom: false,
    hasGoogleMeet: true,
    hasMSTeams: false,
    
    // 密碼變更
    newPassword: '',
    confirmPassword: '',
    
    // 專業資訊
    experience: '',
    institution: '',
    certification: '',
    linkedIn: '',
    website: '',
    
    // 教練方案
    sessionTitle: '',
    sessionDuration: 60,
    sessionPrice: 0,
    
    // 套裝方案
    packageSessions: 4,
    packageDuration: 60,
    packagePrice: 0
  })

  const countryCodes = [
    { code: '+886', name: '🇹🇼 台灣' },
    { code: '+1', name: '🇺🇸 美國' },
    { code: '+44', name: '🇬🇧 英國' },
    { code: '+86', name: '🇨🇳 中國' },
    { code: '+81', name: '🇯🇵 日本' },
    { code: '+82', name: '🇰🇷 韓國' }
  ]

  const experienceOptions = [
    { value: 'beginner', label: '新手教練 (0-1年)' },
    { value: 'intermediate', label: '中級教練 (1-3年)' },
    { value: 'advanced', label: '資深教練 (3-5年)' },
    { value: 'expert', label: '專家教練 (5年以上)' }
  ]

  const timezones = [
    { value: 'Asia/Taipei', label: '台北 (GMT+8)' },
    { value: 'Asia/Tokyo', label: '東京 (GMT+9)' },
    { value: 'Asia/Shanghai', label: '上海 (GMT+8)' },
    { value: 'America/New_York', label: '紐約 (GMT-5)' },
    { value: 'America/Los_Angeles', label: '洛杉磯 (GMT-8)' },
    { value: 'Europe/London', label: '倫敦 (GMT+0)' }
  ]

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }))
  }

  return (
    <div className="min-h-screen bg-dashboard-bg text-white">
      <div className="max-w-4xl mx-auto px-4 py-6">
        {/* 付費解鎖提示 */}
        <div className="mb-6 bg-gradient-to-r from-purple-600 via-pink-600 to-blue-600 rounded-lg p-6 shadow-lg">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-white bg-opacity-20 rounded-full flex items-center justify-center">
                  <StarIcon className="h-6 w-6 text-white" />
                </div>
              </div>
              <div>
                <h3 className="text-xl font-bold text-white">
                  升級至 Pro 版本解鎖完整功能
                </h3>
                <p className="text-white text-opacity-90 mt-1">
                  個人設定功能讓您完整管理教練檔案、設定收費方案、連結付款帳戶等專業功能
                </p>
              </div>
            </div>
            <div className="flex-shrink-0">
              <button className="bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors shadow-lg">
                立即升級
              </button>
            </div>
          </div>
        </div>

        {/* 開發中標籤 */}
        <div className="mb-6 bg-orange-500 bg-opacity-20 border border-orange-500 border-opacity-50 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🚧</span>
            <div>
              <h4 className="font-semibold text-orange-300">功能開發中</h4>
              <p className="text-sm text-orange-200 opacity-90">此頁面為設計預覽，實際功能將在後續版本中實作</p>
            </div>
          </div>
        </div>

        {/* 頁面標題 */}
        <div className="flex items-center space-x-3 mb-8">
          <UserCircleIcon className="h-8 w-8 text-dashboard-accent" />
          <h1 className="text-3xl font-bold text-white">{t('menu.profile')}</h1>
        </div>

        <div className="space-y-8">
          {/* 基本資料區塊 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <UserCircleIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold">基本資料</h2>
            </div>
            
            {/* 大頭照 */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-300 mb-2">個人照片</label>
              <div className="flex items-center space-x-4">
                <div className="w-20 h-20 bg-gray-600 rounded-full flex items-center justify-center">
                  <UserCircleIcon className="h-12 w-12 text-gray-400" />
                </div>
                <button className="flex items-center space-x-2 px-4 py-2 bg-dashboard-accent bg-opacity-10 text-dashboard-accent rounded-lg hover:bg-opacity-20 transition-colors">
                  <CameraIcon className="h-4 w-4" />
                  <span>更換照片</span>
                </button>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">姓名</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => handleInputChange('name', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="請輸入您的姓名"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="example@email.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">電話號碼</label>
                <div className="flex space-x-2">
                  <select
                    value={formData.countryCode}
                    onChange={(e) => handleInputChange('countryCode', e.target.value)}
                    className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  >
                    {countryCodes.map(country => (
                      <option key={country.code} value={country.code}>
                        {country.name}
                      </option>
                    ))}
                  </select>
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={(e) => handleInputChange('phone', e.target.value)}
                    className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    placeholder="請輸入電話號碼"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">國家</label>
                <input
                  type="text"
                  value={formData.country}
                  onChange={(e) => handleInputChange('country', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="台灣"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">城市</label>
                <input
                  type="text"
                  value={formData.city}
                  onChange={(e) => handleInputChange('city', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="台北"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">時區</label>
                <select
                  value={formData.timezone}
                  onChange={(e) => handleInputChange('timezone', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                >
                  <option value="">請選擇時區</option>
                  {timezones.map(tz => (
                    <option key={tz.value} value={tz.value}>
                      {tz.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          {/* 語言設定 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <GlobeAltIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold">語言設定</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">教練語言</label>
                <select
                  value={formData.coachingLanguage}
                  onChange={(e) => handleInputChange('coachingLanguage', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                >
                  <option value="zh">繁體中文</option>
                  <option value="en">English</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">通知語言</label>
                <select
                  value={formData.notificationLanguage}
                  onChange={(e) => handleInputChange('notificationLanguage', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                >
                  <option value="zh">繁體中文</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>
          </div>

          {/* 溝通工具設定 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <ChatBubbleLeftRightIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold">溝通工具</h2>
            </div>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">Line ID</label>
                <input
                  type="text"
                  value={formData.lineId}
                  onChange={(e) => handleInputChange('lineId', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="請輸入 Line ID"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <span className="text-sm font-medium">Zoom</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.hasZoom}
                      onChange={(e) => handleInputChange('hasZoom', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dashboard-accent dark:peer-focus:ring-dashboard-accent rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-dashboard-accent"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <span className="text-sm font-medium">Google Meet</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.hasGoogleMeet}
                      onChange={(e) => handleInputChange('hasGoogleMeet', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dashboard-accent dark:peer-focus:ring-dashboard-accent rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-dashboard-accent"></div>
                  </label>
                </div>

                <div className="flex items-center justify-between p-3 bg-gray-700 rounded-lg">
                  <span className="text-sm font-medium">MS Teams</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={formData.hasMSTeams}
                      onChange={(e) => handleInputChange('hasMSTeams', e.target.checked)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dashboard-accent dark:peer-focus:ring-dashboard-accent rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-dashboard-accent"></div>
                  </label>
                </div>
              </div>
            </div>
          </div>

          {/* 密碼變更 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <KeyIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold">密碼變更</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">新密碼</label>
                <input
                  type="password"
                  value={formData.newPassword}
                  onChange={(e) => handleInputChange('newPassword', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="請輸入新密碼"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">確認密碼</label>
                <input
                  type="password"
                  value={formData.confirmPassword}
                  onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="請再次輸入新密碼"
                />
              </div>
            </div>
          </div>

          {/* 付款設定 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <CreditCardIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold">付款設定</h2>
            </div>
            
            <div className="flex items-center justify-between p-4 bg-gray-700 rounded-lg">
              <div>
                <h3 className="font-medium">Stripe Connect</h3>
                <p className="text-sm text-gray-400 mt-1">連結您的 Stripe 帳戶以接收付款</p>
              </div>
              <button className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
                連結帳戶
              </button>
            </div>
          </div>

          {/* 專業資訊 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <AcademicCapIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold">專業資訊</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">教練經驗</label>
                <select
                  value={formData.experience}
                  onChange={(e) => handleInputChange('experience', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                >
                  <option value="">請選擇經驗程度</option>
                  {experienceOptions.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">培訓機構</label>
                <input
                  type="text"
                  value={formData.institution}
                  onChange={(e) => handleInputChange('institution', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="例如：ICF、CTI"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">認證</label>
                <input
                  type="text"
                  value={formData.certification}
                  onChange={(e) => handleInputChange('certification', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="例如：ACC、PCC、MCC"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">LinkedIn</label>
                <input
                  type="url"
                  value={formData.linkedIn}
                  onChange={(e) => handleInputChange('linkedIn', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="https://linkedin.com/in/yourname"
                />
              </div>

              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-300 mb-2">個人網站</label>
                <input
                  type="url"
                  value={formData.website}
                  onChange={(e) => handleInputChange('website', e.target.value)}
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                  placeholder="https://yourwebsite.com"
                />
              </div>
            </div>
          </div>

          {/* 教練方案設定 */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <BriefcaseIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold">教練方案設定</h2>
            </div>
            
            {/* 單次教練 */}
            <div className="mb-8">
              <h3 className="text-lg font-medium mb-4">單次教練</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">標題</label>
                  <input
                    type="text"
                    value={formData.sessionTitle}
                    onChange={(e) => handleInputChange('sessionTitle', e.target.value)}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    placeholder="一對一教練諮詢"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">時長 (分鐘)</label>
                  <input
                    type="number"
                    value={formData.sessionDuration}
                    onChange={(e) => handleInputChange('sessionDuration', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="30"
                    max="180"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">價格 (NT$)</label>
                  <input
                    type="number"
                    value={formData.sessionPrice}
                    onChange={(e) => handleInputChange('sessionPrice', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="0"
                  />
                </div>
              </div>
            </div>

            {/* 套裝方案 */}
            <div>
              <h3 className="text-lg font-medium mb-4">套裝方案</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">次數</label>
                  <input
                    type="number"
                    value={formData.packageSessions}
                    onChange={(e) => handleInputChange('packageSessions', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="2"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">每次時長 (分鐘)</label>
                  <input
                    type="number"
                    value={formData.packageDuration}
                    onChange={(e) => handleInputChange('packageDuration', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="30"
                    max="180"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">總價格 (NT$)</label>
                  <input
                    type="number"
                    value={formData.packagePrice}
                    onChange={(e) => handleInputChange('packagePrice', parseInt(e.target.value))}
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-dashboard-accent focus:border-transparent"
                    min="0"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* 儲存按鈕 */}
          <div className="flex justify-end space-x-4">
            <button className="px-6 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors">
              重設
            </button>
            <button className="px-6 py-2 bg-dashboard-accent text-white rounded-lg hover:bg-opacity-90 transition-colors">
              儲存變更
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
