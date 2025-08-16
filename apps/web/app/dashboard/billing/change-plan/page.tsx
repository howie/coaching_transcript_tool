'use client'

import { useState } from 'react'
import { CheckIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { useI18n } from '@/contexts/i18n-context'

export default function ChangePlanPage() {
  const [billingCycle, setBillingCycle] = useState('annual')
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const { user } = useAuth()
  const { t } = useI18n()
  const router = useRouter()
  
  // Determine current plan from user data
  const currentUserPlan = user?.plan?.toLowerCase() || 'free'

  const plans = [
    {
      name: 'Free',
      price: { monthly: 0, annual: 0 },
      description: 'Start your journey with essential features',
      features: [
        '5 uploaded recordings',
        '10 linked recordings per month',
        '10 chat credits',
        'Up to 30 min per recording',
        'Basic export formats',
        'Email support'
      ],
      isCurrent: currentUserPlan === 'free',
    },
    {
      name: 'Pro',
      price: { monthly: 25, annual: 20 },
      description: 'Unlock your full potential with premium features',
      features: [
        'Unlimited uploaded recordings',
        '1,200 min of transcription per month',
        'Unlimited chat credits',
        'Up to 90 min per recording',
        'All export formats',
        'Priority email support',
        'Advanced analytics',
        'Custom branding'
      ],
      isPopular: true,
      isCurrent: currentUserPlan === 'pro',
    },
    {
      name: 'Business',
      price: { monthly: 60, annual: 50 },
      description: 'Scale seamlessly with powerful team capabilities',
      features: [
        'Unlimited uploaded recordings',
        '6,000 min of transcription per month',
        'Unlimited chat credits',
        'Up to 4 hours per recording',
        'All export formats',
        'Dedicated support',
        'Team collaboration',
        'API access',
        'Custom integrations',
        'SLA guarantee'
      ],
      isCurrent: currentUserPlan === 'business',
    },
  ]

  const handlePlanSelect = (planName: string) => {
    setSelectedPlan(planName)
  }

  const handleConfirmChange = () => {
    // TODO: Implement plan change
    console.log(`Changing to ${selectedPlan} plan with ${billingCycle} billing`)
    router.push('/dashboard/billing')
  }

  const renderPlanButton = (plan: any) => {
    const planOrder: Record<string, number> = { 'free': 0, 'pro': 1, 'business': 2 }
    const currentOrder = planOrder[currentUserPlan] || 0
    const targetOrder = planOrder[plan.name.toLowerCase()] || 0
    
    if (plan.isCurrent) {
      return (
        <div className="text-center py-2 px-4 rounded-lg bg-gray-600 text-gray-300">
          {t('billing.currentlyUsing')}
        </div>
      )
    } else if (targetOrder < currentOrder) {
      // Downgrade not allowed
      return (
        <div className="text-center py-2 px-4 rounded-lg border border-gray-600 text-gray-500 cursor-not-allowed">
          {t('billing.cannotDowngrade')}
        </div>
      )
    } else {
      // Upgrade available
      return (
        <button
          onClick={(e) => {
            e.stopPropagation()
            handlePlanSelect(plan.name)
          }}
          className="w-full py-2 px-4 rounded-lg font-medium transition-all hover:scale-105"
          style={{
            backgroundColor: selectedPlan === plan.name ? 'var(--accent-color)' : 'transparent',
            border: `2px solid var(--accent-color)`,
            color: selectedPlan === plan.name ? 'var(--bg-primary)' : 'var(--accent-color)'
          }}
        >
          {selectedPlan === plan.name ? `✓ ${t('billing.selected')}` : `${t('billing.upgradeTo')} ${plan.name}`}
        </button>
      )
    }
  }

  return (
    <div className="min-h-screen py-12" style={{backgroundColor: 'var(--bg-primary)'}}>
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/billing" className="inline-flex items-center text-dashboard-accent hover:text-dashboard-accent-hover mb-4">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            {t('common.back')} {t('billing.title')}
          </Link>
          <h1 className="text-3xl font-bold" style={{color: 'var(--text-primary)'}}>{t('billing.upgradePlan')}</h1>
          <p className="mt-2" style={{color: 'var(--text-secondary)'}}>{t('billing.upgradePlanDescription')}</p>
        </div>

        {/* Billing Cycle Toggle */}
        <div className="flex items-center justify-center mb-8">
          <div className="flex items-center space-x-3 bg-dashboard-card rounded-lg p-1">
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-4 py-2 rounded-md transition-all ${
                billingCycle === 'monthly'
                  ? 'bg-dashboard-accent text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {t('billing.monthly')}
            </button>
            <button
              onClick={() => setBillingCycle('annual')}
              className={`px-4 py-2 rounded-md transition-all flex items-center ${
                billingCycle === 'annual'
                  ? 'bg-dashboard-accent text-white'
                  : 'text-gray-400 hover:text-white'
              }`}
            >
              {t('billing.annual')}
              <span className="ml-2 px-2 py-1 bg-green-500 text-xs rounded-full">{t('billing.save31')}</span>
            </button>
          </div>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`bg-dashboard-card rounded-lg p-6 border ${
                plan.isCurrent
                  ? 'border-gray-600'
                  : selectedPlan === plan.name
                  ? 'border-dashboard-accent'
                  : 'border-dashboard-accent border-opacity-20'
              } ${plan.isPopular ? 'relative' : ''}`}
            >
              {plan.isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="px-3 py-1 bg-dashboard-accent text-white text-sm rounded-full">
                    {t('billing.popular')}
                  </span>
                </div>
              )}

              <div className="mb-4">
                <h3 className="text-xl font-bold" style={{color: 'var(--text-primary)'}}>
                  {plan.name}
                </h3>
                <p className="text-sm mt-1" style={{color: 'var(--text-secondary)'}}>
                  {plan.description}
                </p>
              </div>

              <div className="mb-6">
                <div className="flex items-baseline">
                  <span className="text-3xl font-bold" style={{color: 'var(--text-primary)'}}>
                    ${billingCycle === 'annual' ? plan.price.annual : plan.price.monthly}
                  </span>
                  <span className="ml-2" style={{color: 'var(--text-tertiary)'}}>
                    /{t('billing.perMonth')}
                  </span>
                </div>
                {billingCycle === 'annual' && plan.price.annual > 0 && (
                  <p className="text-sm mt-1" style={{color: 'var(--text-tertiary)'}}>
                    {t('billing.perYear')} ${plan.price.annual * 12}
                  </p>
                )}
              </div>

              <div className="mb-6">
                <ul className="space-y-2">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <CheckIcon className="h-5 w-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" />
                      <span className="text-sm" style={{color: 'var(--text-secondary)'}}>
                        {feature}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-8">
                {renderPlanButton(plan)}
              </div>
            </div>
          ))}
        </div>

        {/* Confirmation Section */}
        {selectedPlan && selectedPlan !== plans.find(p => p.isCurrent)?.name && (
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <h3 className="text-xl font-semibold mb-4" style={{color: 'var(--text-primary)'}}>
              {t('billing.confirmUpgrade')}
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div>
                <p className="text-sm mb-1" style={{color: 'var(--text-tertiary)'}}>{t('billing.newPlan')}</p>
                <p className="text-lg font-medium" style={{color: 'var(--text-primary)'}}>{selectedPlan}</p>
              </div>
              <div>
                <p className="text-sm mb-1" style={{color: 'var(--text-tertiary)'}}>{t('billing.billingCycle')}</p>
                <p className="text-lg font-medium" style={{color: 'var(--text-primary)'}}>
                  {billingCycle === 'annual' ? t('billing.annual') : t('billing.monthly')} - $
                  {plans.find(p => p.name === selectedPlan)?.[billingCycle === 'annual' ? 'price' : 'price'][billingCycle === 'annual' ? 'annual' : 'monthly']}
                </p>
              </div>
              <div>
                <p className="text-sm mb-1" style={{color: 'var(--text-tertiary)'}}>{t('billing.effectiveDate')}</p>
                <p className="text-lg font-medium" style={{color: 'var(--text-primary)'}}>{t('billing.immediately')}</p>
              </div>
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setSelectedPlan(null)}
                className="flex-1 px-6 py-3 border rounded-lg transition-colors" style={{borderColor: 'var(--input-border)', color: 'var(--text-secondary)'}}
              >
                {t('billing.cancel')}
              </button>
              <button
                onClick={handleConfirmChange}
                className="flex-1 px-6 py-3 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed font-semibold" style={{backgroundColor: 'var(--accent-color)', color: 'var(--bg-primary)'}}
                disabled
              >
                {t('billing.confirmUpgradeDisabled')}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}