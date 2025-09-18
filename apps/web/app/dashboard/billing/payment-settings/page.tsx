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
import { useI18n } from '@/contexts/i18n-context'

export default function PaymentSettingsPage() {
  const { user } = useAuth()
  const { t } = useI18n()
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

  const handleSaveSettings = async () => {
    try {
      const { apiClient } = await import('@/lib/api');

      const result = await apiClient.updateBillingPreferences({
        billingCycle: billingCycle as 'monthly' | 'yearly',
        autoRenew,
        emailNotifications
      });

      if (result.success !== false) {
        alert(t('billing.settingsSaved') || 'Settings saved successfully!');
      } else {
        alert('Settings saved locally. Full billing preferences will be available soon.');
      }
    } catch (error) {
      console.error('Failed to save billing settings:', error);
      alert('Failed to save settings. Please try again.');
    }
  }

  return (
    <div className="min-h-screen py-12" style={{backgroundColor: 'var(--bg-primary)'}}>
      <div className="max-w-4xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/billing" className="inline-flex items-center text-dashboard-accent hover:text-dashboard-accent-hover mb-4">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            {t('common.back')} {t('billing.title')}
          </Link>
          <div className="flex items-center space-x-3">
            <CreditCardIcon className="h-8 w-8 text-dashboard-accent" />
            <h1 className="text-3xl font-bold" style={{color: 'var(--text-primary)'}}>{t('billing.paymentSettings')}</h1>
          </div>
        </div>

        {/* 開發中標籤 */}
        <div className="mb-6 bg-orange-500 bg-opacity-20 border border-orange-500 border-opacity-50 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🚧</span>
            <div>
              <h4 className="font-semibold text-orange-300">{t('billing.featureInDevelopment')}</h4>
              <p className="text-sm text-orange-200 opacity-90">{t('billing.billingPreviewOnly')}</p>
            </div>
          </div>
        </div>

        <div className="space-y-8">
          {/* Payment Method */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <CreditCardIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('billing.paymentMethod')}</h2>
            </div>
            
            <div className="space-y-4">
              <div className="p-4 rounded-lg flex items-center justify-between" style={{backgroundColor: 'var(--card-bg)'}}>
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-400 rounded flex items-center justify-center">
                    <span className="text-white text-xs font-bold">{t('billing.visa')}</span>
                  </div>
                  <div>
                    <p className="font-medium" style={{color: 'var(--text-primary)'}}>{t('billing.cardEnding')} 4242</p>
                    <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>{t('billing.expiresOn')}: {t('billing.exampleExpiry')}</p>
                  </div>
                </div>
                <span className="px-3 py-1 bg-green-600 bg-opacity-20 text-green-400 rounded-full text-sm font-medium">
                  {t('billing.default')}
                </span>
              </div>

              <button className="w-full px-4 py-3 border border-dashed rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed" style={{borderColor: 'var(--input-border)', color: 'var(--text-tertiary)'}} disabled>
                + {t('billing.addPaymentMethod')} ({t('billing.featureInDevelopment')})
              </button>
            </div>
          </div>

          {/* Billing Cycle */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <CalendarIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('billing.billingCycle')}</h2>
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
                  <h3 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>{t('billing.monthly')}</h3>
                  <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>{t('billing.monthlyDescription')}</p>
                </button>

                <button
                  onClick={() => setBillingCycle('annual')}
                  className={`p-4 rounded-lg border transition-colors ${
                    billingCycle === 'annual'
                      ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10'
                      : 'border-gray-600 hover:border-gray-500'
                  }`}
                >
                  <h3 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>{t('billing.annual')}</h3>
                  <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>{t('billing.annualDescription')}</p>
                </button>
              </div>

              <div className="flex items-center justify-between p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
                <div>
                  <h3 className="font-medium" style={{color: 'var(--text-primary)'}}>{t('billing.autoRenew')}</h3>
                  <p className="text-sm mt-1" style={{color: 'var(--text-tertiary)'}}>{t('billing.autoRenewDescription')}</p>
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
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('billing.billingInformation')}</h2>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="label">{t('billing.companyName')}</label>
                <input
                  type="text"
                  className="input-base"
                  placeholder={t('billing.optional')}
                  disabled
                />
              </div>

              <div>
                <label className="label">{t('billing.taxId')}</label>
                <input
                  type="text"
                  className="input-base"
                  placeholder={t('billing.optional')}
                  disabled
                />
              </div>

              <div className="md:col-span-2">
                <label className="label">{t('billing.billingAddress')}</label>
                <input
                  type="text"
                  className="input-base"
                  placeholder={t('billing.enterBillingAddress')}
                  disabled
                />
              </div>
            </div>
          </div>

          {/* Email Notifications */}
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <div className="flex items-center space-x-3 mb-6">
              <BellIcon className="h-6 w-6 text-dashboard-accent" />
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('billing.emailNotifications')}</h2>
            </div>
            
            <div className="space-y-4">
              {Object.entries({
                paymentSuccess: t('billing.paymentSuccessNotification'),
                paymentFailed: t('billing.paymentFailedNotification'),
                planChanges: t('billing.planChangeNotification'),
                usageAlerts: t('billing.usageAlertNotification'),
                invoices: t('billing.invoiceNotification')
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
              <h2 className="text-xl font-semibold" style={{color: 'var(--text-primary)'}}>{t('billing.invoiceHistory')}</h2>
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
                    <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>{t('billing.proPlan')} - {t('billing.monthlyFee')}</p>
                  </div>
                  <div className="flex items-center space-x-4">
                    <div className="text-right">
                      <p className="font-medium" style={{color: 'var(--text-primary)'}}>{t('billing.currencySymbol')}{invoice.amount}</p>
                      <p className="text-sm text-green-400 flex items-center">
                        <CheckIcon className="h-3 w-3 mr-1" />
                        {t('billing.paid')}
                      </p>
                    </div>
                    <button className="text-dashboard-accent hover:text-dashboard-accent-hover disabled:opacity-50 disabled:cursor-not-allowed" disabled>
                      {t('billing.download')}
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
              {t('billing.saveSettings')} ({t('billing.featureInDevelopment')})
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}