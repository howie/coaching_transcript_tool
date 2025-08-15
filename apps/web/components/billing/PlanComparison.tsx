'use client'

import { useState, useEffect } from 'react';
import { PlanConfig } from '@/lib/services/plan.service';
import planService from '@/lib/services/plan.service';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { useAuth } from '@/contexts/auth-context';

interface PlanCardProps {
  plan: PlanConfig;
  price: number;
  billingCycle: 'monthly' | 'annual';
  isSelected: boolean;
  isCurrent: boolean;
  onSelect: () => void;
}

function PlanCard({ plan, price, billingCycle, isSelected, isCurrent, onSelect }: PlanCardProps) {
  const isPopular = plan.display.isPopular;
  
  return (
    <div
      onClick={() => !isCurrent && onSelect()}
      className={`relative bg-dashboard-card rounded-lg shadow-lg p-6 flex flex-col cursor-pointer transition-all ${
        isPopular ? 'border-2 border-dashboard-accent' : 'border border-gray-700'
      } ${
        isSelected ? 'ring-2 ring-dashboard-accent ring-opacity-50' : ''
      } ${
        isCurrent ? 'opacity-60 cursor-not-allowed' : 'hover:border-dashboard-accent hover:border-opacity-60'
      }`}
    >
      {isPopular && (
        <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
          <span className="bg-dashboard-accent text-white text-xs font-semibold px-3 py-1 rounded-full uppercase">
            Most Popular
          </span>
        </div>
      )}
      
      <div className="mb-4">
        <div className="flex justify-between items-start">
          <h3 className="text-2xl font-semibold text-white">{plan.displayName}</h3>
          {isCurrent && (
            <span className="px-2 py-1 bg-green-600 bg-opacity-20 text-green-400 rounded text-xs font-medium">
              Current
            </span>
          )}
        </div>
        <p className="text-sm text-gray-400 mt-1">{plan.tagline}</p>
      </div>
      
      <div className="mb-6">
        <div className="flex items-baseline">
          <span className="text-4xl font-bold text-white">${price}</span>
          <span className="text-gray-400 ml-2">/ month</span>
        </div>
        {billingCycle === 'annual' && price > 0 && (
          <p className="text-sm text-gray-500 mt-1">
            Billed annually (save {plan.pricing.annualDiscountPercentage}%)
          </p>
        )}
      </div>
      
      <p className="text-gray-300 mb-6 flex-grow">{plan.description}</p>
      
      <div className="space-y-3 mb-6">
        <div className="flex items-center">
          <CheckIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
          <span className="text-sm text-gray-300">
            {planService.formatLimit(plan.limits.maxSessions)} sessions/month
          </span>
        </div>
        <div className="flex items-center">
          <CheckIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
          <span className="text-sm text-gray-300">
            {planService.formatMinutes(plan.limits.maxTotalMinutes)} audio/month
          </span>
        </div>
        <div className="flex items-center">
          <CheckIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
          <span className="text-sm text-gray-300">
            {planService.formatFileSize(plan.limits.maxFileSizeMb)} max file size
          </span>
        </div>
        <div className="flex items-center">
          <CheckIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
          <span className="text-sm text-gray-300">
            {plan.limits.concurrentProcessing} concurrent processing
          </span>
        </div>
        {plan.features.prioritySupport && (
          <div className="flex items-center">
            <CheckIcon className="h-5 w-5 text-green-500 mr-3 flex-shrink-0" />
            <span className="text-sm text-gray-300">Priority support</span>
          </div>
        )}
      </div>
      
      <div className="mt-auto">
        {isCurrent ? (
          <div className="text-center py-2 text-gray-500">
            Your current plan
          </div>
        ) : (
          <button
            className={`w-full py-2 rounded-lg font-medium transition-colors ${
              isSelected
                ? 'bg-dashboard-accent text-white'
                : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
            }`}
          >
            {isSelected ? '✓ Selected' : 'Select Plan'}
          </button>
        )}
      </div>
    </div>
  );
}

export function PlanComparison() {
  const [plans, setPlans] = useState<PlanConfig[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('annual');
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);
  const { user } = useAuth();

  useEffect(() => {
    loadPlans();
  }, []);

  const loadPlans = async () => {
    try {
      const data = await planService.getAvailablePlans();
      setPlans(data.plans);
    } catch (error) {
      console.error('Failed to load plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPrice = (plan: PlanConfig) => {
    return billingCycle === 'annual' 
      ? plan.pricing.annualUsd 
      : plan.pricing.monthlyUsd;
  };

  const features = [
    { 
      key: 'sessions', 
      label: 'Coaching Sessions',
      getValue: (plan: PlanConfig) => planService.formatLimit(plan.limits.maxSessions)
    },
    { 
      key: 'minutes', 
      label: 'Audio Minutes',
      getValue: (plan: PlanConfig) => planService.formatMinutes(plan.limits.maxTotalMinutes)
    },
    { 
      key: 'transcriptions', 
      label: 'Transcriptions',
      getValue: (plan: PlanConfig) => planService.formatLimit(plan.limits.maxTranscriptionCount)
    },
    { 
      key: 'fileSize', 
      label: 'Max File Size',
      getValue: (plan: PlanConfig) => planService.formatFileSize(plan.limits.maxFileSizeMb)
    },
    { 
      key: 'exportFormats', 
      label: 'Export Formats',
      getValue: (plan: PlanConfig) => plan.features.exportFormats.join(', ').toUpperCase()
    },
    { 
      key: 'concurrent', 
      label: 'Concurrent Processing',
      getValue: (plan: PlanConfig) => `${plan.limits.concurrentProcessing} files`
    },
    { 
      key: 'support', 
      label: 'Priority Support',
      getValue: (plan: PlanConfig) => plan.features.prioritySupport
    },
    { 
      key: 'retention', 
      label: 'Data Retention',
      getValue: (plan: PlanConfig) => planService.formatRetention(plan.limits.retentionDays)
    },
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-dashboard-accent"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Billing Cycle Toggle */}
      <div className="flex justify-center">
        <div className="inline-flex rounded-full p-1 bg-gray-800">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-6 py-2 rounded-full transition-all ${
              billingCycle === 'monthly'
                ? 'bg-dashboard-accent text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Monthly
          </button>
          <button
            onClick={() => setBillingCycle('annual')}
            className={`px-6 py-2 rounded-full transition-all flex items-center ${
              billingCycle === 'annual'
                ? 'bg-dashboard-accent text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Annual
            {plans.length > 0 && plans[0].pricing.annualDiscountPercentage > 0 && (
              <span className="ml-2 text-xs bg-green-500 bg-opacity-20 text-green-400 px-2 py-0.5 rounded-full">
                Save {plans[0].pricing.annualDiscountPercentage}%
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Plan Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {plans.map((plan) => (
          <PlanCard
            key={plan.planName}
            plan={plan}
            price={getPrice(plan)}
            billingCycle={billingCycle}
            isSelected={selectedPlan === plan.planName}
            isCurrent={user?.plan?.toLowerCase() === plan.planName}
            onSelect={() => setSelectedPlan(plan.planName)}
          />
        ))}
      </div>

      {/* Feature Comparison Table */}
      <div className="bg-dashboard-card rounded-lg p-6 border border-gray-700">
        <h3 className="text-lg font-semibold text-white mb-6">
          Detailed Feature Comparison
        </h3>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-400">
                  Feature
                </th>
                {plans.map(plan => (
                  <th key={plan.planName} className="text-center py-3 px-4">
                    <div className="text-sm font-medium text-white">
                      {plan.displayName}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {features.map((feature, idx) => (
                <tr 
                  key={feature.key} 
                  className={`border-b border-gray-800 ${
                    idx % 2 === 0 ? 'bg-gray-900 bg-opacity-30' : ''
                  }`}
                >
                  <td className="py-3 px-4 text-sm text-gray-300">
                    {feature.label}
                  </td>
                  {plans.map(plan => {
                    const value = feature.getValue(plan);
                    return (
                      <td key={plan.planName} className="text-center py-3 px-4">
                        {typeof value === 'boolean' ? (
                          value ? (
                            <CheckIcon className="h-5 w-5 text-green-500 mx-auto" />
                          ) : (
                            <XMarkIcon className="h-5 w-5 text-gray-600 mx-auto" />
                          )
                        ) : (
                          <span className="text-sm text-gray-200">{value}</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Action Section */}
      {selectedPlan && selectedPlan !== user?.plan?.toLowerCase() && (
        <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-40">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-white">
                Ready to upgrade to {plans.find(p => p.planName === selectedPlan)?.displayName}?
              </h3>
              <p className="text-sm text-gray-400 mt-1">
                {billingCycle === 'annual' 
                  ? `Billed annually at $${plans.find(p => p.planName === selectedPlan)?.pricing.annualUsd * 12}/year`
                  : `Billed monthly at $${plans.find(p => p.planName === selectedPlan)?.pricing.monthlyUsd}/month`
                }
              </p>
            </div>
            <button
              onClick={() => window.location.href = `/dashboard/billing/change-plan?plan=${selectedPlan}&cycle=${billingCycle}`}
              className="px-6 py-3 bg-dashboard-accent text-white rounded-lg font-medium hover:bg-dashboard-accent-hover transition-colors"
            >
              Continue to Payment
            </button>
          </div>
        </div>
      )}
    </div>
  );
}