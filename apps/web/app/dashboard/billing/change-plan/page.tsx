'use client'

import { useState } from 'react'
import { CheckIcon, ArrowLeftIcon } from '@heroicons/react/24/outline'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'

export default function ChangePlanPage() {
  const [billingCycle, setBillingCycle] = useState('annual')
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const { user } = useAuth()
  const router = useRouter()

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
      isCurrent: user?.plan === 'Free' || !user?.plan,
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
      isCurrent: user?.plan === 'Pro',
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
      isCurrent: user?.plan === 'Business',
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

  return (
    <div className="min-h-screen bg-dashboard-bg py-12">
      <div className="max-w-6xl mx-auto px-4">
        {/* Header */}
        <div className="mb-8">
          <Link href="/dashboard/billing" className="inline-flex items-center text-dashboard-accent hover:text-dashboard-accent-hover mb-4">
            <ArrowLeftIcon className="h-4 w-4 mr-2" />
            返回 Billing
          </Link>
          <h1 className="text-3xl font-bold text-white">選擇方案</h1>
          <p className="text-gray-300 mt-2">選擇最適合您需求的方案</p>
        </div>

        {/* 開發中標籤 */}
        <div className="mb-6 bg-orange-500 bg-opacity-20 border border-orange-500 border-opacity-50 rounded-lg p-4">
          <div className="flex items-center space-x-3">
            <span className="text-2xl">🚧</span>
            <div>
              <h4 className="font-semibold text-orange-300">功能施工中</h4>
              <p className="text-sm text-orange-200 opacity-90">方案變更功能仍在開發中，目前僅供預覽</p>
            </div>
          </div>
        </div>

        {/* Billing Cycle Toggle */}
        <div className="text-center mb-12">
          <div className="inline-flex bg-gray-700 rounded-full p-1">
            <button
              onClick={() => setBillingCycle('annual')}
              className={`px-6 py-2 text-sm font-medium rounded-full transition-colors ${
                billingCycle === 'annual'
                  ? 'bg-dashboard-accent text-white shadow'
                  : 'text-gray-400'
              }`}
            >
              年繳 <span className="ml-2 bg-green-600 bg-opacity-20 text-green-400 text-xs font-semibold px-2 py-1 rounded-full">省 31%</span>
            </button>
            <button
              onClick={() => setBillingCycle('monthly')}
              className={`px-6 py-2 text-sm font-medium rounded-full transition-colors ${
                billingCycle === 'monthly'
                  ? 'bg-dashboard-accent text-white shadow'
                  : 'text-gray-400'
              }`}
            >
              月繳
            </button>
          </div>
        </div>

        {/* Plans Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {plans.map((plan) => (
            <div
              key={plan.name}
              onClick={() => !plan.isCurrent && handlePlanSelect(plan.name)}
              className={`bg-dashboard-card rounded-lg shadow-lg p-8 flex flex-col cursor-pointer transition-all ${
                plan.isPopular ? 'border-2 border-dashboard-accent' : 'border border-dashboard-accent border-opacity-20'
              } ${
                selectedPlan === plan.name ? 'ring-2 ring-dashboard-accent ring-opacity-50' : ''
              } ${
                plan.isCurrent ? 'opacity-60 cursor-not-allowed' : 'hover:border-dashboard-accent hover:border-opacity-40'
              }`}
            >
              {plan.isPopular && (
                <div className="text-center mb-4">
                  <span className="bg-dashboard-accent text-white text-xs font-semibold px-3 py-1 rounded-full uppercase">最受歡迎</span>
                </div>
              )}
              
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-semibold text-white">{plan.name}</h2>
                {plan.isCurrent && (
                  <span className="px-3 py-1 bg-green-600 bg-opacity-20 text-green-400 rounded-full text-sm font-medium">
                    目前方案
                  </span>
                )}
              </div>
              
              <p className="text-4xl font-bold text-white">
                ${billingCycle === 'annual' ? plan.price.annual : plan.price.monthly}
                <span className="text-lg font-medium text-gray-400">/月</span>
              </p>
              <p className="text-sm text-gray-400 mb-4">
                {billingCycle === 'annual' && plan.price.annual > 0 ? '按年計費' : ''}
              </p>
              <p className="text-gray-300 mb-6">{plan.description}</p>
              
              <div className="flex-grow">
                <ul className="space-y-3">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <CheckIcon className="w-5 h-5 text-dashboard-accent mr-3 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-300 text-sm">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              <div className="mt-8">
                {plan.isCurrent ? (
                  <div className="text-center text-gray-400 font-medium">
                    目前使用中
                  </div>
                ) : plan.name === 'Pro' ? (
                  <div className="text-center">
                    <div className="text-dashboard-accent font-medium mb-2">Upgrade to Pro</div>
                    <div className="text-sm text-gray-400">(Coming Soon)</div>
                  </div>
                ) : plan.name === 'Business' ? (
                  <div className="text-center">
                    <div className="text-dashboard-accent font-medium mb-2">Upgrade to Business</div>
                    <div className="text-sm text-gray-400">(Coming Soon)</div>
                  </div>
                ) : (
                  <div className={`text-center font-medium ${
                    selectedPlan === plan.name ? 'text-dashboard-accent' : 'text-gray-400'
                  }`}>
                    {selectedPlan === plan.name ? '✓ 已選擇' : '點擊選擇'}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Confirmation Section */}
        {selectedPlan && (
          <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
            <h3 className="text-xl font-semibold text-white mb-4">確認方案變更</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div>
                <p className="text-sm text-gray-400 mb-1">新方案</p>
                <p className="text-lg font-medium text-white">{selectedPlan}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400 mb-1">計費週期</p>
                <p className="text-lg font-medium text-white">{billingCycle === 'annual' ? '年繳' : '月繳'}</p>
              </div>
              <div>
                <p className="text-sm text-gray-400 mb-1">每月費用</p>
                <p className="text-lg font-medium text-white">
                  ${plans.find(p => p.name === selectedPlan)?.[billingCycle === 'annual' ? 'price' : 'price'][billingCycle === 'annual' ? 'annual' : 'monthly']}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-400 mb-1">生效日期</p>
                <p className="text-lg font-medium text-white">立即生效</p>
              </div>
            </div>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setSelectedPlan(null)}
                className="flex-1 px-6 py-3 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-700 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleConfirmChange}
                className="flex-1 px-6 py-3 bg-dashboard-accent text-white rounded-lg hover:bg-opacity-90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                disabled
              >
                確認變更（功能開發中）
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}