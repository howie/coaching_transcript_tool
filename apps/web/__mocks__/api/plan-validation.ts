/**
 * Mock API implementation for plan validation testing
 * This can be used for development and testing before backend is ready
 */

export interface ValidationRequest {
  action: 'create_session' | 'transcribe' | 'check_minutes' | 'upload_file' | 'export_transcript';
  params?: {
    file_size_mb?: number;
    duration_min?: number;
    format?: string;
  };
}

export interface LimitInfo {
  type: 'sessions' | 'transcriptions' | 'minutes' | 'file_size' | 'exports';
  current: number;
  limit: number;
  reset_date: string;
}

export interface ValidationResponse {
  allowed: boolean;
  message?: string;
  limit_info?: LimitInfo;
  upgrade_suggestion?: {
    plan_id: string;
    display_name: string;
    benefits: string[];
  };
}

// Mock user data storage
const mockUserData = new Map<string, {
  plan: 'FREE' | 'PRO' | 'ENTERPRISE';
  session_count: number;
  transcription_count: number;
  usage_minutes: number;
}>();

// Plan limits configuration
const PLAN_LIMITS = {
  FREE: {
    sessions: 10,
    transcriptions: 20,
    minutes: 120,
    file_size_mb: 100,
    exports_per_month: 5
  },
  PRO: {
    sessions: 100,
    transcriptions: 200,
    minutes: 1200,
    file_size_mb: 500,
    exports_per_month: 50
  },
  ENTERPRISE: {
    sessions: -1, // Unlimited
    transcriptions: -1,
    minutes: -1,
    file_size_mb: 2000,
    exports_per_month: -1
  }
};

/**
 * Mock validation function that simulates backend behavior
 */
export async function mockValidateAction(
  userId: string,
  request: ValidationRequest
): Promise<ValidationResponse> {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 100));

  // Get or create user data
  let userData = mockUserData.get(userId);
  if (!userData) {
    userData = {
      plan: 'FREE',
      session_count: 0,
      transcription_count: 0,
      usage_minutes: 0
    };
    mockUserData.set(userId, userData);
  }

  const limits = PLAN_LIMITS[userData.plan];
  const resetDate = getNextMonthFirstDay();

  switch (request.action) {
    case 'create_session': {
      const allowed = limits.sessions === -1 || userData.session_count < limits.sessions;
      return {
        allowed,
        message: allowed ? undefined : 'You have reached your monthly session limit',
        limit_info: {
          type: 'sessions',
          current: userData.session_count,
          limit: limits.sessions,
          reset_date: resetDate
        },
        upgrade_suggestion: !allowed && userData.plan !== 'ENTERPRISE' ? {
          plan_id: userData.plan === 'FREE' ? 'PRO' : 'ENTERPRISE',
          display_name: userData.plan === 'FREE' ? 'Pro Plan' : 'Enterprise Plan',
          benefits: userData.plan === 'FREE' 
            ? ['100 sessions/month', '1200 minutes/month', '200 transcriptions/month']
            : ['Unlimited sessions', 'Unlimited minutes', 'Unlimited transcriptions']
        } : undefined
      };
    }

    case 'transcribe': {
      const allowed = limits.transcriptions === -1 || userData.transcription_count < limits.transcriptions;
      return {
        allowed,
        message: allowed ? undefined : 'You have reached your monthly transcription limit',
        limit_info: {
          type: 'transcriptions',
          current: userData.transcription_count,
          limit: limits.transcriptions,
          reset_date: resetDate
        },
        upgrade_suggestion: !allowed && userData.plan !== 'ENTERPRISE' ? {
          plan_id: userData.plan === 'FREE' ? 'PRO' : 'ENTERPRISE',
          display_name: userData.plan === 'FREE' ? 'Pro Plan' : 'Enterprise Plan',
          benefits: userData.plan === 'FREE'
            ? ['200 transcriptions/month', 'Advanced features', 'Priority support']
            : ['Unlimited transcriptions', 'Custom integrations', 'Dedicated support']
        } : undefined
      };
    }

    case 'check_minutes': {
      const requestedMinutes = request.params?.duration_min || 0;
      const projectedUsage = userData.usage_minutes + requestedMinutes;
      const allowed = limits.minutes === -1 || projectedUsage <= limits.minutes;
      
      return {
        allowed,
        message: allowed ? undefined : 'You have reached your monthly audio minutes limit',
        limit_info: {
          type: 'minutes',
          current: userData.usage_minutes,
          limit: limits.minutes,
          reset_date: resetDate
        },
        upgrade_suggestion: !allowed && userData.plan !== 'ENTERPRISE' ? {
          plan_id: userData.plan === 'FREE' ? 'PRO' : 'ENTERPRISE',
          display_name: userData.plan === 'FREE' ? 'Pro Plan' : 'Enterprise Plan',
          benefits: userData.plan === 'FREE'
            ? ['1200 minutes/month (20 hours)', 'Faster processing', 'Higher quality']
            : ['Unlimited minutes', 'Bulk processing', 'API access']
        } : undefined
      };
    }

    case 'upload_file': {
      const fileSizeMb = request.params?.file_size_mb || 0;
      const allowed = fileSizeMb <= limits.file_size_mb;
      
      return {
        allowed,
        message: allowed ? undefined : `File size exceeds your plan limit of ${limits.file_size_mb}MB`,
        limit_info: {
          type: 'file_size',
          current: fileSizeMb,
          limit: limits.file_size_mb,
          reset_date: resetDate
        },
        upgrade_suggestion: !allowed && userData.plan !== 'ENTERPRISE' ? {
          plan_id: userData.plan === 'FREE' ? 'PRO' : 'ENTERPRISE',
          display_name: userData.plan === 'FREE' ? 'Pro Plan' : 'Enterprise Plan',
          benefits: userData.plan === 'FREE'
            ? ['500MB file size limit', 'Batch uploads', 'Cloud storage']
            : ['2GB file size limit', 'Unlimited storage', 'Direct API upload']
        } : undefined
      };
    }

    case 'export_transcript': {
      // For simplicity, using session count as export count
      const exportCount = userData.session_count;
      const allowed = limits.exports_per_month === -1 || exportCount < limits.exports_per_month;
      
      return {
        allowed,
        message: allowed ? undefined : 'You have reached your monthly export limit',
        limit_info: {
          type: 'exports',
          current: exportCount,
          limit: limits.exports_per_month,
          reset_date: resetDate
        },
        upgrade_suggestion: !allowed && userData.plan !== 'ENTERPRISE' ? {
          plan_id: userData.plan === 'FREE' ? 'PRO' : 'ENTERPRISE',
          display_name: userData.plan === 'FREE' ? 'Pro Plan' : 'Enterprise Plan',
          benefits: userData.plan === 'FREE'
            ? ['50 exports/month', 'Multiple formats', 'Bulk export']
            : ['Unlimited exports', 'Custom formats', 'Automated exports']
        } : undefined
      };
    }

    default:
      throw new Error(`Unknown action: ${request.action}`);
  }
}

/**
 * Helper function to update mock user data (for testing)
 */
export function updateMockUserData(
  userId: string,
  updates: Partial<{
    plan: 'FREE' | 'PRO' | 'ENTERPRISE';
    session_count: number;
    transcription_count: number;
    usage_minutes: number;
  }>
) {
  const current = mockUserData.get(userId) || {
    plan: 'FREE' as const,
    session_count: 0,
    transcription_count: 0,
    usage_minutes: 0
  };
  
  mockUserData.set(userId, { ...current, ...updates });
}

/**
 * Helper function to reset mock user data (for testing)
 */
export function resetMockUserData(userId?: string) {
  if (userId) {
    mockUserData.delete(userId);
  } else {
    mockUserData.clear();
  }
}

/**
 * Get the first day of next month
 */
function getNextMonthFirstDay(): string {
  const now = new Date();
  const nextMonth = new Date(now.getFullYear(), now.getMonth() + 1, 1);
  return nextMonth.toISOString();
}

/**
 * Simulate incrementing usage (for testing)
 */
export function incrementUsage(
  userId: string,
  metric: 'session_count' | 'transcription_count' | 'usage_minutes',
  amount: number = 1
) {
  const userData = mockUserData.get(userId);
  if (userData) {
    userData[metric] += amount;
    mockUserData.set(userId, userData);
  }
}

/**
 * Get current usage for a user (for testing)
 */
export function getCurrentUsage(userId: string) {
  return mockUserData.get(userId) || {
    plan: 'FREE',
    session_count: 0,
    transcription_count: 0,
    usage_minutes: 0
  };
}

// Export for use in tests and development
export default {
  mockValidateAction,
  updateMockUserData,
  resetMockUserData,
  incrementUsage,
  getCurrentUsage,
  PLAN_LIMITS
};