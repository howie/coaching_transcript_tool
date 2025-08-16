'use client'

import { useState } from 'react'
import { 
  CreditCardIcon, 
  CalendarIcon, 
  DocumentTextIcon,
  BellIcon,
  CheckIcon
} from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'
import { useThemeClasses } from '@/lib/theme-utils'

export function PaymentSettings() {
  const { user } = useAuth()
  const { t } = useI18n()
  const themeClasses = useThemeClasses()
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
    <div className="space-y-8">
      {/* Payment Settings Header with Coming Soon Badge */}
      <div className="flex items-center space-x-3">
        <h2 className={`text-xl font-semibold ${themeClasses.textPrimary}`}>
          {t('billing.paymentSettings')}
        </h2>
        <span className="px-2 py-1 bg-dashboard-accent bg-opacity-20 text-dashboard-accent rounded-full text-xs font-medium">
          {t('billing.comingSoon')}
        </span>
      </div>

      {/* Payment Method */}
      <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
        <div className="flex items-center space-x-3 mb-6">
          <CreditCardIcon className="h-6 w-6 text-dashboard-accent" />
          <h3 className="text-lg font-semibold" style={{color: 'var(--text-primary)'}}>
            {t('billing.paymentMethod')}
          </h3>
        </div>
        
        <div className="space-y-4">
          <div className="p-4 rounded-lg flex items-center justify-between" style={{backgroundColor: 'var(--card-bg)'}}>
            <div className="flex items-center space-x-4">
              <div className="w-12 h-8 bg-gradient-to-r from-blue-600 to-blue-400 rounded flex items-center justify-center">
                <span className="text-white text-xs font-bold">{t('billing.visa')}</span>
              </div>
              <div>
                <p className="font-medium" style={{color: 'var(--text-primary)'}}>{t('billing.cardEnding')} 4242</p>
                <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>
                  {t('billing.expiresOn')}: {t('billing.exampleExpiry')}
                </p>
              </div>
            </div>
            <span className="px-3 py-1 bg-green-600 bg-opacity-20 text-green-400 rounded-full text-sm font-medium">
              {t('billing.default')}
            </span>
          </div>

          <button className="w-full px-4 py-3 border border-dashed rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed" 
            style={{borderColor: 'var(--input-border)', color: 'var(--text-tertiary)'}} 
            disabled
          >
            + {t('billing.addPaymentMethod')}
          </button>
        </div>
      </div>

      {/* Billing Cycle */}
      <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
        <div className="flex items-center space-x-3 mb-6">
          <CalendarIcon className="h-6 w-6 text-dashboard-accent" />
          <h3 className="text-lg font-semibold" style={{color: 'var(--text-primary)'}}>
            {t('billing.billingCycle')}
          </h3>
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
              <h4 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>
                {t('billing.monthly')}
              </h4>
              <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>
                {t('billing.monthlyDescription')}
              </p>
            </button>

            <button
              onClick={() => setBillingCycle('annual')}
              className={`p-4 rounded-lg border transition-colors ${
                billingCycle === 'annual'
                  ? 'border-dashboard-accent bg-dashboard-accent bg-opacity-10'
                  : 'border-gray-600 hover:border-gray-500'
              }`}
            >
              <h4 className="font-medium mb-1" style={{color: 'var(--text-primary)'}}>
                {t('billing.annual')}
              </h4>
              <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>
                {t('billing.annualDescription')}
              </p>
            </button>
          </div>

          <div className="flex items-center justify-between p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
            <div>
              <h4 className="font-medium" style={{color: 'var(--text-primary)'}}>
                {t('billing.autoRenew')}
              </h4>
              <p className="text-sm mt-1" style={{color: 'var(--text-tertiary)'}}>
                {t('billing.autoRenewDescription')}
              </p>
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

      {/* Email Notifications */}
      <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
        <div className="flex items-center space-x-3 mb-6">
          <BellIcon className="h-6 w-6 text-dashboard-accent" />
          <h3 className="text-lg font-semibold" style={{color: 'var(--text-primary)'}}>
            {t('billing.emailNotifications')}
          </h3>
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
          <h3 className="text-lg font-semibold" style={{color: 'var(--text-primary)'}}>
            {t('billing.invoiceHistory')}
          </h3>
        </div>
        
        <div className="space-y-3">
          {[
            { date: t('billing.invoice1Date'), amount: t('billing.invoiceAmount'), status: 'paid' },
            { date: t('billing.invoice2Date'), amount: t('billing.invoiceAmount'), status: 'paid' },
            { date: t('billing.invoice3Date'), amount: t('billing.invoiceAmount'), status: 'paid' }
          ].map((invoice, index) => (
            <div key={index} className="flex items-center justify-between p-4 rounded-lg" style={{backgroundColor: 'var(--card-bg)'}}>
              <div>
                <p className="font-medium" style={{color: 'var(--text-primary)'}}>{invoice.date}</p>
                <p className="text-sm" style={{color: 'var(--text-tertiary)'}}>
                  {t('billing.proPlan')} - {t('billing.monthlyFee')}
                </p>
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
          {t('billing.saveSettings')}
        </button>
      </div>
    </div>
  )
}