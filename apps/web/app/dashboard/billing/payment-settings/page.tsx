'use client'

import { useState } from 'react'
import { 
  CreditCardIcon, 
  CalendarIcon, 
  DocumentTextIcon,
  BellIcon,
  ArrowLeftIcon,
  CheckIcon,
  XMarkIcon
} from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useAuth } from '@/contexts/auth-context'

export default function PaymentSettingsPage() {
  const { user } = useAuth()
  const [billingCycle, setBillingCycle] = useState('monthly')
  const [autoRenew, setAutoRenew] = useState(true)
  const [emailNotifications, setEmailNotifications] = useState({
    paymentSuccess: true,
    paymentFailed: true,
    planChanges: true,
    usageAlerts: false,
    invoices: true
  })

  const handleNotificationChange = (key: keyof typeof emailNotifications) => {
    setEmailNotifications(prev => ({
      ...prev,
      [key]: !prev[key]
    }))
  }

  const handleSaveSettings = () => {
    // TODO: Implement save settings
    console.log('Saving billing settings', { billingCycle, autoRenew, emailNotifications })
  }

  return (
    <div className="min-h-screen py-12" style={{backgroundColor: 'var(--bg-primary)'}}>
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/billing" className="inline-flex items-center text-dashboard-accent hover:text-dashboard-accent-hover mb-4">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            返回 Billing
          </Link>
          <div className="flex items-center space-x-3">
            <CreditCardIcon className="h-8 w-8 text-dashboard-accent" />
            <h1 className="text-3xl font-bold" style={{color: 'var(--text-primary)'}}>Payment Settings</h1>
          </div>
        </div>

        {/* 開發中標籤 */}
        <div className="mb-6 bg-orange-500 bg-opacity-20 border border-orange-500 border-opacity-50 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🚧</span>
            <div>
              <h4 className="font-semibold text-orange-300">功能施工中</h4>
              <p className="text-sm text-orange-200 opacity-90">Billing 設定功能仍在開發中，目前僅供預覽</p>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          {/* Payment Method */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <CreditCardIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>付款方式</h2>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 rounded-lg flex items-center justify-between" style={{backgroundColor: 'var(--card-bg)'}}>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-400 rounded flex items-center justify-center">
                    <span className="text-white text-xs font-bold">VISA</span>
                  </div>
                  <div>
                    <p className="font-medium" style={{color: 'var(--text-primary)'}}>•••• •••• •••• 4242</p>
                    <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>到期日: 12/2025</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-600 bg-opacity-20 text-green-400 rounded-full text-sm font-medium">
                  預設
                </span>
              </div>

              <button className="w-full px-4 py-3 border border-dashed rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed" style={{borderColor: 'var(--input-border)', color: 'var(--text-tertiary)'}} disabled>
                + 新增付款方式（功能開發中）
              </button>
            </div>
          </div>

          {/* Billing Cycle */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <CalendarIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>計費週期</h2>
            </div>
            
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <button
                  onClick={() => setBillingCycle('monthly')}
                  className={`p-4 rounded-lg border transition-colors ${
                    billingCycle === 'monthly'
                      ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10'
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <h3 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>月繳</h3>
                  <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>每月自動扣款</p>
                </button>

                <button
                  onClick={() => setBillingCycle('annual')}
                  className={`p-4 rounded-lg border transition-colors ${
                    billingCycle === 'annual'
                      ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10'
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <h3 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>年繳</h3>
                  <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>每年扣款，享 31% 折扣</p>
                </button>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                <div>
                  <h3 className="font-medium" style={{color: 'var(--text-primary)'}}>自動續約</h3>
                  <p className="text-sm mt-1" style={{color: 'var(--text-tertiary)'}}>到期時自動續約您的方案</p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={autoRenew}
                    onChange={(e) => setAutoRenew(e.target.checked)}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dashboard-accent rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-dashboard-accent"></div>
                </label>
              </div>
            </div>
          </div>

          {/* Billing Information */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <DocumentTextIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>帳單資訊</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">公司名稱</label>
                <input
                  type="text"
                  className="input-base"
                  placeholder="選填"
                  disabled
                />
              </div>

              <div>
                <label className="label">統一編號</label>
                <input
                  type="text"
                  className="input-base"
                  placeholder="選填"
                  disabled
                />
              </div>

              <div className="md:col-span-2">
                <label className="label">帳單地址</label>
                <input
                  type="text"
                  className="input-base"
                  placeholder="請輸入帳單地址"
                  disabled
                />
              </div>
            </div>
          </div>

          {/* Email Notifications */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <BellIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>Email 通知設定</h2>
            </div>
            
            <div className="space-y-4">
              {Object.entries({
                paymentSuccess: '付款成功通知',
                paymentFailed: '付款失敗通知',
                planChanges: '方案變更通知',
                usageAlerts: '用量警示通知（達到 80% 時）',
                invoices: '發票和收據'
              }).map(([key, label]) => (
                <div key={key} className="flex items-center justify-between p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                  <span style={{color: 'var(--text-secondary)'}}>{label}</span>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={emailNotifications[key as keyof typeof emailNotifications]}
                      onChange={() => handleNotificationChange(key as keyof typeof emailNotifications)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-600 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-dashboard-accent rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-dashboard-accent"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Invoice History */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <DocumentTextIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>發票紀錄</h2>
            </div>
            
            <div className="space-y-3">
              {[
                { date: '2025-01-01', amount: 25, status: 'paid' },
                { date: '2024-12-01', amount: 25, status: 'paid' },
                { date: '2024-11-01', amount: 25, status: 'paid' }
              ].map((invoice, index) => (
                <div key={index} className="flex items-center justify-between p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                  <div>
                    <p className="font-medium" style={{color: 'var(--text-primary)'}}>{invoice.date}</p>
                    <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>Pro 方案 - 月費</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="font-medium" style={{color: 'var(--text-primary)'}}>${invoice.amount}</p>
                      <p className="text-sm text-green-400 flex items-center">
                        <CheckIcon className="h-3 w-3 mr-1" />
                        已付款
                      </p>
                    </div>
                    <button className="text-dashboard-accent hover:text-dashboard-accent-hover disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                      下載
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Save Button */}
          <div className="flex justify-end">
            <button
              onClick={handleSaveSettings}
              className="px-6 py-3 bg-dashboard-accent text-white rounded-lg hover:bg-opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled
            >
              儲存設定（功能開發中）
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}