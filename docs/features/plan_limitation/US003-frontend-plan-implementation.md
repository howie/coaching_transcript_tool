# US003: Frontend Plan Implementation

## 📋 User Story

**As a** platform user  
**I want** a clear and intuitive interface to understand my plan limits and usage  
**So that** I can manage my subscription effectively and upgrade when needed

## 🎯 Acceptance Criteria

### 1. Plan Display & Comparison
- [ ] Dynamic plan cards showing all available tiers (Free, Pro, Business)
- [ ] Clear visual differentiation between plans
- [ ] Monthly/Annual billing toggle with savings calculation
- [ ] "Current Plan" and "Most Popular" badges
- [ ] Feature comparison matrix with checkmarks

### 2. Usage Tracking & Visualization
- [ ] Real-time usage meters for all tracked metrics
- [ ] Progress bars with color coding (green → yellow → red)
- [ ] Percentage and absolute values display
- [ ] Days remaining in billing cycle
- [ ] Usage history graphs (last 6 months)

### 3. Limit Warnings & Alerts
- [ ] 80% usage warning banners
- [ ] 90% usage alerts with upgrade prompts
- [ ] Limit exceeded modals with clear CTAs
- [ ] Soft limit grace period notifications
- [ ] Email notification preferences

### 4. Upgrade Flow
- [ ] One-click upgrade from any limit warning
- [ ] Plan comparison with benefits highlighted
- [ ] Proration calculator for mid-cycle upgrades
- [ ] Payment method selection/update
- [ ] Confirmation with immediate effect notice

### 5. API Integration
- [ ] Fetch plans from `/api/plans/`
- [ ] Get current usage from `/api/plans/current`
- [ ] Compare plans via `/api/plans/compare`
- [ ] Validate actions before execution
- [ ] Handle API errors gracefully

## 🏗️ Technical Implementation

### API Service Layer

```typescript
// apps/web/lib/services/plan.service.ts

export interface PlanLimit {
  maxSessions: number | 'unlimited';
  maxTotalMinutes: number | 'unlimited';
  maxTranscriptionCount: number | 'unlimited';
  maxFileSizeMb: number;
  exportFormats: string[];
  concurrentProcessing: number;
  retentionDays: number | 'permanent';
}

export interface PlanConfig {
  planName: 'free' | 'pro' | 'business';
  displayName: string;
  description: string;
  tagline: string;
  limits: PlanLimit;
  features: {
    prioritySupport: boolean;
    exportFormats: string[];
    concurrentProcessing: number;
  };
  pricing: {
    monthlyUsd: number;
    annualUsd: number;
    annualDiscountPercentage: number;
    annualSavingsUsd: number;
  };
  display: {
    isPopular: boolean;
    colorScheme: string;
    sortOrder: number;
  };
  stripe?: {
    monthlyPriceId?: string;
    annualPriceId?: string;
  };
}

export interface UsageStatus {
  userId: string;
  plan: string;
  planDisplayName: string;
  currentUsage: {
    sessions: number;
    minutes: number;
    transcriptions: number;
  };
  planLimits: PlanLimit;
  usagePercentages: {
    sessions: number | null;
    minutes: number | null;
    transcriptions: number | null;
  };
  approachingLimits: {
    sessions: boolean;
    minutes: boolean;
    transcriptions: boolean;
  };
  nextReset: string | null;
  upgradeSuggestion?: {
    suggestedPlan: string;
    displayName: string;
    keyBenefits: string[];
    pricing: any;
    tagline: string;
  };
}

export interface ValidationResult {
  allowed: boolean;
  message: string;
  limitInfo?: {
    type: string;
    current: number;
    limit: number;
  };
  upgradeSuggestion?: any;
}

class PlanService {
  private apiClient: ApiClient;

  constructor() {
    this.apiClient = new ApiClient();
  }

  async getAvailablePlans(): Promise<{
    plans: PlanConfig[];
    currency: string;
    billingCycles: string[];
  }> {
    return this.apiClient.get('/api/plans/');
  }

  async getCurrentPlanStatus(): Promise<{
    currentPlan: PlanConfig;
    usageStatus: UsageStatus;
    subscriptionInfo: {
      startDate: string | null;
      endDate: string | null;
      active: boolean;
      stripeSubscriptionId: string | null;
    };
  }> {
    return this.apiClient.get('/api/plans/current');
  }

  async comparePlans(): Promise<{
    currentPlan: string;
    plans: PlanConfig[];
    recommendedUpgrade: any;
  }> {
    return this.apiClient.get('/api/plans/compare');
  }

  async validateAction(action: string, params?: any): Promise<ValidationResult> {
    return this.apiClient.post('/api/plans/validate', {
      action,
      ...params
    });
  }

  // Helper methods for UI
  calculateUsagePercentage(current: number, limit: number | 'unlimited'): number | null {
    if (limit === 'unlimited' || limit === -1) return null;
    return Math.min(100, Math.round((current / limit) * 100));
  }

  getUsageColor(percentage: number | null): string {
    if (percentage === null) return 'green';
    if (percentage < 70) return 'green';
    if (percentage < 90) return 'yellow';
    return 'red';
  }

  formatLimit(value: number | 'unlimited' | -1): string {
    if (value === 'unlimited' || value === -1) return 'Unlimited';
    return value.toLocaleString();
  }

  shouldShowWarning(percentage: number | null): boolean {
    return percentage !== null && percentage >= 80;
  }

  shouldShowAlert(percentage: number | null): boolean {
    return percentage !== null && percentage >= 90;
  }
}

export default new PlanService();
```

### React Components

```typescript
// apps/web/components/billing/UsageCard.tsx

import { UsageStatus } from '@/lib/services/plan.service';
import { CircularProgress } from '@/components/ui/circular-progress';
import { AlertBanner } from '@/components/ui/alert-banner';

interface UsageCardProps {
  usageStatus: UsageStatus;
  onUpgrade: () => void;
}

export function UsageCard({ usageStatus, onUpgrade }: UsageCardProps) {
  const metrics = [
    {
      key: 'sessions',
      label: 'Sessions',
      icon: DocumentTextIcon,
      current: usageStatus.currentUsage.sessions,
      limit: usageStatus.planLimits.maxSessions,
      percentage: usageStatus.usagePercentages.sessions,
    },
    {
      key: 'minutes',
      label: 'Audio Minutes',
      icon: ClockIcon,
      current: usageStatus.currentUsage.minutes,
      limit: usageStatus.planLimits.maxTotalMinutes,
      percentage: usageStatus.usagePercentages.minutes,
    },
    {
      key: 'transcriptions',
      label: 'Transcriptions',
      icon: MicrophoneIcon,
      current: usageStatus.currentUsage.transcriptions,
      limit: usageStatus.planLimits.maxTranscriptionCount,
      percentage: usageStatus.usagePercentages.transcriptions,
    },
  ];

  const hasWarnings = Object.values(usageStatus.approachingLimits).some(v => v);

  return (
    <div className="bg-dashboard-card rounded-lg p-6 border border-dashboard-accent border-opacity-20">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h2 className="text-xl font-semibold text-white">Current Usage</h2>
          <p className="text-sm text-gray-400 mt-1">
            {usageStatus.planDisplayName} Plan
          </p>
        </div>
        {usageStatus.nextReset && (
          <div className="text-right">
            <p className="text-xs text-gray-500">Resets in</p>
            <p className="text-sm font-medium text-gray-300">
              {formatDaysUntil(usageStatus.nextReset)}
            </p>
          </div>
        )}
      </div>

      {hasWarnings && (
        <AlertBanner
          type="warning"
          message="You're approaching your plan limits"
          action={{
            label: 'Upgrade Now',
            onClick: onUpgrade
          }}
          className="mb-4"
        />
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {metrics.map((metric) => (
          <div key={metric.key} className="relative">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                <metric.icon className="h-5 w-5 text-dashboard-accent" />
                <span className="text-sm font-medium text-gray-300">
                  {metric.label}
                </span>
              </div>
              {metric.percentage !== null && metric.percentage >= 90 && (
                <span className="text-xs text-red-400 font-medium animate-pulse">
                  {metric.percentage}%
                </span>
              )}
            </div>
            
            <div className="relative">
              <CircularProgress
                value={metric.percentage || 0}
                maxValue={100}
                size="lg"
                color={getProgressColor(metric.percentage)}
                showValue={false}
              />
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-white">
                  {metric.current}
                </span>
                <span className="text-xs text-gray-400">
                  / {formatLimit(metric.limit)}
                </span>
              </div>
            </div>

            {metric.percentage !== null && (
              <div className="mt-3">
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div 
                    className={`h-2 rounded-full transition-all duration-300 ${
                      getProgressBarClass(metric.percentage)
                    }`}
                    style={{ width: `${Math.min(100, metric.percentage)}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>

      {usageStatus.upgradeSuggestion && (
        <div className="mt-6 p-4 bg-dashboard-accent bg-opacity-10 rounded-lg border border-dashboard-accent border-opacity-30">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <h4 className="text-sm font-semibold text-dashboard-accent mb-1">
                Upgrade to {usageStatus.upgradeSuggestion.displayName}
              </h4>
              <p className="text-xs text-gray-400 mb-2">
                {usageStatus.upgradeSuggestion.tagline}
              </p>
              <ul className="space-y-1">
                {usageStatus.upgradeSuggestion.keyBenefits.slice(0, 3).map((benefit, idx) => (
                  <li key={idx} className="text-xs text-gray-300 flex items-center">
                    <CheckIcon className="h-3 w-3 text-green-400 mr-2" />
                    {benefit}
                  </li>
                ))}
              </ul>
            </div>
            <button
              onClick={onUpgrade}
              className="ml-4 px-4 py-2 bg-dashboard-accent text-white rounded-lg text-sm font-medium hover:bg-dashboard-accent-hover transition-colors"
            >
              Upgrade
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
```

```typescript
// apps/web/components/billing/PlanComparison.tsx

import { useState, useEffect } from 'react';
import { PlanConfig } from '@/lib/services/plan.service';
import planService from '@/lib/services/plan.service';

export function PlanComparison() {
  const [plans, setPlans] = useState<PlanConfig[]>([]);
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('annual');
  const [loading, setLoading] = useState(true);
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null);

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
    { key: 'sessions', label: 'Coaching Sessions', format: formatLimit },
    { key: 'minutes', label: 'Audio Minutes', format: formatMinutes },
    { key: 'transcriptions', label: 'Transcriptions', format: formatLimit },
    { key: 'fileSize', label: 'Max File Size', format: formatFileSize },
    { key: 'exportFormats', label: 'Export Formats', format: formatList },
    { key: 'concurrent', label: 'Concurrent Processing', format: formatNumber },
    { key: 'support', label: 'Priority Support', format: formatBoolean },
    { key: 'retention', label: 'Data Retention', format: formatRetention },
  ];

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
            className={`px-6 py-2 rounded-full transition-all ${
              billingCycle === 'annual'
                ? 'bg-dashboard-accent text-white'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            Annual
            <span className="ml-2 text-xs bg-green-500 bg-opacity-20 text-green-400 px-2 py-0.5 rounded-full">
              Save {plans[0]?.pricing.annualDiscountPercentage || 0}%
            </span>
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
                <tr key={feature.key} className={`border-b border-gray-800 ${
                  idx % 2 === 0 ? 'bg-gray-900 bg-opacity-30' : ''
                }`}>
                  <td className="py-3 px-4 text-sm text-gray-300">
                    {feature.label}
                  </td>
                  {plans.map(plan => (
                    <td key={plan.planName} className="text-center py-3 px-4">
                      <span className="text-sm text-gray-200">
                        {feature.format(getFeatureValue(plan, feature.key))}
                      </span>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
```

### Limit Validation Hook

```typescript
// apps/web/hooks/usePlanLimits.ts

import { useState, useCallback } from 'react';
import planService, { ValidationResult } from '@/lib/services/plan.service';
import { useToast } from '@/hooks/useToast';

export function usePlanLimits() {
  const [validating, setValidating] = useState(false);
  const { showToast } = useToast();

  const validateAction = useCallback(async (
    action: string,
    params?: any,
    options?: {
      showError?: boolean;
      showUpgradePrompt?: boolean;
    }
  ): Promise<boolean> => {
    setValidating(true);
    try {
      const result: ValidationResult = await planService.validateAction(action, params);
      
      if (!result.allowed) {
        if (options?.showError !== false) {
          showToast({
            type: 'error',
            title: 'Plan Limit Reached',
            message: result.message,
            action: options?.showUpgradePrompt && result.upgradeSuggestion ? {
              label: `Upgrade to ${result.upgradeSuggestion.displayName}`,
              onClick: () => {
                window.location.href = '/dashboard/billing/change-plan';
              }
            } : undefined
          });
        }
      }
      
      return result.allowed;
    } catch (error) {
      console.error('Failed to validate action:', error);
      return true; // Allow action on error (fail open)
    } finally {
      setValidating(false);
    }
  }, [showToast]);

  const checkBeforeAction = useCallback(async (
    action: string,
    callback: () => void | Promise<void>,
    params?: any
  ) => {
    const allowed = await validateAction(action, params, {
      showError: true,
      showUpgradePrompt: true
    });
    
    if (allowed) {
      await callback();
    }
  }, [validateAction]);

  return {
    validateAction,
    checkBeforeAction,
    validating
  };
}
```

### Updated Billing Page

```typescript
// apps/web/app/dashboard/billing/page.tsx

'use client'

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import planService, { UsageStatus, PlanConfig } from '@/lib/services/plan.service';
import { UsageCard } from '@/components/billing/UsageCard';
import { PlanComparison } from '@/components/billing/PlanComparison';
import { UsageHistory } from '@/components/billing/UsageHistory';
import { CreditCardIcon, ChartBarIcon, ClockIcon } from '@heroicons/react/24/outline';
import Link from 'next/link';

export default function BillingPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [loading, setLoading] = useState(true);
  const [usageStatus, setUsageStatus] = useState<UsageStatus | null>(null);
  const [currentPlan, setCurrentPlan] = useState<PlanConfig | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'usage' | 'plans'>('overview');

  useEffect(() => {
    loadPlanData();
  }, []);

  const loadPlanData = async () => {
    try {
      const data = await planService.getCurrentPlanStatus();
      setUsageStatus(data.usageStatus);
      setCurrentPlan(data.currentPlan);
    } catch (error) {
      console.error('Failed to load plan data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    window.location.href = '/dashboard/billing/change-plan';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-dashboard-accent"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dashboard-bg py-12">
      <div className="max-w-7xl mx-auto px-4">
        {/* Page Header */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-3">
            <CreditCardIcon className="h-8 w-8 text-dashboard-accent" />
            <h1 className="text-3xl font-bold text-white">
              {t('billing.title')}
            </h1>
          </div>
          <div className="flex space-x-4">
            <Link 
              href="/dashboard/billing/payment-settings"
              className="px-4 py-2 border border-gray-600 text-gray-300 rounded-lg hover:bg-gray-800 transition-colors"
            >
              Payment Settings
            </Link>
            <button
              onClick={handleUpgrade}
              className="px-4 py-2 bg-dashboard-accent text-white rounded-lg hover:bg-dashboard-accent-hover transition-colors"
            >
              Upgrade Plan
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex space-x-1 mb-8 border-b border-gray-700">
          {[
            { id: 'overview', label: 'Overview', icon: ChartBarIcon },
            { id: 'usage', label: 'Usage History', icon: ClockIcon },
            { id: 'plans', label: 'Compare Plans', icon: CreditCardIcon },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-3 border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-dashboard-accent text-dashboard-accent'
                  : 'border-transparent text-gray-400 hover:text-white'
              }`}
            >
              <tab.icon className="h-5 w-5" />
              <span>{tab.label}</span>
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="space-y-8">
          {activeTab === 'overview' && (
            <>
              {/* Current Plan Summary */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  {usageStatus && (
                    <UsageCard 
                      usageStatus={usageStatus} 
                      onUpgrade={handleUpgrade}
                    />
                  )}
                </div>
                <div>
                  {currentPlan && (
                    <CurrentPlanSummary 
                      plan={currentPlan}
                      subscriptionInfo={data.subscriptionInfo}
                    />
                  )}
                </div>
              </div>

              {/* Quick Stats */}
              <QuickStats usageStatus={usageStatus} />
            </>
          )}

          {activeTab === 'usage' && (
            <UsageHistory />
          )}

          {activeTab === 'plans' && (
            <PlanComparison />
          )}
        </div>
      </div>
    </div>
  );
}
```

## 🎨 UI/UX Design Specifications

### Visual Hierarchy
1. **Color Coding System**
   - Green (0-70%): Safe usage zone
   - Yellow (70-89%): Warning zone
   - Red (90-100%): Critical zone
   - Dashboard accent: Upgrade CTAs

2. **Progress Indicators**
   - Circular progress for main metrics
   - Linear progress bars for detailed view
   - Animated pulse for critical warnings
   - Smooth transitions on value changes

3. **Responsive Breakpoints**
   - Mobile (<640px): Single column, stacked cards
   - Tablet (640-1024px): 2-column grid
   - Desktop (>1024px): 3-column grid, side panels

### Interaction Patterns
1. **Hover States**
   - Plan cards: Subtle elevation + border highlight
   - Buttons: Color transition + scale
   - Progress bars: Show tooltip with exact values

2. **Loading States**
   - Skeleton screens for initial load
   - Shimmer effect for updating values
   - Spinner for action processing

3. **Error Handling**
   - Toast notifications for API errors
   - Inline error messages for validation
   - Retry buttons for failed requests

## 📊 Success Metrics

### User Experience
- Page load time <2s
- Real-time usage updates <500ms
- Zero UI blocking during validation
- 100% mobile responsive

### Engagement
- >80% users check usage weekly
- >50% click-through on upgrade prompts
- <10% support tickets about limits

### Technical
- API response time <200ms
- Cache hit rate >90%
- Zero false limit violations

## 🧪 Testing Requirements

### Unit Tests
- Plan service methods
- Usage calculation logic
- Color coding functions
- Limit formatting utilities

### Integration Tests
- API endpoint connections
- Real-time usage updates
- Plan upgrade flow
- Payment integration

### E2E Tests
- Complete billing page flow
- Plan comparison and selection
- Usage warning triggers
- Upgrade completion

## 📋 Implementation Checklist

### Phase 1: Foundation (Week 1)
- [ ] Create plan service with API integration
- [ ] Build usage tracking hooks
- [ ] Implement validation utilities
- [ ] Set up error handling

### Phase 2: Core Components (Week 2)
- [ ] Usage card with real-time data
- [ ] Plan comparison table
- [ ] Progress indicators
- [ ] Warning/alert banners

### Phase 3: Integration (Week 3)
- [ ] Connect billing page to API
- [ ] Implement plan change flow
- [ ] Add usage history graphs
- [ ] Create upgrade prompts

### Phase 4: Polish (Week 4)
- [ ] Mobile optimization
- [ ] Loading states
- [ ] Animation refinements
- [ ] A/B testing setup

## 🔗 Dependencies

- Backend API endpoints (US002)
- Stripe integration for payments
- Authentication system
- Internationalization (i18n)
- Toast notification system

## 🚀 Deployment Notes

1. **Feature Flags**
   - Gradual rollout to 10% → 50% → 100%
   - A/B test upgrade prompt designs
   - Monitor conversion rates

2. **Monitoring**
   - Track API response times
   - Monitor upgrade funnel metrics
   - Alert on high error rates

3. **Migration**
   - Existing users see current usage
   - No disruption to active sessions
   - Graceful degradation on API failure