# Billing Plan Limitation System - API Specification

## 📋 Overview

This document provides the complete API specification for the Billing Plan Limitation & Usage Management System, including all endpoints, request/response schemas, authentication requirements, and error handling.

## 🔐 Authentication & Authorization

All API endpoints require authentication via JWT token in the Authorization header:
```
Authorization: Bearer <jwt_token>
```

### Role-Based Access Control
- **User**: Access to own billing and usage data
- **Admin**: Access to system-wide analytics and user management
- **System**: Internal service-to-service communication

## 📊 API Endpoints

### 1. Billing Management APIs

#### GET /api/billing/plans
Get available billing plans and their features.

**Authentication**: Required (Any authenticated user)  
**Rate Limit**: 60 requests/minute

```typescript
// Response
interface PlansResponse {
  plans: {
    name: 'free' | 'pro' | 'business';
    display_name: string;
    description: string;
    tagline: string;
    features: {
      max_sessions: number | 'unlimited';
      max_total_minutes: number | 'unlimited';
      max_transcription_count: number | 'unlimited';
      max_file_size_mb: number;
      export_formats: string[];
      priority_support: boolean;
      concurrent_processing: number;
      retention_days: number | 'permanent';
    };
    pricing: {
      monthly_usd: number;
      annual_usd: number;
      annual_discount_percentage: number;
    };
    is_popular: boolean;
    color_scheme: string;
  }[];
}
```

**Example Response**:
```json
{
  "plans": [
    {
      "name": "free",
      "display_name": "Free Trial",
      "description": "Perfect for trying out the platform",
      "tagline": "Get started for free",
      "features": {
        "max_sessions": 10,
        "max_total_minutes": 120,
        "max_transcription_count": 20,
        "max_file_size_mb": 50,
        "export_formats": ["json", "txt"],
        "priority_support": false,
        "concurrent_processing": 1,
        "retention_days": 30
      },
      "pricing": {
        "monthly_usd": 0.00,
        "annual_usd": 0.00,
        "annual_discount_percentage": 0
      },
      "is_popular": false,
      "color_scheme": "gray"
    }
  ]
}
```

---

#### GET /api/billing/usage
Get current user's usage statistics and limits.

**Authentication**: Required (User)  
**Rate Limit**: 120 requests/minute

```typescript
// Response
interface UsageResponse {
  user_id: string;
  plan: 'free' | 'pro' | 'business';
  current_usage: {
    sessions: number;
    minutes: number;
    transcriptions: number;
  };
  plan_limits: {
    max_sessions: number | 'unlimited';
    max_minutes: number | 'unlimited';
    max_transcriptions: number | 'unlimited';
    max_file_size_mb: number;
    export_formats: string[];
    concurrent_processing: number;
  };
  usage_percentages: {
    sessions: number | null;
    minutes: number | null;
    transcriptions: number | null;
  };
  approaching_limits: {
    sessions: boolean;
    minutes: boolean;
    transcriptions: boolean;
  };
  subscription_info: {
    start_date: string | null;
    end_date: string | null;
    active: boolean;
    days_until_reset: number;
  };
}
```

**Example Response**:
```json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "plan": "free",
  "current_usage": {
    "sessions": 8,
    "minutes": 95,
    "transcriptions": 15
  },
  "plan_limits": {
    "max_sessions": 10,
    "max_minutes": 120,
    "max_transcriptions": 20,
    "max_file_size_mb": 50,
    "export_formats": ["json", "txt"],
    "concurrent_processing": 1
  },
  "usage_percentages": {
    "sessions": 80.0,
    "minutes": 79.2,
    "transcriptions": 75.0
  },
  "approaching_limits": {
    "sessions": true,
    "minutes": false,
    "transcriptions": false
  },
  "subscription_info": {
    "start_date": "2025-08-01T00:00:00Z",
    "end_date": null,
    "active": true,
    "days_until_reset": 12
  }
}
```

---

#### GET /api/billing/usage/history
Get user's usage history.

**Authentication**: Required (User)  
**Rate Limit**: 30 requests/minute

**Query Parameters**:
- `months` (optional): Number of months to retrieve (default: 3, max: 12)

```typescript
// Response
interface UsageHistoryResponse {
  user_id: string;
  months_requested: number;
  usage_history: {
    id: string;
    session_id: string;
    transcription_type: 'original' | 'retry_failed' | 'retry_success';
    duration_minutes: number;
    cost_usd: number;
    is_billable: boolean;
    billing_reason: string;
    stt_provider: 'google' | 'assemblyai';
    user_plan: string;
    created_at: string;
    billing_description: string;
  }[];
}
```

---

#### POST /api/billing/upgrade
Upgrade user's plan.

**Authentication**: Required (User)  
**Rate Limit**: 10 requests/hour

```typescript
// Request
interface UpgradeRequest {
  plan: 'pro' | 'business';
  payment_method?: string; // Stripe payment method ID
  billing_cycle?: 'monthly' | 'annual';
}

// Response
interface UpgradeResponse {
  message: string;
  user_id: string;
  new_plan: string;
  transaction: {
    id: string;
    amount: number;
    prorated_amount?: number;
    effective_date: string;
    next_billing_date: string;
  };
  stripe: {
    client_secret?: string;
    subscription_id: string;
  };
}
```

**Example Request**:
```json
{
  "plan": "pro",
  "payment_method": "pm_1234567890abcdef",
  "billing_cycle": "monthly"
}
```

**Error Responses**:
```json
// 400 Bad Request
{
  "error": "invalid_plan",
  "message": "Invalid plan. Choose 'pro' or 'business'",
  "details": {
    "available_plans": ["pro", "business"]
  }
}

// 402 Payment Required
{
  "error": "payment_failed",
  "message": "Payment method declined",
  "details": {
    "stripe_error": "Your card was declined."
  }
}
```

---

#### POST /api/billing/downgrade
Downgrade user's plan.

**Authentication**: Required (User)  
**Rate Limit**: 5 requests/hour

```typescript
// Request
interface DowngradeRequest {
  plan: 'free' | 'pro';
  reason?: string;
  effective_immediately?: boolean;
}

// Response
interface DowngradeResponse {
  message: string;
  user_id: string;
  new_plan: string;
  effective_date: string;
  current_plan_expires?: string;
  refund_amount?: number;
}
```

---

#### GET /api/billing/limits/check
Check if user can perform specific action against plan limits.

**Authentication**: Required (User)  
**Rate Limit**: 300 requests/minute

**Query Parameters**:
- `action`: 'create_session' | 'transcribe' | 'export' | 'upload'
- `format` (optional): Export format for validation
- `file_size` (optional): File size in bytes for validation

```typescript
// Response
interface LimitsCheckResponse {
  allowed: boolean;
  message: string;
  limit_exceeded?: {
    type: string;
    current_usage: number | string;
    plan_limit: number | string;
    suggested_plan?: string;
  };
  suggestions?: {
    upgrade_plan?: string;
    wait_until_reset?: string;
    alternative_actions?: string[];
  };
}
```

**Example Responses**:
```json
// Success
{
  "allowed": true,
  "message": "Action is allowed"
}

// Limit exceeded
{
  "allowed": false,
  "message": "Session limit exceeded. Upgrade to continue.",
  "limit_exceeded": {
    "type": "max_sessions",
    "current_usage": 10,
    "plan_limit": 10,
    "suggested_plan": "pro"
  },
  "suggestions": {
    "upgrade_plan": "pro",
    "wait_until_reset": "2025-09-01T00:00:00Z"
  }
}
```

---

### 2. Session Integration APIs

#### POST /api/sessions
Create new session with plan validation.

**Authentication**: Required (User)  
**Rate Limit**: 60 requests/minute

```typescript
// Request (Enhanced)
interface CreateSessionRequest {
  title: string;
  language?: string;
  stt_provider?: 'google' | 'assemblyai' | 'auto';
  client_id?: string;
  // Plan validation will be performed automatically
}

// Response (Enhanced)
interface CreateSessionResponse {
  session_id: string;
  title: string;
  status: 'uploading';
  plan_validation: {
    passed: boolean;
    usage_after_creation: {
      sessions: number;
      sessions_limit: number | 'unlimited';
    };
  };
  // ... existing session fields
}
```

**Error Response for Plan Limits**:
```json
{
  "error": "plan_limit_exceeded",
  "message": "Session limit exceeded for Free plan",
  "details": {
    "limit_type": "max_sessions",
    "current_usage": 10,
    "plan_limit": 10,
    "suggested_plan": "pro"
  },
  "upgrade_url": "/billing/upgrade"
}
```

---

#### POST /api/sessions/{session_id}/retranscribe
Re-transcribe a completed session (paid service).

**Authentication**: Required (User)  
**Rate Limit**: 20 requests/hour

```typescript
// Request
interface RetranscribeRequest {
  confirm_cost: boolean;
  enable_diarization?: boolean;
  stt_provider?: 'google' | 'assemblyai';
}

// Response
interface RetranscribeResponse {
  message: string;
  task_id: string;
  session_id: string;
  estimated_cost: number;
  transcription_type: 're-transcription';
  billing_info: {
    is_billable: true;
    billing_reason: 'retranscription_service';
    cost_estimate: number;
    requires_confirmation: boolean;
  };
}
```

**Cost Estimation Response** (when confirm_cost = false):
```json
{
  "message": "Cost confirmation required for re-transcription",
  "cost_estimate": 0.05,
  "billing_reason": "retranscription_service",
  "requires_confirmation": true,
  "session_info": {
    "duration_minutes": 5,
    "original_cost": 0.04,
    "stt_provider": "google"
  }
}
```

---

#### GET /api/sessions/{session_id}/billing
Get detailed billing information for a session.

**Authentication**: Required (User, owns session)  
**Rate Limit**: 60 requests/minute

```typescript
// Response
interface SessionBillingResponse {
  session_id: string;
  session_status: 'completed' | 'failed' | 'processing';
  billing_summary: {
    total_cost: number;
    billable_attempts: number;
    free_retries: number;
    total_attempts: number;
  };
  transcription_history: {
    attempt_number: number;
    transcription_type: 'original' | 'retry_failed' | 'retry_success';
    cost: number;
    is_billable: boolean;
    billing_reason: string;
    created_at: string;
    duration_minutes: number;
    stt_provider: string;
  }[];
  plan_context: {
    user_plan: string;
    plan_limits: object;
  };
}
```

---

### 3. Admin Management APIs

#### GET /api/admin/billing/analytics
Get system-wide billing analytics.

**Authentication**: Required (Admin)  
**Rate Limit**: 30 requests/minute

**Query Parameters**:
- `months` (optional): Number of months (default: 3, max: 24)
- `plan` (optional): Filter by specific plan
- `metric` (optional): Specific metric to focus on

```typescript
// Response
interface AdminBillingAnalyticsResponse {
  time_period: {
    months: number;
    start_date: string;
    end_date: string;
  };
  summary: {
    total_users: number;
    active_subscriptions: number;
    total_revenue_usd: number;
    total_transcriptions: number;
    total_minutes_processed: number;
  };
  plan_distribution: {
    [plan: string]: {
      user_count: number;
      percentage: number;
      revenue_usd: number;
    };
  };
  conversion_metrics: {
    free_to_paid_rate: number;
    upgrade_rate: number;
    churn_rate: number;
    average_time_to_convert_days: number;
  };
  usage_patterns: {
    avg_sessions_per_user: number;
    avg_minutes_per_session: number;
    peak_usage_hours: number[];
    seasonal_trends: {
      month: string;
      transcriptions: number;
      revenue: number;
    }[];
  };
  financial_metrics: {
    monthly_recurring_revenue: number;
    annual_run_rate: number;
    average_revenue_per_user: number;
    customer_lifetime_value: number;
  };
}
```

---

#### GET /api/admin/users/{user_id}/billing
Get detailed billing information for specific user.

**Authentication**: Required (Admin)  
**Rate Limit**: 60 requests/minute

```typescript
// Response
interface AdminUserBillingResponse {
  user_id: string;
  user_info: {
    email: string;
    name: string;
    created_at: string;
  };
  current_plan: {
    plan: string;
    subscription_start: string;
    subscription_end?: string;
    subscription_active: boolean;
    stripe_subscription_id?: string;
  };
  usage_summary: {
    current_month: {
      sessions: number;
      minutes: number;
      transcriptions: number;
    };
    all_time: {
      total_sessions: number;
      total_minutes: number;
      total_cost: number;
    };
  };
  subscription_history: {
    id: string;
    old_plan?: string;
    new_plan: string;
    change_type: string;
    amount_usd: number;
    effective_date: string;
    change_reason?: string;
  }[];
  payment_history: {
    invoice_id: string;
    amount: number;
    status: string;
    created_at: string;
    description: string;
  }[];
}
```

---

#### POST /api/admin/users/{user_id}/plan
Change user's plan (Admin only).

**Authentication**: Required (Admin)  
**Rate Limit**: 10 requests/hour

```typescript
// Request
interface AdminChangePlanRequest {
  new_plan: 'free' | 'pro' | 'business';
  reason: string;
  effective_immediately?: boolean;
  send_notification?: boolean;
}

// Response
interface AdminChangePlanResponse {
  message: string;
  user_id: string;
  old_plan: string;
  new_plan: string;
  changed_by: string;
  effective_date: string;
  subscription_history_id: string;
}
```

---

### 4. Analytics & Reporting APIs

#### GET /api/billing/reports/usage
Generate usage report for user.

**Authentication**: Required (User)  
**Rate Limit**: 10 requests/hour

**Query Parameters**:
- `start_date`: Start date (ISO 8601)
- `end_date`: End date (ISO 8601)
- `format`: 'json' | 'csv' | 'xlsx'

```typescript
// Response (JSON format)
interface UsageReportResponse {
  report_info: {
    user_id: string;
    generated_at: string;
    period: {
      start_date: string;
      end_date: string;
    };
    format: string;
  };
  summary: {
    total_sessions: number;
    total_minutes: number;
    total_cost: number;
    avg_session_duration: number;
  };
  detailed_usage: {
    date: string;
    sessions: number;
    minutes: number;
    cost: number;
    transcription_breakdown: {
      original: number;
      retries: number;
      retranscriptions: number;
    };
  }[];
  plan_history: {
    plan: string;
    start_date: string;
    end_date?: string;
    days_active: number;
  }[];
}
```

---

## 🔒 Error Handling

### Standard Error Response Format
```typescript
interface ErrorResponse {
  error: string;
  message: string;
  details?: object;
  timestamp: string;
  request_id: string;
  suggestions?: {
    action: string;
    url?: string;
    message: string;
  }[];
}
```

### Plan Limit Error Response
```typescript
interface PlanLimitErrorResponse extends ErrorResponse {
  error: 'plan_limit_exceeded';
  details: {
    limit_type: string;
    current_usage: number | string;
    plan_limit: number | string;
    suggested_plan?: string;
    reset_date?: string;
  };
  suggestions: {
    action: 'upgrade_plan' | 'wait_for_reset' | 'delete_old_sessions';
    url?: string;
    message: string;
  }[];
}
```

### Common Error Codes

| HTTP Status | Error Code | Description |
|-------------|------------|-------------|
| 400 | `invalid_plan` | Invalid plan specified |
| 400 | `invalid_billing_cycle` | Invalid billing cycle |
| 401 | `authentication_required` | JWT token missing or invalid |
| 402 | `plan_limit_exceeded` | User has exceeded plan limits |
| 402 | `payment_required` | Payment method required for upgrade |
| 403 | `insufficient_permissions` | Admin access required |
| 404 | `session_not_found` | Session doesn't exist or not accessible |
| 409 | `subscription_conflict` | Conflicting subscription state |
| 422 | `validation_error` | Request validation failed |
| 429 | `rate_limit_exceeded` | Too many requests |
| 500 | `internal_error` | Internal server error |
| 502 | `payment_service_error` | Stripe/payment service error |
| 503 | `service_unavailable` | Temporary service unavailable |

---

## 🎯 Rate Limiting

### Rate Limit Headers
All API responses include rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 59
X-RateLimit-Reset: 1692901200
X-RateLimit-Window: 60
```

### Rate Limit Tiers by Plan
| Plan | Tier | Requests/Minute | Burst Limit |
|------|------|-----------------|-------------|
| Free | Basic | 60 | 100 |
| Pro | Standard | 120 | 200 |
| Business | Premium | 300 | 500 |

---

## 📊 Webhook Events

### Stripe Webhook Events
The system listens for the following Stripe webhook events:

#### invoice.payment_succeeded
```json
{
  "event_type": "invoice.payment_succeeded",
  "data": {
    "customer_id": "cus_1234567890",
    "subscription_id": "sub_1234567890",
    "amount_paid": 2999,
    "currency": "usd",
    "period_start": 1692901200,
    "period_end": 1695579600
  }
}
```

#### invoice.payment_failed
```json
{
  "event_type": "invoice.payment_failed",
  "data": {
    "customer_id": "cus_1234567890",
    "subscription_id": "sub_1234567890",
    "amount_due": 2999,
    "attempt_count": 1,
    "next_payment_attempt": 1692987600
  }
}
```

#### customer.subscription.updated
```json
{
  "event_type": "customer.subscription.updated",
  "data": {
    "customer_id": "cus_1234567890",
    "subscription_id": "sub_1234567890",
    "status": "active",
    "current_period_start": 1692901200,
    "current_period_end": 1695579600,
    "plan": {
      "id": "price_1234567890",
      "nickname": "Pro Monthly"
    }
  }
}
```

---

## 🔧 SDK Examples

### JavaScript/TypeScript SDK
```typescript
import { BillingClient } from '@coaching-assistant/sdk';

const client = new BillingClient({
  apiKey: process.env.API_KEY,
  baseUrl: 'https://api.coaching-assistant.com'
});

// Get usage information
const usage = await client.billing.getUsage();
console.log(`Usage: ${usage.current_usage.sessions}/${usage.plan_limits.max_sessions}`);

// Check limits before action
const canCreateSession = await client.billing.checkLimits({
  action: 'create_session'
});

if (!canCreateSession.allowed) {
  // Show upgrade prompt
  console.log(canCreateSession.message);
  console.log(`Suggested plan: ${canCreateSession.limit_exceeded?.suggested_plan}`);
}

// Upgrade plan
try {
  const upgrade = await client.billing.upgrade({
    plan: 'pro',
    payment_method: 'pm_1234567890'
  });
  console.log(`Successfully upgraded to ${upgrade.new_plan}`);
} catch (error) {
  console.error('Upgrade failed:', error.message);
}
```

### Python SDK
```python
from coaching_assistant_sdk import BillingClient

client = BillingClient(
    api_key=os.getenv('API_KEY'),
    base_url='https://api.coaching-assistant.com'
)

# Get usage information
usage = client.billing.get_usage()
print(f"Usage: {usage['current_usage']['sessions']}/{usage['plan_limits']['max_sessions']}")

# Check limits
limits = client.billing.check_limits(action='create_session')
if not limits['allowed']:
    print(f"Limit exceeded: {limits['message']}")
    if limits.get('limit_exceeded', {}).get('suggested_plan'):
        print(f"Consider upgrading to: {limits['limit_exceeded']['suggested_plan']}")

# Upgrade plan
try:
    upgrade = client.billing.upgrade(
        plan='pro',
        payment_method='pm_1234567890'
    )
    print(f"Successfully upgraded to {upgrade['new_plan']}")
except BillingError as e:
    print(f"Upgrade failed: {e.message}")
```

---

**Document Owner**: API Architecture Team  
**Last Updated**: August 14, 2025  
**API Version**: v1.0  
**OpenAPI Spec**: Available at `/api/docs`