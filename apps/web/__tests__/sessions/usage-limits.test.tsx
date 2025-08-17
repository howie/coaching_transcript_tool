import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { useRouter } from 'next/navigation';
import SessionDetailPage from '@/app/dashboard/sessions/[id]/page';
import { usePlanLimits } from '@/hooks/usePlanLimits';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';

// Mock the modules
jest.mock('next/navigation', () => ({
  useRouter: jest.fn(),
  useParams: jest.fn(() => ({ id: 'test-session-id' }))
}));

jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn()
}));

jest.mock('@/contexts/i18n-context', () => ({
  useI18n: jest.fn()
}));

jest.mock('@/hooks/usePlanLimits', () => ({
  usePlanLimits: jest.fn()
}));

jest.mock('@/lib/api', () => ({
  apiClient: {
    getSession: jest.fn(),
    getClients: jest.fn(() => Promise.resolve({ items: [] })),
    getCurrencies: jest.fn(() => Promise.resolve([
      { value: 'TWD', label: 'TWD - 新台幣' },
      { value: 'USD', label: 'USD - 美元' }
    ]))
  }
}));

jest.mock('@/hooks/useTranscriptionStatus', () => ({
  useTranscriptionStatus: jest.fn(() => ({
    status: null,
    session: null,
    loading: false,
    error: null,
    startPolling: jest.fn(),
    stopPolling: jest.fn(),
    isPolling: false,
    refetch: jest.fn()
  })),
  formatTimeRemaining: jest.fn(),
  formatDuration: jest.fn()
}));

describe('Session Detail Usage Limits', () => {
  const mockRouter = {
    push: jest.fn(),
    back: jest.fn()
  };

  const mockT = (key: string) => {
    const translations: Record<string, string> = {
      'limits.usageLimitReached': '使用量已達上限',
      'limits.sessionLimitReached': '您本月的會談數已達到方案上限',
      'limits.transcriptionLimitReached': '您本月的轉錄數已達到方案上限',
      'limits.minutesLimitReached': '您本月的音檔分鐘數已達到方案上限',
      'limits.sessions': '會談數',
      'limits.transcriptions': '轉錄數',
      'limits.minutes': '音檔分鐘數',
      'limits.upgradeNow': '立即升級',
      'limits.viewUsage': '查看使用量',
      'sessions.sessionDetail': '會談詳情',
      'sessions.loading': '載入中...',
      'common.back': '返回',
      'common.edit': '編輯',
      'common.delete': '刪除'
    };
    return translations[key] || key;
  };

  beforeEach(() => {
    (useRouter as jest.Mock).mockReturnValue(mockRouter);
    (useAuth as jest.Mock).mockReturnValue({
      user: { name: 'Test User' },
      logout: jest.fn()
    });
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should show limit message when session limit is reached', async () => {
    // Mock plan limits hook to return session limit reached
    (usePlanLimits as jest.Mock).mockReturnValue({
      canCreateSession: jest.fn().mockResolvedValue(false),
      canTranscribe: jest.fn().mockResolvedValue(true),
      validateAction: jest.fn().mockResolvedValue({
        allowed: false,
        limitInfo: { current: 10, limit: 10 }
      }),
      checkBeforeAction: jest.fn()
    });

    // Mock API response for session data
    const { apiClient } = require('@/lib/api');
    apiClient.getSession.mockResolvedValue({
      id: 'test-session-id',
      session_date: '2024-01-01',
      client_id: 'client-1',
      duration_min: 60,
      fee_currency: 'TWD',
      fee_amount: 1000,
      fee_display: 'TWD 1,000',
      duration_display: '60 分鐘'
    });

    render(<SessionDetailPage />);

    // Wait for the component to load and check limits
    await waitFor(() => {
      expect(screen.getByText('使用量已達上限')).toBeInTheDocument();
    });

    // Check if the limit details are shown
    expect(screen.getByText('10 / 10')).toBeInTheDocument();
    expect(screen.getByText('立即升級')).toBeInTheDocument();
    expect(screen.getByText('查看使用量')).toBeInTheDocument();
  });

  it('should navigate to billing page when upgrade button is clicked', async () => {
    // Mock plan limits hook to return limit reached
    (usePlanLimits as jest.Mock).mockReturnValue({
      canCreateSession: jest.fn().mockResolvedValue(false),
      canTranscribe: jest.fn().mockResolvedValue(true),
      validateAction: jest.fn().mockResolvedValue({
        allowed: false,
        limitInfo: { current: 10, limit: 10 }
      }),
      checkBeforeAction: jest.fn()
    });

    // Mock API response
    const { apiClient } = require('@/lib/api');
    apiClient.getSession.mockResolvedValue({
      id: 'test-session-id',
      session_date: '2024-01-01',
      client_id: 'client-1',
      duration_min: 60,
      fee_currency: 'TWD',
      fee_amount: 1000,
      fee_display: 'TWD 1,000',
      duration_display: '60 分鐘'
    });

    render(<SessionDetailPage />);

    // Wait for the limit message to appear
    await waitFor(() => {
      expect(screen.getByText('使用量已達上限')).toBeInTheDocument();
    });

    // Click the upgrade button
    const upgradeButton = screen.getByText('立即升級');
    fireEvent.click(upgradeButton);

    // Verify navigation to billing page with plans tab
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/billing?tab=plans');
  });

  it('should show transcription limit message when transcription limit is reached', async () => {
    // Mock plan limits hook to return transcription limit reached
    (usePlanLimits as jest.Mock).mockReturnValue({
      canCreateSession: jest.fn().mockResolvedValue(true),
      canTranscribe: jest.fn().mockResolvedValue(false),
      validateAction: jest.fn().mockResolvedValue({
        allowed: false,
        limitInfo: { current: 20, limit: 20 }
      }),
      checkBeforeAction: jest.fn()
    });

    // Mock API response
    const { apiClient } = require('@/lib/api');
    apiClient.getSession.mockResolvedValue({
      id: 'test-session-id',
      session_date: '2024-01-01',
      client_id: 'client-1',
      duration_min: 60,
      fee_currency: 'TWD',
      fee_amount: 1000,
      fee_display: 'TWD 1,000',
      duration_display: '60 分鐘'
    });

    render(<SessionDetailPage />);

    // Wait for the component to load and check limits
    await waitFor(() => {
      expect(screen.getByText('使用量已達上限')).toBeInTheDocument();
    });

    // Check if transcription limit message is shown
    expect(screen.getByText('您本月的轉錄數已達到方案上限')).toBeInTheDocument();
  });

  it('should allow audio upload when no limits are reached', async () => {
    // Mock plan limits hook to return all limits OK
    (usePlanLimits as jest.Mock).mockReturnValue({
      canCreateSession: jest.fn().mockResolvedValue(true),
      canTranscribe: jest.fn().mockResolvedValue(true),
      validateAction: jest.fn().mockResolvedValue({
        allowed: true
      }),
      checkBeforeAction: jest.fn((action, callback) => callback())
    });

    // Mock API response
    const { apiClient } = require('@/lib/api');
    apiClient.getSession.mockResolvedValue({
      id: 'test-session-id',
      session_date: '2024-01-01',
      client_id: 'client-1',
      duration_min: 60,
      fee_currency: 'TWD',
      fee_amount: 1000,
      fee_display: 'TWD 1,000',
      duration_display: '60 分鐘'
    });

    render(<SessionDetailPage />);

    // Wait for component to load
    await waitFor(() => {
      expect(screen.queryByText('會談詳情')).toBeInTheDocument();
    });

    // Check that limit warning is NOT shown
    expect(screen.queryByText('使用量已達上限')).not.toBeInTheDocument();
  });

  it('should navigate to usage overview when view usage button is clicked', async () => {
    // Mock plan limits hook to return limit reached
    (usePlanLimits as jest.Mock).mockReturnValue({
      canCreateSession: jest.fn().mockResolvedValue(false),
      canTranscribe: jest.fn().mockResolvedValue(true),
      validateAction: jest.fn().mockResolvedValue({
        allowed: false,
        limitInfo: { current: 10, limit: 10 }
      }),
      checkBeforeAction: jest.fn()
    });

    // Mock API response
    const { apiClient } = require('@/lib/api');
    apiClient.getSession.mockResolvedValue({
      id: 'test-session-id',
      session_date: '2024-01-01',
      client_id: 'client-1',
      duration_min: 60,
      fee_currency: 'TWD',
      fee_amount: 1000,
      fee_display: 'TWD 1,000',
      duration_display: '60 分鐘'
    });

    render(<SessionDetailPage />);

    // Wait for the limit message to appear
    await waitFor(() => {
      expect(screen.getByText('使用量已達上限')).toBeInTheDocument();
    });

    // Click the view usage button
    const viewUsageButton = screen.getByText('查看使用量');
    fireEvent.click(viewUsageButton);

    // Verify navigation to billing overview page
    expect(mockRouter.push).toHaveBeenCalledWith('/dashboard/billing?tab=overview');
  });
});