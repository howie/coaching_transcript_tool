/**
 * Subscription service for managing plan data and user subscriptions
 * This service fetches real data from the backend database
 */

import { apiClient } from '../api'

export interface SubscriptionData {
  subscription?: {
    id: string
    plan_id: string
    plan_name: string
    billing_cycle: 'monthly' | 'annual'
    amount_twd: number
    status: 'active' | 'cancelled' | 'past_due' | 'unpaid'
    current_period_start: string
    current_period_end: string
    cancel_at_period_end: boolean
    next_payment_date?: string
  }
  payment_method?: {
    card_last4: string
    card_brand: string
    auth_status: string
  }
  status: 'no_subscription' | 'active' | 'cancelled' | 'past_due'
}

export interface PlanData {
  id: string
  name: string
  display_name: string
  description: string
  pricing: {
    monthly_twd: number
    annual_twd: number
    monthly_usd?: number
    annual_usd?: number
  }
  features: string[]
  limits: {
    max_sessions: number
    max_transcriptions: number
    max_total_minutes: number
    max_file_size_mb: number
  }
  is_active: boolean
  sort_order: number
}

export interface BillingHistory {
  payments: Array<{
    id: string
    amount: number
    currency: string
    status: 'success' | 'failed' | 'pending'
    period_start: string
    period_end: string
    processed_at?: string
    failure_reason?: string
    retry_count: number
  }>
  total: number
  limit: number
  offset: number
}

class SubscriptionService {
  /**
   * Get current user subscription details from database
   */
  async getCurrentSubscription(): Promise<SubscriptionData> {
    try {
      const response = await apiClient.get('/api/v1/subscriptions/current')
      return response
    } catch (error) {
      console.error('Failed to get current subscription:', error)
      return { status: 'no_subscription' }
    }
  }

  /**
   * Get all available plans from database
   */
  async getAvailablePlans(): Promise<PlanData[]> {
    try {
      const response = await apiClient.get('/api/v1/plans')
      return response.plans || this.getDefaultPlans()
    } catch (error) {
      console.error('Failed to get available plans:', error)
      return this.getDefaultPlans()
    }
  }

  /**
   * Create subscription authorization with ECPay
   */
  async createSubscriptionAuthorization(planId: string, billingCycle: string) {
    const response = await apiClient.post('/api/v1/subscriptions/authorize', {
      plan_id: planId,
      billing_cycle: billingCycle
    })
    return response
  }

  /**
   * Preview plan change with prorated billing
   */
  async previewPlanChange(planId: string, billingCycle: string) {
    const response = await apiClient.post('/api/v1/subscriptions/preview-change', {
      plan_id: planId,
      billing_cycle: billingCycle
    })
    return response
  }

  /**
   * Upgrade subscription plan
   */
  async upgradeSubscription(planId: string, billingCycle: string) {
    const response = await apiClient.post('/api/v1/subscriptions/upgrade', {
      plan_id: planId,
      billing_cycle: billingCycle
    })
    return response
  }

  /**
   * Downgrade subscription plan
   */
  async downgradeSubscription(planId: string, billingCycle: string) {
    const response = await apiClient.post('/api/v1/subscriptions/downgrade', {
      plan_id: planId,
      billing_cycle: billingCycle
    })
    return response
  }

  /**
   * Cancel subscription
   */
  async cancelSubscription(immediate: boolean = false, reason?: string) {
    const response = await apiClient.post('/api/v1/subscriptions/cancel', {
      immediate,
      reason
    })
    return response
  }

  /**
   * Reactivate cancelled subscription
   */
  async reactivateSubscription() {
    const response = await apiClient.post('/api/v1/subscriptions/reactivate')
    return response
  }

  /**
   * Get billing history
   */
  async getBillingHistory(limit: number = 20, offset: number = 0): Promise<BillingHistory> {
    try {
      const response = await apiClient.get(
        `/api/v1/subscriptions/billing-history?limit=${limit}&offset=${offset}`
      )
      return response
    } catch (error) {
      console.error('Failed to get billing history:', error)
      return { payments: [], total: 0, limit, offset }
    }
  }

  /**
   * Default plans configuration (fallback when API is unavailable)
   * This matches the database schema and ECPay pricing
   */
  private getDefaultPlans(): PlanData[] {
    return [
      {
        id: 'FREE',
        name: 'FREE',
        display_name: '免費版',
        description: '開始您的教練旅程',
        pricing: {
          monthly_twd: 0,
          annual_twd: 0,
          monthly_usd: 0,
          annual_usd: 0
        },
        features: [
          '每月 10 個會談記錄',
          '每月 5 個轉錄',
          '每月 200 分鐘轉錄額度',
          '錄音檔最長 40 分鐘',
          '最大檔案 60MB',
          '基本匯出格式',
          'Email 支援'
        ],
        limits: {
          max_sessions: 10,
          max_transcriptions: 5,
          max_total_minutes: 200,
          max_file_size_mb: 60
        },
        is_active: true,
        sort_order: 1
      },
      {
        id: 'PRO',
        name: 'PRO',
        display_name: '專業版',
        description: '專業教練的最佳選擇',
        pricing: {
          monthly_twd: 89900, // 899.00 TWD (stored in cents)
          annual_twd: 749900, // 7499.00 TWD (stored in cents) - 17% discount
          monthly_usd: 2800,  // $28.00 USD
          annual_usd: 25200   // $252.00 USD
        },
        features: [
          '每月 25 個會談記錄',
          '每月 50 個轉錄',
          '每月 300 分鐘轉錄額度',
          '錄音檔最長 90 分鐘',
          '最大檔案 200MB',
          '所有匯出格式',
          '優先 Email 支援',
          '進階分析報告',
          '自訂品牌'
        ],
        limits: {
          max_sessions: 25,
          max_transcriptions: 50,
          max_total_minutes: 300,
          max_file_size_mb: 200
        },
        is_active: true,
        sort_order: 2
      },
      {
        id: 'ENTERPRISE',
        name: 'ENTERPRISE',
        display_name: '企業版',
        description: '團隊與機構的企業解決方案',
        pricing: {
          monthly_twd: 299900, // 2999.00 TWD (stored in cents)
          annual_twd: 2499900, // 24999.00 TWD (stored in cents) - 17% discount
          monthly_usd: 9500,   // $95.00 USD
          annual_usd: 85500    // $855.00 USD
        },
        features: [
          '每月 500 個會談記錄',
          '每月 1000 個轉錄',
          '每月 1500 分鐘轉錄額度',
          '錄音檔最長 4 小時',
          '最大檔案 500MB',
          '所有匯出格式',
          '專屬客戶經理',
          '24/7 電話支援',
          '團隊協作功能',
          'API 存取權限',
          '自訂整合',
          'SLA 服務保證'
        ],
        limits: {
          max_sessions: 500,
          max_transcriptions: 1000,
          max_total_minutes: 1500,
          max_file_size_mb: 500
        },
        is_active: true,
        sort_order: 3
      }
    ]
  }

  /**
   * Format TWD currency
   */
  formatTWD(amountCents: number): string {
    return new Intl.NumberFormat('zh-TW', {
      style: 'currency',
      currency: 'TWD',
      minimumFractionDigits: 0
    }).format(amountCents / 100)
  }

  /**
   * Calculate savings percentage for annual plans
   */
  calculateAnnualSavings(monthlyPrice: number, annualPrice: number): number {
    if (monthlyPrice === 0 || annualPrice === 0) return 0
    const monthlyCost = monthlyPrice * 12
    const savings = ((monthlyCost - annualPrice) / monthlyCost) * 100
    return Math.round(savings)
  }

  /**
   * Get plan by ID
   */
  async getPlanById(planId: string): Promise<PlanData | null> {
    const plans = await this.getAvailablePlans()
    return plans.find(plan => plan.id === planId) || null
  }

  /**
   * Check if plan change is upgrade or downgrade
   */
  getPlanChangeType(currentPlanId: string, targetPlanId: string): 'upgrade' | 'downgrade' | 'same' {
    const planHierarchy: Record<string, number> = {
      'FREE': 0,
      'STUDENT': 1,
      'PRO': 2,
      'ENTERPRISE': 3
    }
    
    const currentLevel = planHierarchy[currentPlanId.toUpperCase()] || 0
    const targetLevel = planHierarchy[targetPlanId.toUpperCase()] || 0
    
    if (targetLevel > currentLevel) return 'upgrade'
    if (targetLevel < currentLevel) return 'downgrade'
    return 'same'
  }
}

export const subscriptionService = new SubscriptionService()
export default subscriptionService