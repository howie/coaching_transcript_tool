// Plan Management Service
// Handles all plan-related API calls and business logic

import { apiClient } from '@/lib/api';

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
  message?: string;
  limit_info?: {
    type: string;
    current: number;
    limit: number;
    reset_date?: string;
  };
  upgrade_suggestion?: {
    plan_id: string;
    display_name: string;
    benefits: string[];
  };
}

export interface SubscriptionInfo {
  startDate: string | null;
  endDate: string | null;
  active: boolean;
  stripeSubscriptionId: string | null;
}

class PlanService {
  async getAvailablePlans(): Promise<{
    plans: PlanConfig[];
    currency: string;
    billingCycles: string[];
    featuresComparison: Record<string, string>;
  }> {
    try {
      const response = await apiClient.get('/api/plans/');
      return response;
    } catch (error) {
      console.error('Failed to fetch available plans:', error);
      throw error;
    }
  }

  async getCurrentPlanStatus(): Promise<{
    currentPlan: PlanConfig;
    usageStatus: UsageStatus;
    subscriptionInfo: SubscriptionInfo;
  }> {
    try {
      const response = await apiClient.get('/api/plans/current');
      return response;
    } catch (error) {
      console.error('Failed to fetch current plan status:', error);
      throw error;
    }
  }

  async comparePlans(): Promise<{
    currentPlan: string;
    plans: PlanConfig[];
    recommendedUpgrade: any;
  }> {
    try {
      const response = await apiClient.get('/api/plans/compare');
      return response;
    } catch (error) {
      console.error('Failed to compare plans:', error);
      throw error;
    }
  }

  async validateAction(action: string, params?: any): Promise<ValidationResult> {
    try {
      const response = await apiClient.post('/api/v1/plan/validate-action', {
        action,
        ...params
      });
      return response;
    } catch (error) {
      console.error('Failed to validate action:', error);
      // Fail open - allow action if validation fails
      return {
        allowed: true,
        message: 'Validation service unavailable'
      };
    }
  }

  // Helper methods for UI
  calculateUsagePercentage(current: number, limit: number | 'unlimited' | -1): number | null {
    if (limit === 'unlimited' || limit === -1) return null;
    if (limit === 0) return 0;
    return Math.min(100, Math.round((current / limit) * 100));
  }

  getUsageColor(percentage: number | null): 'green' | 'yellow' | 'red' {
    if (percentage === null) return 'green';
    if (percentage < 70) return 'green';
    if (percentage < 90) return 'yellow';
    return 'red';
  }

  getProgressBarClass(percentage: number | null): string {
    const color = this.getUsageColor(percentage);
    switch (color) {
      case 'green':
        return 'bg-green-500';
      case 'yellow':
        return 'bg-yellow-500';
      case 'red':
        return 'bg-red-500 animate-pulse';
      default:
        return 'bg-gray-500';
    }
  }

  formatLimit(value: number | 'unlimited' | -1): string {
    if (value === 'unlimited' || value === -1) return 'Unlimited';
    return value.toLocaleString();
  }

  formatMinutes(value: number | 'unlimited' | -1): string {
    if (value === 'unlimited' || value === -1) return 'Unlimited';
    if (value < 60) return `${value} min`;
    const hours = Math.floor(value / 60);
    const minutes = value % 60;
    if (minutes === 0) return `${hours} hrs`;
    return `${hours} hrs ${minutes} min`;
  }

  formatFileSize(mb: number): string {
    if (mb < 1024) return `${mb} MB`;
    return `${(mb / 1024).toFixed(1)} GB`;
  }

  formatRetention(days: number | 'permanent' | -1): string {
    if (days === 'permanent' || days === -1) return 'Permanent';
    if (days === 30) return '30 days';
    if (days === 365) return '1 year';
    return `${days} days`;
  }

  shouldShowWarning(percentage: number | null): boolean {
    return percentage !== null && percentage >= 80;
  }

  shouldShowAlert(percentage: number | null): boolean {
    return percentage !== null && percentage >= 90;
  }

  getDaysUntilReset(resetDate: string | null): number {
    if (!resetDate) return 0;
    const reset = new Date(resetDate);
    const now = new Date();
    const diffTime = Math.abs(reset.getTime() - now.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  }

  formatDaysUntil(resetDate: string | null): string {
    const days = this.getDaysUntilReset(resetDate);
    if (days === 0) return 'Today';
    if (days === 1) return '1 day';
    return `${days} days`;
  }

  // Check if a specific feature is available for a plan
  isFeatureAvailable(plan: PlanConfig, feature: string): boolean {
    switch (feature) {
      case 'priority_support':
        return plan.features.prioritySupport;
      case 'xlsx_export':
        return plan.features.exportFormats.includes('xlsx');
      case 'vtt_export':
        return plan.features.exportFormats.includes('vtt');
      case 'srt_export':
        return plan.features.exportFormats.includes('srt');
      case 'unlimited_sessions':
        return plan.limits.maxSessions === 'unlimited' || plan.limits.maxSessions === -1;
      case 'unlimited_minutes':
        return plan.limits.maxTotalMinutes === 'unlimited' || plan.limits.maxTotalMinutes === -1;
      case 'permanent_retention':
        return plan.limits.retentionDays === 'permanent' || plan.limits.retentionDays === -1;
      default:
        return false;
    }
  }

  // Get a human-readable description of a plan limit
  describeLimitStatus(current: number, limit: number | 'unlimited' | -1, type: string): string {
    if (limit === 'unlimited' || limit === -1) {
      return `${current} ${type} used (unlimited)`;
    }
    
    const percentage = this.calculateUsagePercentage(current, limit);
    const remaining = typeof limit === 'number' ? limit - current : 0;
    
    if (percentage === null) {
      return `${current} ${type} used`;
    }
    
    if (percentage >= 100) {
      return `Limit reached (${current}/${limit} ${type})`;
    }
    
    if (percentage >= 90) {
      return `${remaining} ${type} remaining (${percentage}% used)`;
    }
    
    return `${current}/${limit} ${type} (${percentage}% used)`;
  }
}

export const planService = new PlanService();
export default planService;