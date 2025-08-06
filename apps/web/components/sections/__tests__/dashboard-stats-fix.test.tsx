import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import { DashboardStats } from '../dashboard-stats';
import { useAuth } from '@/contexts/auth-context';
import { useI18n } from '@/contexts/i18n-context';
import { apiClient } from '@/lib/api';

// Mock modules
jest.mock('@/contexts/auth-context', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/contexts/i18n-context', () => ({
  useI18n: jest.fn(),
}));

jest.mock('@/lib/api', () => ({
  apiClient: {
    getSummary: jest.fn(),
  },
}));

describe('DashboardStats ApiClient Fix', () => {
  const mockUser = { id: 'user-123', email: 'test@example.com' };
  const mockT = (key: string) => {
    const translations: Record<string, string> = {
      'dashboard.stats.total_hours': 'Total Hours',
      'dashboard.stats.monthly_hours': 'Monthly Hours', 
      'dashboard.stats.transcripts': 'Transcripts',
      'dashboard.stats.total_clients': 'Total Clients',
      'dashboard.stats.monthly_revenue': 'Monthly Revenue',
    };
    return translations[key] || key;
  };

  const mockSummaryData = {
    total_minutes: 3600, // 60 hours
    current_month_minutes: 1800, // 30 hours
    transcripts_converted_count: 25,
    current_month_revenue_by_currency: { NTD: 50000, USD: 1000 },
    unique_clients_total: 15,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    (useAuth as jest.Mock).mockReturnValue({ user: mockUser });
    (useI18n as jest.Mock).mockReturnValue({ t: mockT });
    (apiClient.getSummary as jest.Mock).mockResolvedValue(mockSummaryData);
  });

  it('should successfully load and display summary data using apiClient', async () => {
    render(<DashboardStats />);

    // Initially shows loading
    expect(screen.getAllByText('...')).toHaveLength(4);

    await waitFor(() => {
      expect(apiClient.getSummary).toHaveBeenCalled();
      
      // Check that all stats are displayed correctly
      expect(screen.getByText('60')).toBeInTheDocument(); // total_minutes / 60
      expect(screen.getByText('30')).toBeInTheDocument(); // current_month_minutes / 60
      expect(screen.getByText('25')).toBeInTheDocument(); // transcripts_converted_count
      expect(screen.getByText('15')).toBeInTheDocument(); // unique_clients_total
      
      // Check revenue display
      expect(screen.getByText('NTD 50,000, USD 1,000')).toBeInTheDocument();
    });

    // Verify labels are correct
    expect(screen.getByText('Total Hours')).toBeInTheDocument();
    expect(screen.getByText('Monthly Hours')).toBeInTheDocument();
    expect(screen.getByText('Transcripts')).toBeInTheDocument();
    expect(screen.getByText('Total Clients')).toBeInTheDocument();
    expect(screen.getByText('Monthly Revenue')).toBeInTheDocument();
  });

  it('should handle API errors gracefully', async () => {
    (apiClient.getSummary as jest.Mock).mockRejectedValue(new Error('API Error'));

    render(<DashboardStats />);

    await waitFor(() => {
      // Should show zeros when API fails
      expect(screen.getAllByText('0')).toHaveLength(4);
    });
  });

  it('should not fetch data when user is not present', () => {
    (useAuth as jest.Mock).mockReturnValue({ user: null });

    render(<DashboardStats />);

    expect(apiClient.getSummary).not.toHaveBeenCalled();
  });

  it('should handle summary data without revenue', async () => {
    const summaryDataWithoutRevenue = {
      ...mockSummaryData,
      current_month_revenue_by_currency: {},
    };
    (apiClient.getSummary as jest.Mock).mockResolvedValue(summaryDataWithoutRevenue);

    render(<DashboardStats />);

    await waitFor(() => {
      // Should show 4 stats (no revenue card)
      expect(screen.getByText('60')).toBeInTheDocument();
      expect(screen.getByText('30')).toBeInTheDocument(); 
      expect(screen.getByText('25')).toBeInTheDocument();
      expect(screen.getByText('15')).toBeInTheDocument();
      
      // Should not show revenue
      expect(screen.queryByText('Monthly Revenue')).not.toBeInTheDocument();
    });
  });

  it('should format single currency revenue correctly', async () => {
    const summaryDataSingleCurrency = {
      ...mockSummaryData,
      current_month_revenue_by_currency: { NTD: 25000 },
    };
    (apiClient.getSummary as jest.Mock).mockResolvedValue(summaryDataSingleCurrency);

    render(<DashboardStats />);

    await waitFor(() => {
      expect(screen.getByText('NTD 25,000')).toBeInTheDocument();
    });
  });

  it('should round hours correctly', async () => {
    const summaryDataWithDecimals = {
      ...mockSummaryData,
      total_minutes: 3665, // 61.08 hours -> should round to 61
      current_month_minutes: 1835, // 30.58 hours -> should round to 31
    };
    (apiClient.getSummary as jest.Mock).mockResolvedValue(summaryDataWithDecimals);

    render(<DashboardStats />);

    await waitFor(() => {
      expect(screen.getByText('61')).toBeInTheDocument();
      expect(screen.getByText('31')).toBeInTheDocument();
    });
  });

  it('should handle loading state correctly', async () => {
    // Mock a delayed response
    (apiClient.getSummary as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve(mockSummaryData), 100))
    );

    render(<DashboardStats />);

    // Should show loading initially
    expect(screen.getAllByText('...')).toHaveLength(4);

    // After data loads, should show actual numbers
    await waitFor(() => {
      expect(screen.getByText('60')).toBeInTheDocument();
    });
  });
});