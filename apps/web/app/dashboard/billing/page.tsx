'use client'

import { useState } from 'react'
import { CheckIcon } from '@heroicons/react/24/outline'

export default function BillingPage() {
  const [billingCycle, setBillingCycle] = useState('annual')

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
      ],
      isCurrent: true,
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
      ],
      isPopular: true,
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
      ],
    },
  ]

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 py-12">
      <div className="max-w-4xl mx-auto px-4">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white">Change your plan</h1>
          <div className="mt-4">
            <div className="inline-flex bg-gray-200 dark:bg-gray-700 rounded-full p-1">
              <button
                onClick={() => setBillingCycle('annual')}
                className={`px-6 py-2 text-sm font-medium rounded-full transition-colors ${
                  billingCycle === 'annual'
                    ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Annual <span className="ml-2 bg-green-100 text-green-800 text-xs font-semibold px-2 py-1 rounded-full">Save 31%</span>
              </button>
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-6 py-2 text-sm font-medium rounded-full transition-colors ${
                  billingCycle === 'monthly'
                    ? 'bg-white dark:bg-gray-800 text-gray-900 dark:text-white shadow'
                    : 'text-gray-600 dark:text-gray-400'
                }`}
              >
                Monthly
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 flex flex-col ${
                plan.isPopular ? 'border-2 border-indigo-600' : 'border border-gray-200 dark:border-gray-700'
              }`}
            >
              {plan.isPopular && (
                <div className="text-center mb-4">
                  <span className="bg-indigo-600 text-white text-xs font-semibold px-3 py-1 rounded-full uppercase">Popular</span>
                </div>
              )}
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-white">{plan.name}</h2>
              <p className="mt-4 text-4xl font-bold text-gray-900 dark:text-white">
                ${billingCycle === 'annual' ? plan.price.annual : plan.price.monthly}
                <span className="text-lg font-medium text-gray-500 dark:text-gray-400">/month</span>
              </p>
              <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                {billingCycle === 'annual' && plan.price.annual > 0 ? 'billed annually' : ''}
              </p>
              <p className="mt-4 text-gray-600 dark:text-gray-300">{plan.description}</p>
              
              <div className="mt-8 mb-8 flex-grow">
                <ul className="space-y-4">
                  {plan.features.map((feature, index) => (
                    <li key={index} className="flex items-start">
                      <CheckIcon className="w-5 h-5 text-indigo-600 mr-3 flex-shrink-0" />
                      <span className="text-gray-600 dark:text-gray-300">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {plan.isCurrent ? (
                <button className="w-full mt-auto px-6 py-3 border border-gray-300 rounded-md text-center text-sm font-medium text-gray-700 bg-gray-100 dark:bg-gray-700 dark:text-gray-200 cursor-default">
                  Current Plan
                </button>
              ) : (
                <button className={`w-full mt-auto px-6 py-3 rounded-md text-center text-sm font-medium ${
                  plan.isPopular
                    ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-200 dark:hover:bg-gray-600'
                }`}>
                  Upgrade to {plan.name}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
